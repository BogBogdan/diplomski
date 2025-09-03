# parallel_search.py

import os
import json
from typing import List, Dict, Any, Tuple
import asyncio  # <-- NOVI IMPORT

# Importujemo funkcije iz search_manager-a
from search_manager import pretrazi_po_recenici, pretrazi_po_kljucnim_recima
from langchain_huggingface import HuggingFaceEmbeddings

# Import za reranker
from sentence_transformers.cross_encoder import CrossEncoder

# Pomoćna funkcija za jedinstveni ključ (ostaje ista)
def _izvuci_jedinstveni_kljuc(d: Dict[str, Any]) -> str:
    predmet = d.get('partOf', {}).get('name', '').split(' ')[-1]
    lekcija = d.get('meta_lekcija', d.get('lekcija', ''))
    opis_isečak = d.get('description', '')[:50]
    return f"{predmet}::{lekcija}::{opis_isečak}"


# =================================================================
# === IZMENA #1: Funkcija sada postaje `async def` ===
# =================================================================
async def izvrsi_paralelnu_pretragu(
    originalno_pitanje: str,
    slicna_pitanja: List[str],
    provera_odgovor: str,
    provera_kljucne_reci: List[str],
    db_path: str,
    embeddings: HuggingFaceEmbeddings,
    predmet: str = None,
    lekcija: str = None,
    broj_rezultata: int = 10,
    top_n: int = 5
) -> List[Dict[str, Any]]:
    """
    Pokreće tri odvojene pretrage asinhrono, spaja jedinstvene rezultate,
    koristi LOKALNI Cross-Encoder model da ih preuredi i vraća top N rezultata.
    """
    lista_zadataka = []
    
    # 1. Kreiraj listu svih upita za vektorsku pretragu
    svi_upiti_za_pretragu = [originalno_pitanje] + slicna_pitanja + [provera_odgovor]
    
    # =================================================================
    # === IZMENA #2: Koristimo asyncio.to_thread umesto ThreadPoolExecutor ===
    # =================================================================

    # 2. Dinamički dodaj zadatke za SVAKI upit za vektorsku pretragu
    for upit in svi_upiti_za_pretragu:
        if upit and upit.strip():
            # asyncio.to_thread pokreće blokirajuću funkciju u posebnom thread-u
            # i vraća "awaitable" objekat (korutinu).
            task = await asyncio.to_thread(
                pretrazi_po_recenici, 
                upit=upit, 
                db_path=db_path, 
                embeddings=embeddings,
                predmet=predmet,
                lekcija=lekcija,
                broj_rezultata=broj_rezultata
            )
            lista_zadataka.append(task)
            print(f"INFOOO: Dodan zadatak pretrage za upit: '{str(task)}'")
        
    # 3. Dodaj zadatak za pretragu po ključnim rečima
    if provera_kljucne_reci:
        task = asyncio.to_thread(
            pretrazi_po_kljucnim_recima,
            kljucne_reci=provera_kljucne_reci,
            db_path=db_path,
            embeddings=embeddings,
            predmet=predmet,
            lekcija=lekcija,
            broj_rezultata=broj_rezultata
        )
        lista_zadataka.append(task)
            
    # =================================================================
    # === IZMENA #3: Sakupljamo rezultate koristeći `await asyncio.gather` ===
    # =================================================================
    if not lista_zadataka:
        return []

    print(f"INFO: Pokrećem {len(lista_zadataka)} zadataka pretrage paralelno...")
    # asyncio.gather pokreće sve zadatke konkurentno i čeka da se završe.
    # `return_exceptions=True` sprečava da jedna greška obori sve ostale zadatke.
    rezultati_iz_zadataka = await asyncio.gather(*lista_zadataka, return_exceptions=True)
    
    sve_liste_rezultata = []
    for rezultat in rezultati_iz_zadataka:
        if isinstance(rezultat, Exception):
            print(f"GREŠKA: Jedan od zadataka pretrage je pukao: {rezultat}")
        else:
            sve_liste_rezultata.append(rezultat)
                
    # --- Spajanje i uklanjanje duplikata (logika ostaje ista) ---
    jedinstveni_dokumenti_dict = {}
    for lista in sve_liste_rezultata:
        for doc in lista:
            kljuc = _izvuci_jedinstveni_kljuc(doc)
            if kljuc not in jedinstveni_dokumenti_dict:
                jedinstveni_dokumenti_dict[kljuc] = doc
    
    kandidati_za_rerank = list(jedinstveni_dokumenti_dict.values())
    
    if not kandidati_za_rerank:
        print("INFO: Nema pronađenih kandidata za rerankiranje.")
        return []

    print(f"INFO: Ukupno {len(kandidati_za_rerank)} jedinstvenih dokumenata pronađeno za rerankiranje.")
    
    print("INFO: Pokrećem lokalni reranker (Cross-Encoder)...")
    try:
        cross_encoder = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
        
        parovi_za_ocenjivanje = [
            (originalno_pitanje, doc.get('description', '')) 
            for doc in kandidati_za_rerank
        ]
        
        # =================================================================
        # === IZMENA #4: I reranker (CPU-bound) mora da se pokrene u thread-u ===
        # =================================================================
        skorovi = await asyncio.to_thread(cross_encoder.predict, parovi_za_ocenjivanje)
        
        rezultati_sa_skorovima = list(zip(skorovi, kandidati_za_rerank))
        rezultati_sa_skorovima.sort(key=lambda x: x[0], reverse=True)
        
        finalni_rezultati = [doc for skor, doc in rezultati_sa_skorovima]
        
        print(f"INFO: Rerankiranje završeno. Vraćam top {top_n} rezultata.")
        return finalni_rezultati[:top_n]

    except Exception as e:
        print(f"GREŠKA: Došlo je do problema prilikom lokalnog rerankiranja: {e}")
        return kandidati_za_rerank[:top_n]