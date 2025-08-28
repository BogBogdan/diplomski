# test_search.py
import os
from dotenv import load_dotenv

# VAŽNO: Koristi ispravan import, onaj koji si popravio u glavnom projektu
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

print("--- Pokrećem test pretrage vektorske baze ---")

# Učitaj .env fajl da dobiješ putanje
load_dotenv()

# Uzmi putanje i ime modela iz .env
DB_FAISS_PATH = os.getenv("DB_FAISS_PATH")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL")

if not DB_FAISS_PATH or not os.path.exists(DB_FAISS_PATH):
    print(f"GREŠKA: Putanja do baze '{DB_FAISS_PATH}' ne postoji ili nije definisana u .env. Prekidam.")
    exit()

if not EMBEDDING_MODEL:
    print("GREŠKA: EMBEDDING_MODEL nije definisan u .env. Prekidam.")
    exit()

try:
    print(f"Učitavam embedding model: {EMBEDDING_MODEL}...")
    # Inicijalizuj embedding model, baš kao u glavnoj aplikaciji
    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL, model_kwargs={'device': 'cpu'})
    print("Embedding model učitan.")

    print(f"Učitavam vektorsku bazu sa putanje: {DB_FAISS_PATH}...")
    # Učitaj FAISS bazu
    db = FAISS.load_local(DB_FAISS_PATH, embeddings, allow_dangerous_deserialization=True)
    print("Vektorska baza učitana.")

    # Definiši jednostavan, generički upit
    test_upit = "distribuirani sistemi" # Koristimo vrlo opšti pojam
    print(f"\n--- Testiram vektorsku pretragu sa upitom: '{test_upit}' ---")

    # Pokreni najprostiju moguću pretragu
    rezultati = db.similarity_search(test_upit, k=5)

    print(f"\nPronađeno {len(rezultati)} rezultata.")

    # Ispiši sadržaj i metapodatke prvog rezultata, ako postoji
    if rezultati:
        print("\n--- Prvi rezultat ---")
        print("Sadržaj (page_content):")
        print(rezultati[0].page_content)
        print("\nMetapodaci (metadata):")
        print(rezultati[0].metadata)
    else:
        print("\nNije pronađen nijedan rezultat. Ovo ukazuje na problem sa sadržajem baze.")

except Exception as e:
    print(f"\nDošlo je do greške tokom testa: {e}")