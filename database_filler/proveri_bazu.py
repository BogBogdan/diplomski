import os
from dotenv import load_dotenv
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings

# Učitaj konfiguraciju iz .env fajla
load_dotenv()

# Iste varijable kao u skripti za kreiranje baze
DB_FAISS_PATH = os.getenv("DB_FAISS_PATH", "faiss_index")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
EMBEDDING_DEVICE = os.getenv("EMBEDDING_DEVICE", "cpu")

def main():
    """
    Glavna funkcija koja učitava vektorsku bazu i ispisuje njen sadržaj.
    """
    print(f"--- Provera sadržaja vektorske baze ---")
    print(f"Putanja do baze: {DB_FAISS_PATH}")

    # Proveri da li baza uopšte postoji
    if not os.path.exists(DB_FAISS_PATH):
        print(f"GREŠKA: Vektorska baza nije pronađena na putanji '{DB_FAISS_PATH}'.")
        print("Molimo vas da prvo pokrenete skriptu za kreiranje baze.")
        return

    # Inicijalizuj isti embedding model koji je korišćen za kreiranje baze
    # Ovo je neophodno za ispravno učitavanje
    print(f"Učitavanje embedding modela: {EMBEDDING_MODEL}...")
    embeddings = HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        model_kwargs={'device': EMBEDDING_DEVICE}
    )

    # Učitaj lokalnu FAISS bazu
    print("Učitavanje FAISS baze...")
    try:
        db = FAISS.load_local(
            DB_FAISS_PATH, 
            embeddings,
            # Ovaj fleg je često potreban za FAISS baze kreirane u LangChain-u
            allow_dangerous_deserialization=True 
        )
        print("Baza je uspešno učitana.")
    except Exception as e:
        print(f"Došlo je do greške prilikom učitavanja baze: {e}")
        return

    # Pristupi sačuvanim dokumentima kroz docstore
    # U FAISS-u unutar LangChain-a, dokumenti se čuvaju u `db.docstore._dict`
    if not hasattr(db, 'docstore') or not hasattr(db.docstore, '_dict'):
        print("Nije moguće pristupiti sadržaju baze (docstore nije pronađen).")
        return

    saved_documents = list(db.docstore._dict.values())
    
    if not saved_documents:
        print("Baza je prazna, nema sačuvanih dokumenata.")
        return

    print("\n" + "="*50)
    print(f"SADRŽAJ BAZE (ukupno {len(saved_documents)} delova):")
    print("="*50 + "\n")

    # Prođi kroz sve dokumente i ispiši ih
    for i, doc in enumerate(saved_documents):
        print(f"--- DOKUMENT (CHUNK) #{i + 1} ---")
        
        # Ispiši metapodatke
        print(f"Metapodaci: {doc.metadata}")
        
        # Ispiši sam tekst
        print("Sadržaj teksta:")
        print(f"\"{doc.page_content}\"")
        
        print("\n" + "="*50 + "\n")

    print(f"Prikazano je svih {len(saved_documents)} delova iz baze.")


if __name__ == "__main__":
    main()