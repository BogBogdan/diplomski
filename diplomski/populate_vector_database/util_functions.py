import os
import shutil
import unicodedata
import re


def ocisti_tekst(text: str) -> str:
    """
    Vrši agresivno čišćenje teksta ekstraktovanog iz PDF-a.
    """
    # 1. Unikod normalizacija (dobra praksa)
    text = unicodedata.normalize('NFKC', text)

    # 2. Ručna zamena najčešćih problematičnih karaktera
    # Možete proširiti ovaj rečnik po potrebi. Ključ je loš karakter, vrednost je zamena.
    zamene = {
        '': '!=',   # Različito od
        '': '<=',   # Manje ili jednako
        '': '>=',   # Veće ili jednako
        '': ' AND ',# Logičko I
        '': ' OR ', # Logičko ILI
        '': ' NOT ',# Logičko NE
        '': ' pripada ', # Pripada (matematika)
        '': ' ne pripada ', # Ne pripada
        # Dodajte još zamena ovde ako ih primetite...
    }
    for los_karakter, dobra_zamena in zamene.items():
        text = text.replace(los_karakter, dobra_zamena)

    # 3. Uklanjanje svih karaktera koji nisu slova, brojevi, standardna interpunkcija ili razmaci.
    # Ovo je agresivan korak koji čisti sve preostale "kvadratiće".
    # Dozvoljavamo slova (latinicu i našu), brojeve, i osnovne znakove interpunkcije.
    text = re.sub(r'[^\w\s.,!?;:"\'()\[\]{}<>=+/\\-]', '', text, flags=re.UNICODE)
    
    # 4. Zamena višestrukih razmaka jednim (opciono, ali preporučeno)
    text = re.sub(r'\s+', ' ', text).strip()

    return text

def ocisti_direktorijum(ime_direktorijuma: str = "izvucene_slike"):
    """
    Briše navedeni direktorijum i sav njegov sadržaj.

    Args:
        ime_direktorijuma (str, optional): Ime direktorijuma koji treba obrisati.
                                            Podrazumevana vrednost je "izvucene_slike".
    """
    print(f"\n--- Pokrećem čišćenje direktorijuma: '{ime_direktorijuma}' ---")
    
    try:
        # Proveravamo da li direktorijum uopšte postoji
        if os.path.exists(ime_direktorijuma):
            # shutil.rmtree briše direktorijum i SVE što se u njemu nalazi
            shutil.rmtree(ime_direktorijuma)
            print(f"✅ Uspešno obrisan direktorijum: '{ime_direktorijuma}'")
        else:
            # Ako direktorijum ne postoji, samo ispisujemo poruku
            print(f"ℹ️ Direktorijum '{ime_direktorijuma}' ne postoji, nema šta da se briše.")
            
    except PermissionError:
        print(f"❌ Greška: Nemate dozvolu za brisanje. Proverite da li je neki fajl iz '{ime_direktorijuma}' otvoren u drugom programu.")
    except Exception as e:
        print(f"❌ Došlo je do neočekivane greške tokom čišćenja: {e}")
        
    print("--- Čišćenje završeno ---")

def load_pdf_fiels(data_path: str) -> list[str]:
    """
    Rekurzivno učitava SVE PDF fajlove iz datog direktorijuma i svih
    njegovih poddirektorijuma. Vraća listu punih putanja do fajlova.
    """
    # Provera da li ulazni direktorijum uopšte postoji
    if not os.path.isdir(data_path):
        print(f"GREŠKA: Direktorijum '{data_path}' ne postoji ili nije direktorijum.")
        return []

    pdf_files_paths = []
    
    # os.walk() prolazi kroz ceo "drvo" direktorijuma
    # Za svaki folder, vraća njegovu putanju (root), listu podfoldera (dirs) i listu fajlova (files)
    for root, dirs, files in os.walk(data_path):
        for file in files:
            # Proveravamo da li se fajl završava sa .pdf (case-insensitive)
            if file.lower().endswith('.pdf'):
                full_path = os.path.join(root, file)
                normalized_path = os.path.normpath(full_path)
                pdf_files_paths.append(normalized_path)

    return pdf_files_paths
