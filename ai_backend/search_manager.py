import os
import json
from typing import List, Dict, Any, Optional
# Preporučuje se korišćenje novog paketa, ali ostaviću i stari u komentaru ako imate problema sa instalacijom
from langchain_huggingface import HuggingFaceEmbeddings
# from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

def pretrazi_po_recenici(
    upit: str,
    db_path: str,
    embeddings: HuggingFaceEmbeddings,
    predmet: Optional[str] = None,
    lekcija: Optional[str] = None,
    broj_rezultata: int = 4
) -> List[Dict[str, Any]]:
    """
    Vrši VEKTORSKU pretragu sličnosti i opciono filtrira rezultate po metapodacima.

    Args:
        upit (str): Tekstualni upit za pretragu.
        db_path (str): Putanja do direktorijuma FAISS baze.
        embeddings (HuggingFaceEmbeddings): Učitani embedding model.
        predmet (Optional[str]): Opciono, ime predmeta za filtriranje.
        lekcija (Optional[str]): Opciono, ime lekcije (fajla) za filtriranje.
        broj_rezultata (int): Maksimalan broj rezultata za povratak.

    Returns:
        List[Dict[str, Any]]: Lista parsiranih, originalnih JSON objekata koji su najsličniji upitu.
    """
    if not os.path.exists(db_path):
        print(f"GREŠKA: Vektorska baza na putanji '{db_path}' ne postoji.")
        return []

    try:
        print("INFO: Učitavam vektorsku bazu za pretragu po rečenici...")
        db = FAISS.load_local(db_path, embeddings, allow_dangerous_deserialization=True)
        
        # FAISS ne podržava pre-filtriranje, zato dohvatamo više rezultata pa ih filtriramo programski.
        pocetni_broj = broj_rezultata * 5 if predmet or lekcija else broj_rezultata
        
        print(f"INFO: Vršim pretragu za upit: '{upit}'...")
        rezultati_pretrage = db.similarity_search(upit, k=pocetni_broj)
        
        finalni_rezultati = []
    
        for doc in rezultati_pretrage:
            if len(finalni_rezultati) >= broj_rezultata:
                break
                
            metadata = doc.metadata
            # Provera da li dokument zadovoljava filter
            if predmet and metadata.get('predmet') != predmet:
                continue
            if lekcija and metadata.get('lekcija') != lekcija:
                continue

            # Ako je prošao filter, formatiramo ga za izlaz
            finalni_rezultati.append({
                "page_content": doc.page_content,
                "metadata": metadata
            })
        
        print(f"INFO: Vektorska pretraga završena. Pronađeno {len(finalni_rezultati)} rezultata.")
        return finalni_rezultati

    except Exception as e:
        print(f"GREŠKA: Došlo je do problema prilikom vektorske pretrage: {e}")
        return []

def pretrazi_po_kljucnim_recima(
    kljucne_reci: List[str],
    db_path: str,
    embeddings: HuggingFaceEmbeddings,
    predmet: Optional[str] = None,
    lekcija: Optional[str] = None,
    broj_rezultata: int = 10
) -> List[Dict[str, Any]]:
    """
    Vrši pretragu po KLJUČNIM REČIMA unutar metapodataka, bez vektorske pretrage.

    Args:
        kljucne_reci (List[str]): Lista ključnih reči koje se traže (case-insensitive).
        db_path (str): Putanja do direktorijuma FAISS baze.
        embeddings (HuggingFaceEmbeddings): Potrebno za učitavanje baze.
        predmet (Optional[str]): Opciono, ime predmeta za filtriranje.
        lekcija (Optional[str]): Opciono, ime lekcije (fajla) za filtriranje.
        broj_rezultata (int): Maksimalan broj rezultata za povratak.

    Returns:
        List[Dict[str, Any]]: Lista parsiranih, originalnih JSON objekata koji zadovoljavaju kriterijume.
    """
    if not os.path.exists(db_path):
        print(f"GREŠKA: Vektorska baza na putanji '{db_path}' ne postoji.")
        return []

    try:
        print("INFO: Učitavam vektorsku bazu za pretragu po ključnim rečima...")
        db = FAISS.load_local(db_path, embeddings, allow_dangerous_deserialization=True)
        
        # Pristupamo svim sačuvanim dokumentima
        docstore = db.docstore._dict
        trazene_reci_lower = {rec.lower() for rec in kljucne_reci}
        finalni_rezultati = []

        for doc_id, doc in docstore.items():
            if len(finalni_rezultati) >= broj_rezultata:
                break

            metadata = doc.metadata
            # Filtriranje po predmetu i lekciji
            if predmet and metadata.get('predmet') != predmet:
                continue
            if lekcija and metadata.get('lekcija') != lekcija:
                continue
            
            # Filtriranje po ključnim rečima
            postojece_reci = {rec.lower() for rec in metadata.get('keywords', [])}
            if trazene_reci_lower.intersection(postojece_reci):
                finalni_rezultati.append({
                    "page_content": doc.page_content,
                    "metadata": metadata
                })
        
        print(f"INFO: Pretraga po ključnim rečima završena. Pronađeno {len(finalni_rezultati)} rezultata.")
        return finalni_rezultati
        
    except Exception as e:
        print(f"GREŠKA: Došlo je do problema prilikom pretrage po ključnim rečima: {e}")
        return []