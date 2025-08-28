# app.py

import os
from dotenv import load_dotenv

from langchain_community.embeddings import HuggingFaceEmbeddings

from populate_vector_database.is_pdf_or_pp import main_chack_pdf
from populate_vector_database.util_functions import load_pdf_fiels, ocisti_direktorijum
from populate_vector_database.processing import ekstraktuj_i_podeli_tekst
from populate_vector_database.ai import get_ai_chunks

from vector_db_manager import kreiraj_ili_azuriraj_vektorsku_bazu

def main():
    """
    Glavna funkcija aplikacije.
    Prvi korak: Učitavanje i provera konfiguracije iz .env fajla.
    """
    load_dotenv()

    print("--- Pokrenuta aplikacija, učitavam konfiguraciju... ---")

    data_path = os.getenv("DATA_PATH", "podaci")
    db_faiss_path = os.getenv("DB_FAISS_PATH", "faiss_index")
    embedding_model = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
    embedding_device = os.getenv("EMBEDDING_DEVICE", "cpu")
    
    img_output_dir = os.getenv("IMG_OUTPUT_DIR", "izvucene_slike")

    try:
        # Parametri za obradu slika (brojevi)
        min_dimenzija = int(os.getenv("MIN_DIMENZIJA", 20))
        min_velicina_kb = float(os.getenv("MIN_VELICINA_KB", 2.0))
        prag_tamne = int(os.getenv("PRAG_TAMNE", 60))
        prag_svetle = int(os.getenv("PRAG_SVETLE", 195))
        minimalni_procenat = float(os.getenv("MINIMALNI_PROCENAT", 1.0))
        
        # Parametri za AI pozive
        time_to_wait = int(os.getenv("TIME_TO_WAIT", 5))
        
    except ValueError:
        print("GREŠKA: Neka od numeričkih vrednosti u .env fajlu nije validna. Postavljam na default vrednosti.")
        min_dimenzija = 20
        min_velicina_kb = 2.0
        prag_tamne = 60
        prag_svetle = 195
        minimalni_procenat = 1.0
        time_to_wait = 5
    try:
        print(f"INFO: Učitavam embedding model '{embedding_model}' na uređaj '{embedding_device}'...")
        embeddings = HuggingFaceEmbeddings(
            model_name=embedding_model,
            model_kwargs={'device': embedding_device}
        )
        print("INFO: Embedding model je uspešno učitan.")
    except Exception as e:
        print(f"KRITIČNA GREŠKA: Nije moguće učitati embedding model: {e}")
        return
    # Za brojeve je važno da ih pretvorimo u 'int' tip, jer os.getenv() uvek vraća string.
    try:
        chunk_size = int(os.getenv("CHUNK_SIZE", 1000))
        chunk_overlap = int(os.getenv("CHUNK_OVERLAP", 150))
    except ValueError:
        print("GREŠKA: CHUNK_SIZE ili CHUNK_OVERLAP u .env fajlu nisu validni brojevi.")
        # U slučaju greške, postavljamo na default vrednosti
        chunk_size = 1000
        chunk_overlap = 150


    for pdf_file in load_pdf_fiels(data_path):
        print(f"Pronađen PDF fajl: {pdf_file}")

        podeljeni_tekst = None

        # file_type = "pdf"
        # if(main_chack_pdf(pdf_file) == "PowerPoint"):
        #     file_type = "pp"
        

        podeljeni_tekst = get_ai_chunks(ekstraktuj_i_podeli_tekst(pdf_file, img_output_dir, chunk_size, chunk_overlap, min_dimenzija, min_velicina_kb, prag_tamne, prag_svetle, minimalni_procenat), time_to_wait, img_direktorijum=img_output_dir)

            
        ocisti_direktorijum()
            # Generisanje pravih znanja na osnovu vracenog teksta
            # AI generisnje
        print(f"Obrađujem PDF fajl: {podeljeni_tekst}...")
        # Proveravamo da li je rezultat uspešan i ispisujemo ga
        if podeljeni_tekst:

            putanja_do_foldera, naziv_lekcije = os.path.split(pdf_file)
            naziv_predmeta = os.path.basename(putanja_do_foldera) if putanja_do_foldera.strip() and os.path.basename(putanja_do_foldera) != os.path.basename(data_path.strip('/\\')) else ""

            metapodaci = [
                {
                    "keywords": i.get('metadata', []).get('keywords', []),
                    "source": pdf_file, 
                    "lekcija": naziv_lekcije,
                    "predmet": naziv_predmeta
                } 
                for i in podeljeni_tekst
            ]


            samo_embedding_tekstovi = []

            # 2. Prolazimo kroz svaki element (rečnik) u originalnoj listi
            for rečnik in podeljeni_tekst:
                # 3. Iz svakog rečnika, uzimamo vrednost ključa 'embedding_text'
                tekst = rečnik['embedding_text']
                
                # 4. Dodajemo tu vrednost u našu novu listu
                samo_embedding_tekstovi.append(tekst)

            # -------------------------------
            
            # --- POZIV NOVE FUNKCIJE IZ MODULA ---
            kreiraj_ili_azuriraj_vektorsku_bazu(
                chunks=samo_embedding_tekstovi,
                metadatas=metapodaci,
                db_path=db_faiss_path,
                embeddings=embeddings
            )
            # ---------------------------------
            print(f"Tekst je uspešno podeljen na {len(podeljeni_tekst)} delova (chunks).\n")
            # for i, chunk in enumerate(podeljeni_tekst):
            #     print(f"--- DEO {i+1} ---")
            #     print(chunk)
            #     print("\n" + "="*20 + "\n")
        else:
            print("Nije bilo moguće obraditi PDF fajl.")
        
        break
    # Ucitaj spisak putanja ka fajlovima koje cu obradjivati



if __name__ == "__main__":
    # Ova linija osigurava da se funkcija main() poziva samo 
    # kada se skripta pokrene direktno (a ne kada se importuje kao modul).
    main()