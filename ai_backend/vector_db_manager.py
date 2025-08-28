# populate_vector_database/vector_db_manager.py

import os
from typing import List, Dict, Any
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings

def kreiraj_ili_azuriraj_vektorsku_bazu(
    chunks: List[str],
    metadatas: List[Dict[str, Any]],
    db_path: str,
    embeddings: HuggingFaceEmbeddings
):
    if len(chunks) != len(metadatas):
        print("GREŠKA: Broj chunkova i broj metapodataka se ne poklapaju. Prekidam upis u bazu.")
        return

    try:
        if os.path.exists(db_path):
            # Baza već postoji, učitaj je i dodaj nove dokumente
            print(f"INFO: Postojeća vektorska baza pronađena na '{db_path}'. Učitavam i ažuriram...")
            # 'allow_dangerous_deserialization' je neophodno za učitavanje sa HuggingFaceEmbeddings
            local_index = FAISS.load_local(
                db_path, 
                embeddings,
                allow_dangerous_deserialization=True
            )
            local_index.add_texts(texts=chunks, metadatas=metadatas)
            local_index.save_local(db_path)
            print("INFO: Vektorska baza je uspešno ažurirana.")
        else:
            # Baza ne postoji, kreiraj novu od nule
            print(f"INFO: Ne postoji vektorska baza. Kreiram novu na putanji '{db_path}'...")
            new_index = FAISS.from_texts(texts=chunks, metadatas=metadatas, embedding=embeddings)
            new_index.save_local(folder_path=db_path)
            print("INFO: Nova vektorska baza je uspešno kreirana i sačuvana.")
            
    except Exception as e:
        print(f"GREŠKA: Došlo je do problema prilikom rada sa vektorskom bazom: {e}")