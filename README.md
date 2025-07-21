# Konfigurabilni RAG API za Pitanja i Odgovore

Ovaj projekat predstavlja kompletan RAG (Retrieval-Augmented Generation) sistem izgrađen u Python-u, koji služi kao pametni asistent sposoban da odgovara na pitanja na osnovu priloženih dokumenata. Sistem takođe poseduje i naprednu funkcionalnost za evaluaciju tačnosti datih odgovora.

Aplikacija je izložena putem FastAPI servera, čineći je lako dostupnom za integraciju sa drugim sistemima ili korisničkim interfejsima.

## Ključne Funkcionalnosti

-   **Generisanje Odgovora (RAG):** Korisnik postavlja pitanje, sistem pronalazi relevantne delove teksta iz svoje baze znanja (dokumenata) i koristi Veliki Jezički Model (LLM) da generiše precizan i kontekstualno tačan odgovor.
-   **Evaluacija Odgovora:** Sistem može da primi pitanje i već postojeći odgovor, pronađe relevantan kontekst, i iskoristi LLM da oceni tačnost i potpunost datog odgovora.
-   **Obrada Različitih Dokumenata:** Automatski učitava i obrađuje dokumente u različitim formatima (`.pdf`, `.docx`, `.txt`, `.pptx`, `.html`).
-   **Konfigurabilni AI Provider:** Lako se prebacuje između različitih AI provajdera (lokalni **Ollama**, **OpenAI**, **Google Gemini**) izmenom jedne linije u `.env` fajlu.
-   **Optimizovana Pretraga:** Koristi **FAISS** vektorsku bazu za ultra-brzu pretragu relevantnih informacija.

## Tehnologije i Komponente

-   **Backend:** FastAPI, Uvicorn
-   **AI/ML Framework:** LangChain
-   **Vektorska Baza:** FAISS (Facebook AI Similarity Search)
-   **Embedding Model:** `sentence-transformers/all-MiniLM-L6-v2` (sa Hugging Face)
-   **LLM (Jezički Modeli):** Podržava bilo koji model kroz Ollama (npr. `llama3`), OpenAI (npr. `gpt-4`) ili Google Gemini.
-   **Obrada Dokumenata:** `unstructured`, `pdf2image`, `python-pptx`, itd.

## Struktura Projekta

---

## Podešavanje i Instalacija

### Korak 0: Preduslovi

1.  **Python 3.9+**: Proverite da li imate instaliran Python.
2.  **Git**: Za kloniranje repozitorijuma.
3.  **(Za Windows)** **Poppler**: Neophodan za obradu PDF fajlova.
    -   Preuzmite najnoviju verziju sa [ove stranice](https://github.com/oschwartz10612/poppler-for-windows/releases/).
    -   Raspakujte arhivu npr. u `C:\poppler`.
    -   Dodajte putanju do `bin` foldera (npr. `C:\poppler\poppler-24.02.0\bin`) u vaš sistemski `PATH`.
4.  **(Opciono, preporučeno)** **Ollama**: Ako želite da koristite lokalni LLM. Preuzmite sa [ollama.com](https://ollama.com) i nakon instalacije, povucite željeni model komandom:
    ```bash
    ollama pull llama3
    ```

### Korak 1: Kloniranje Repozitorijuma

```bash
git clone https://github.com/BogBogdan/diplomski.git
cd diplomski
```
### Korak 2: Kreiranje Virtuelnog Okruženja

Preporučuje se korišćenje virtuelnog okruženja za izolaciju projektnih zavisnosti.

```bash
# Kreiranje okruženja
python -m venv venv

# Aktivacija okruženja
# Na Windows-u:
venv\Scripts\activate
# Na Mac/Linux-u:
source venv/bin/activate
```
### Korak 3: Instalacija Zavisnosti

Svi potrebni paketi su navedeni u `requirements.txt`.

```bash
pip install -r requirements.txt
```
(Napomena: Ako requirements.txt ne postoji, možete ga kreirati sa potrebnim paketima: fastapi uvicorn python-dotenv langchain langchain-community sentence-transformers faiss-cpu "unstructured[all]" pdf2image python-pptx requests)

Korak 4: Konfiguracija (.env fajl)
Kreirajte fajl pod nazivom .env u korenu projekta i dodajte sledeći sadržaj. Podesite vrednosti prema vašim potrebama.
```bash
# === KONFIGURACIJA VEKTORSKE BAZE ===
# Putanja do foldera sa vašim dokumentima
DATA_PATH="../data/"
# Putanja gde će biti sačuvana vektorska baza
DB_FAISS_PATH="faiss_index"

# === KONFIGURACIJA MODELA ===
# Embedding model za pretvaranje teksta u vektore
EMBEDDING_MODEL="sentence-transformers/all-MiniLM-L6-v2"
# Uređaj na kojem će se izvršavati embedding (cpu ili cuda)
EMBEDDING_DEVICE="cpu"

# Veličina delova teksta (chunkova) i preklapanje
CHUNK_SIZE=1000
CHUNK_OVERLAP=150

# === KONFIGURACIJA AI PROVIDERA ===
# Izaberite jednog od: "ollama", "openai", "gemini"
AI_PROVIDER="ollama"
# Naziv modela koji će se koristiti.
# Za ollama: "llama3", "mistral", itd.
# Za openai: "gpt-4", "gpt-3.5-turbo"
# Za gemini: "gemini-pro"
AI_MODEL_NAME="llama3"

# === API KLJUČEVI (popuniti samo ako ne koristite Ollama) ===
OPENAI_API_KEY="vas_openai_kljuc_ovde"
GOOGLE_API_KEY="vas_google_api_kljuc_ovde"
```
## Korišćenje Aplikacije

Proces se sastoji od dva glavna koraka: popunjavanje baze znanja, a zatim pokretanje API servera.

### Korak 1: Popunjavanje Vektorske Baze

Pre nego što možete da postavljate pitanja, morate obraditi vaše dokumente i kreirati vektorsku bazu.

1.  **Dodajte vaše dokumente**: Sve vaše `.pdf`, `.docx`, `.txt` i druge fajlove stavite u `data` folder.
2.  **Pokrenite skriptu**: U terminalu (sa aktiviranim virtuelnim okruženjem), izvršite sledeću komandu:
    ```bash
    python 1_create_or_update_database.py
    ```
    Ova skripta će proći kroz sve dokumente, očistiti ih, podeliti na delove (chunkove), pretvoriti u vektore i sačuvati u `faiss_index` folder. Ako dodate nove dokumente, ponovnim pokretanjem skripte baza će se samo ažurirati.

### Korak 2: Pokretanje API Servera

Kada je baza kreirana, možete pokrenuti FastAPI server.

```bash
uvicorn main:app --reload
```

Ostavite ovaj terminal da radi. Server će sada biti dostupan na adresi `http://127.0.0.1:8000`.

### Korak 3: Testiranje API-ja

Otvorite **novi terminal** (ne gasite onaj u kojem radi server) i koristite priložene skripte za testiranje.

#### Testiranje Generisanja Odgovora
Izvršite skriptu da biste poslali pitanje i dobili odgovor generisan od strane AI.

```bash
python test_pitanje.py
```

#### Testiranje Evaluacije Odgovora
Izvršite skriptu da biste poslali pitanje i odgovor, i dobili ocenu tačnosti.

```bash
python test_evaluacija.py
```
Slobodno menjajte pitanja i odgovore unutar test_pitanje.py i test_evaluacija.py fajlova kako biste testirali različite scenarije.
