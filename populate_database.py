# 1_create_or_update_database.py

import os
from dotenv import load_dotenv
from langchain_community.document_loaders import DirectoryLoader, UnstructuredFileLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.docstore.document import Document
import warnings
import re 

def clean_text(text: str) -> str:
    """Pomoćna funkcija za čišćenje teksta od poznatih artefakata."""
    # Ukloni brojeve slajdova kao što su 5/70, 12/80 itd.
    text = re.sub(r'\b\d+/\d+\b', '', text)
    # Ukloni cid greške iz PDF-a
    text = re.sub(r'\(cid:\d+\)', '', text)
    # Ukloni višestruke prelome reda i zameni ih jednim
    text = re.sub(r'\n\s*\n', '\n', text)
    return text.strip()

def process_documents(documents: list[Document]) -> list[Document]:
    """
    Pomoćna funkcija koja obrađuje listu dokumenata:
    1. Čisti tekstualni sadržaj.
    2. Dodaje metapodatke (predmet, lekcija)
    3. Deli dokumente na manje delove (chunkove)
    """
    # === KORAK 1: ČIŠĆENJE TEKSTA ===
    for doc in documents:
        doc.page_content = clean_text(doc.page_content)
    
    # === KORAK 2: DODAVANJE METAPODATAKA ===
    for doc in documents:
        # ... (ostatak koda za metapodatke ostaje isti) ...
        source_path = doc.metadata.get('source', '')
        filename = os.path.basename(source_path)
        # ... itd.

    # === KORAK 3: DELJENJE TEKSTA NA DELOVE ===
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP
    )
    texts = text_splitter.split_documents(documents)
    return texts

# --- OPCIONO: Sakrijte specifična "color" upozorenja iz unstructured biblioteke ---
warnings.filterwarnings(
    "ignore",
    category=UserWarning,
    message="Cannot set non-stroke color" # Dovoljan je deo poruke
)

load_dotenv()

DATA_PATH = os.getenv("DATA_PATH", "../data/")
DB_FAISS_PATH = os.getenv("DB_FAISS_PATH", "faiss_index")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
EMBEDDING_DEVICE = os.getenv("EMBEDDING_DEVICE", "cpu")
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", 1000))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", 150))

print(f"--- Konfiguracija za kreiranje baze učitana ---")
print(f"Izvorni folder sa podacima: {DATA_PATH}")
print(f"Putanja za vektorsku bazu: {DB_FAISS_PATH}")
print(f"Embedding model: {EMBEDDING_MODEL} na uređaju: {EMBEDDING_DEVICE}")
print(f"Veličina delova (chunk size): {CHUNK_SIZE}, Preklapanje (overlap): {CHUNK_OVERLAP}")
print("-" * 50)

def process_documents(documents: list[Document]) -> list[Document]:
    """
    Pomoćna funkcija koja obrađuje listu dokumenata:
    1. Dodaje metapodatke (predmet, lekcija)
    2. Deli dokumente na manje delove (chunkove)
    """
    # --- Korak 1: Dodavanje metapodataka ---
    for doc in documents:
        source_path = doc.metadata.get('source', '')
        
        # Izdvajanje imena LEKCIJE
        filename = os.path.basename(source_path)
        lekcija_ime, _ = os.path.splitext(filename)
        doc.metadata['lekcija'] = lekcija_ime

        # Izdvajanje imena PREDMETA
        relative_path = os.path.relpath(source_path, DATA_PATH)
        path_parts = relative_path.split(os.sep)
        
        doc.metadata['predmet'] = path_parts[0] if len(path_parts) > 1 else 'opšte'

    # --- Korak 2: Deljenje teksta na delove ---
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE, 
        chunk_overlap=CHUNK_OVERLAP
    )
    texts = text_splitter.split_documents(documents)
    return texts


