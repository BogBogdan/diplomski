# main.py

import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

# Importovanje tvojih AI funkcija i promptova
from ai_functions import pitaj_ollama, pitaj_ai, pitaj_gemini
from prompts import PROMPT_GENERISANJE_ODGOVORA, PROMPT_PREFORMULISANJE_PITANJA, PROMPT_PROVERA_TACNOSTI

# Putanje i konstante
# === Učitavanje konfiguracije iz .env fajla ===
DB_FAISS_PATH = os.getenv("DB_FAISS_PATH", "faiss_index")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
AI_PROVIDER = os.getenv("AI_PROVIDER", "ollama").lower()
INTERNI_MODEL_NAZIV = os.getenv("AI_MODEL_NAME", "llama3")

# === Logika za odabir AI funkcije na osnovu .env fajla ===
if AI_PROVIDER == "ollama":
    INTERNI_AI_POZIV = pitaj_ollama
elif AI_PROVIDER == "openai":
    INTERNI_AI_POZIV = pitaj_ai
elif AI_PROVIDER == "gemini":
    INTERNI_AI_POZIV = pitaj_gemini
else:
    raise ValueError(f"Nepoznat AI_PROVIDER u .env fajlu: '{AI_PROVIDER}'. Molimo izaberite 'ollama', 'openai', ili 'gemini'.")

print(f"--- Konfiguracija učitana: Koristi se {AI_PROVIDER.upper()} sa modelom '{INTERNI_MODEL_NAZIV}' ---")

app = FastAPI(title="Konfigurabilni RAG API")

db = None
embeddings = None
# CORS Middleware
origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def load_rag_components():
    global db
    print("--- Pokretanje servera: Učitavanje RAG komponenti ---")
    if not os.path.exists(DB_FAISS_PATH):
        print(f"GREŠKA: Vektorska baza '{DB_FAISS_PATH}' nije pronađena!")
        return
    try:
        embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL, model_kwargs={'device': 'cpu'})
        db = FAISS.load_local(DB_FAISS_PATH, embeddings, allow_dangerous_deserialization=True)
        print("--- RAG komponente uspešno učitane. Server je spreman. ---")
    except Exception as e:
        print(f"Došlo je do greške prilikom učitavanja RAG komponenti: {e}")
        db = None

@app.get("/")
def read_root():
    return {"message": "Server je pokrenut. Dostupne rute su /pitanje i /proveri-odgovor."}

# --- RUTA 1: Kompletna RAG funkcionalnost (Generisanje odgovora) ---

class PitanjeRequest(BaseModel):
    pitanje: str

@app.post("/pitanje")
async def handle_pitanje(request_data: PitanjeRequest):
    """
    Prima pitanje, pronalazi kontekst u vektorskoj bazi, i generiše novi odgovor.
    (Preformulisanje -> Pretraga -> Generisanje)
    """
    if db is None:
        raise HTTPException(status_code=503, detail="Vektorska baza nije učitana.")

    originalno_pitanje = request_data.pitanje
    print(f"Primljeno pitanje za generisanje odgovora: '{originalno_pitanje}'")

    # Korak 1: Preformulisanje pitanja za bolju pretragu
    print("Korak 1: Preformulisanje pitanja...")
    prompt_za_obradu = PROMPT_PREFORMULISANJE_PITANJA.format(question=originalno_pitanje)
    obradjeno_pitanje = INTERNI_AI_POZIV(prompt_za_obradu, model=INTERNI_MODEL_NAZIV).strip()
    print(f"Preformulisano pitanje za pretragu: '{obradjeno_pitanje}'")

    # Korak 2: RAG Pretraga sa preformulisanim pitanjem
    print("Korak 2: Pretraga vektorske baze...")
    docs = db.similarity_search(obradjeno_pitanje, k=4)
    context = "\n---\n".join([doc.page_content for doc in docs])
    print(context)
    # Korak 3: Generisanje odgovora na osnovu konteksta
    print("Korak 3: Generisanje finalnog odgovora...")
    prompt_za_odgovor = PROMPT_GENERISANJE_ODGOVORA.format(context=context, question=originalno_pitanje)
    finalni_odgovor = INTERNI_AI_POZIV(prompt_za_odgovor, model=INTERNI_MODEL_NAZIV)
    
    return {
        "odgovor": finalni_odgovor,
        "originalno_pitanje": originalno_pitanje,
        "preformulisano_pitanje": obradjeno_pitanje,
        "koriscen_kontekst": context
    }

# --- RUTA 2: Funkcionalnost za Proveru/Evaluaciju Odgovora ---

class EvaluacijaRequest(BaseModel):
    pitanje: str
    odgovor: str

@app.post("/proveri-odgovor")
async def handle_evaluacija(request_data: EvaluacijaRequest):
    """
    Prima pitanje i VEĆ POSTOJEĆI odgovor, pronalazi kontekst, i procenjuje tačnost.
    (Preformulisanje -> Pretraga -> Provera)
    """
    if db is None:
        raise HTTPException(status_code=503, detail="Vektorska baza nije učitana.")

    originalno_pitanje = request_data.pitanje
    odgovor_za_proveru = request_data.odgovor
    print(f"Primljeno za evaluaciju: Pitanje='{originalno_pitanje}', Odgovor='{odgovor_za_proveru}'")

    # Korak 1: Preformulisanje pitanja za RAG pretragu
    print("Korak 1: Preformulisanje pitanja...")
    prompt_za_obradu = PROMPT_PREFORMULISANJE_PITANJA.format(question=originalno_pitanje)
    obradjeno_pitanje_za_pretragu = INTERNI_AI_POZIV(prompt_za_obradu, model=INTERNI_MODEL_NAZIV).strip()
    print(f"Preformulisano pitanje za pretragu: '{obradjeno_pitanje_za_pretragu}'")

    # Korak 2: RAG Pretraga za pronalaženje relevantnog konteksta
    print("Korak 2: Pretraga vektorske baze...")
    docs = db.similarity_search(obradjeno_pitanje_za_pretragu, k=5)
    pronadjen_kontekst = "\n---\n".join([doc.page_content for doc in docs])
    
    # Korak 3: Evaluacija originalnog odgovora pomoću LLM-a
    print("Korak 3: Slanje na finalnu evaluaciju...")
    prompt_za_proveru = PROMPT_PROVERA_TACNOSTI.format(
        question=originalno_pitanje,
        context=pronadjen_kontekst,
        answer=odgovor_za_proveru
    )
    rezultat_provere = INTERNI_AI_POZIV(prompt_za_proveru, model=INTERNI_MODEL_NAZIV)

    # Korak 4: Parsiranje odgovora i vraćanje rezultata
    print("Korak 4: Parsiranje rezultata evaluacije.")
    try:
        ocena = rezultat_provere.split("OCENA:")[1].split("OBJAŠNJENJE:")[0].strip()
        objasnjenje = rezultat_provere.split("OBJAŠNJENJE:")[1].strip()
    except IndexError:
        ocena = "GREŠKA_U_PARSIRANJU"
        objasnjenje = rezultat_provere

    return {
        "ocena": ocena,
        "objasnjenje": objasnjenje,
        "originalno_pitanje": originalno_pitanje,
        "odgovor_koji_se_proverava": odgovor_za_proveru,
        "koriscen_kontekst": pronadjen_kontekst
    }