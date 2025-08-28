# parallel_search.py

import os
import json
from typing import List, Dict, Any, Tuple
import concurrent.futures

# Importujemo funkcije iz search_manager-a
from search_manager import pretrazi_po_recenici, pretrazi_po_kljucnim_recima
from langchain_huggingface import HuggingFaceEmbeddings

# --- NOVI IMPORT ZA LOKALNI RERANKER ---
from sentence_transformers.cross_encoder import CrossEncoder

# Pomoćna funkcija za jedinstveni ključ (ostaje ista)
def _izvuci_jedinstveni_kljuc(d: Dict[str, Any]) -> str:
    predmet = d.get('partOf', {}).get('name', '').split(' ')[-1]
    lekcija = d.get('meta_lekcija', d.get('lekcija', ''))
    opis_isečak = d.get('description', '')[:50]
    return f"{predmet}::{lekcija}::{opis_isečak}"


def izvrsi_paralelnu_pretragu(
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
    Pokreće tri odvojene pretrage paralelno, spaja jedinstvene rezultate,
    koristi LOKALNI Cross-Encoder model da ih preuredi i vraća top N rezultata.
    """
    lista_zadataka = []
    
    # 1. Kreiraj listu svih upita za vektorsku pretragu
    svi_upiti_za_pretragu = [originalno_pitanje] + slicna_pitanja + [provera_odgovor]
    
    # 2. Inicijalizuj ThreadPoolExecutor
    with concurrent.futures.ThreadPoolExecutor() as executor:
        
        # 3. Dinamički dodaj zadatke za SVAKI upit za vektorsku pretragu <--- IZMENA #2
        for upit in svi_upiti_za_pretragu:
            if upit and upit.strip():
                future = executor.submit(
                    pretrazi_po_recenici, 
                    upit=upit, 
                    db_path=db_path, 
                    embeddings=embeddings,
                    predmet=predmet,
                    lekcija=lekcija,
                    broj_rezultata=broj_rezultata
                )
                lista_zadataka.append(future)

        # 4. Dodaj zadatak za pretragu po ključnim rečima
        if provera_kljucne_reci:
            future = executor.submit(
                pretrazi_po_kljucnim_recima,
                kljucne_reci=provera_kljucne_reci,
                db_path=db_path,
                embeddings=embeddings,
                predmet=predmet,
                lekcija=lekcija,
                broj_rezultata=broj_rezultata
            )
            lista_zadataka.append(future)
            
        # --- Sakupljanje rezultata (ostatak koda je isti) ---
        sve_liste_rezultata = []
        for future in concurrent.futures.as_completed(lista_zadataka):
            try:
                sve_liste_rezultata.append(future.result())
            except Exception as e:
                print(f"GREŠKA: Jedna od niti za pretragu je pukla: {e}")
                
    # --- Spajanje i uklanjanje duplikata (ostaje isto) ---
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
    
    # --- Rerankiranje sa LOKALNIM Cross-Encoderom ---
    print("INFO: Pokrećem lokalni reranker (Cross-Encoder)...")
    try:
        # 1. Inicijalizacija modela. Automatski će se preuzeti i keširati pri prvom pokretanju.
        # NEMA API KLJUČA!
        cross_encoder = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
        
        # 2. Priprema parova za ocenjivanje: (upit, tekst_dokumenta)
        # Koristićemo 'description' kao tekst dokumenta za poređenje.
        parovi_za_ocenjivanje = [
            (originalno_pitanje, doc.get('description', '')) 
            for doc in kandidati_za_rerank
        ]
        
        # 3. Dobijanje ocena relevantnosti od modela. Ovo je BRZO.
        skorovi = cross_encoder.predict(parovi_za_ocenjivanje)
        
        # 4. Spajanje dokumenata sa njihovim skorovima i sortiranje
        rezultati_sa_skorovima = list(zip(skorovi, kandidati_za_rerank))
        
        # Sortiramo listu u opadajućem redosledu na osnovu skora (prvi element torke)
        rezultati_sa_skorovima.sort(key=lambda x: x[0], reverse=True)
        
        # 5. Izdvajamo samo sortirane dokumente i vraćamo top N
        finalni_rezultati = [doc for skor, doc in rezultati_sa_skorovima]
        
        print(f"INFO: Rerankiranje završeno. Vraćam top {top_n} rezultata.")
        return finalni_rezultati[:top_n]

    except Exception as e:
        print(f"GREŠKA: Došlo je do problema prilikom lokalnog rerankiranja: {e}")
        return kandidati_za_rerank[:top_n] # U slučaju greške, vraćamo nesortirane