def main():
    """
    Glavna funkcija koja proverava da li baza postoji i odlučuje
    da li da je kreira od nule ili da je samo ažurira.
    """
    
    # Inicijalizacija embedding modela, trebaće nam u oba slučaja
    embeddings = HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        model_kwargs={'device': EMBEDDING_DEVICE}
    )

    loader_kwargs = {'languages': ['srp', 'eng']} # Dodajemo srpski i engleski


    if os.path.exists(DB_FAISS_PATH):
        # --- PUTANJA ZA AŽURIRANJE POSTOJEĆE BAZE ---
        print(f"Postojeća baza pronađena u '{DB_FAISS_PATH}'. Pokrećem ažuriranje...")
        
        # Učitaj postojeću bazu
        db = FAISS.load_local(DB_FAISS_PATH, embeddings, allow_dangerous_deserialization=True)

        # Napravi set postojećih izvora za brzu pretragu
        existing_sources = set(doc.metadata['source'] for doc in db.docstore._dict.values())
        print(f"U bazi se trenutno nalazi {len(existing_sources)} jedinstvenih dokumenata.")

        # Učitaj SVE trenutne dokumente sa diska
        print("Skeniranje 'data' foldera za novim ili izmenjenim dokumentima...")
        glob_patterns = ["**/*.pdf", "**/*.docx", "**/*.txt", "**/*.pptx", "**/*.html"]
        all_documents = []
        for pattern in glob_patterns:
            loader = DirectoryLoader(
                DATA_PATH, glob=pattern, loader_cls=UnstructuredFileLoader,
                loader_kwargs=loader_kwargs, 
                show_progress=True, use_multithreading=True
            )
            all_documents.extend(loader.load())

        # Filtriraj samo NOVE dokumente
        new_documents = [doc for doc in all_documents if doc.metadata['source'] not in existing_sources]

        if not new_documents:
            print("Nema novih dokumenata za dodavanje. Baza je ažurna.")
            return

        print(f"Pronađeno {len(new_documents)} novih dokumenata za obradu.")
        
        # Obradi samo nove dokumente
        new_texts = process_documents(new_documents)
        print(f"Novi dokumenti podeljeni na {len(new_texts)} delova.")
        
        # Dodaj nove delove u postojeću bazu
        print("Dodavanje novih delova u FAISS bazu...")
        db.add_documents(new_texts)
        
        # Sačuvaj ažuriranu bazu
        print("Čuvanje ažurirane baze...")
        db.save_local(DB_FAISS_PATH)
        print("Baza je uspešno ažurirana!")

    else:
        # --- PUTANJA ZA KREIRANJE NOVE BAZE OD NULE ---
        print(f"Baza nije pronađena. Kreiranje nove baze u '{DB_FAISS_PATH}'...")
        
        # Učitaj sve dokumente sa diska
        print(f"Učitavanje dokumenata iz '{DATA_PATH}' foldera...")
        glob_patterns = ["**/*.pdf", "**/*.docx", "**/*.txt", "**/*.pptx", "**/*.html"]
        documents = []
        for pattern in glob_patterns:
            loader = DirectoryLoader(
                DATA_PATH, glob=pattern, loader_cls=UnstructuredFileLoader,
                loader_kwargs=loader_kwargs, 
                show_progress=True, use_multithreading=True
            )
            documents.extend(loader.load())

        if not documents:
            print("Nije pronađen nijedan dokument za obradu.")
            return

        print(f"Učitano {len(documents)} dokumenata.")
        
        # Obradi sve dokumente
        texts = process_documents(documents)
        print(f"Tekst je podeljen na {len(texts)} delova.")

        texts = process_documents(documents)
        print(f"Tekst je podeljen na {len(texts)} delova.")


        # Kreiraj FAISS bazu od tekstova
        print("Kreiranje FAISS baze od dokumenata...")
        db = FAISS.from_documents(texts, embeddings)

        # Sačuvaj bazu na disk
        print(f"Čuvanje vektorske baze u folder: {DB_FAISS_PATH}...")
        db.save_local(DB_FAISS_PATH)
        print("Baza je uspešno kreirana!")


if __name__ == "__main__":
    main()