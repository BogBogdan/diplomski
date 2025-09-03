# main.py

import os
import json
import re
import time
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from typing import Dict, Any, List

load_dotenv()

from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.prompts import PromptTemplate
from ai_functions import pitaj_ollama, pitaj_ai, pitaj_gemini
from prompts import (
    prompt_triage_tree_template,
    prompt_kreiraj_ceklistu_template,
    prompt_oceni_po_ceklisti_template,
    prompt_generisi_varijacije_pitanja_template
)
from parallel_search import izvrsi_paralelnu_pretragu

# --- KONFIGURACIJA ---
DB_FAISS_PATH = os.getenv("DB_FAISS_PATH", "faiss_index")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
AI_PROVIDER = os.getenv("AI_PROVIDER", "ollama").lower()
INTERNI_MODEL_NAZIV = os.getenv("AI_MODEL_NAME", "llama3")
BROJ_REZULTATA = int(os.getenv("BROJ_REZULTATA", 10))
CACHE_TTL_SECONDS = int(os.getenv("CACHE_TTL_SECONDS", 1800))

if AI_PROVIDER == "ollama":    INTERNI_AI_POZIV = pitaj_ollama
elif AI_PROVIDER == "openai":    INTERNI_AI_POZIV = pitaj_ai
elif AI_PROVIDER == "gemini":    INTERNI_AI_POZIV = pitaj_gemini
else:    raise ValueError(f"Nepoznat AI_PROVIDER: '{AI_PROVIDER}'.")

print(f"--- Konfiguracija: AI Provider={AI_PROVIDER.upper()}, Model='{INTERNI_MODEL_NAZIV}' ---")

PROMPT_TRIAGE_TREE = PromptTemplate(
    template=prompt_triage_tree_template,
    input_variables=["question", "answer"]
)
PROMPT_KREIRAJ_CEKLISTU = PromptTemplate(
    template=prompt_kreiraj_ceklistu_template,
    input_variables=["question"]
)
PROMPT_OCENI_PO_CEKLISTI = PromptTemplate(
    template=prompt_oceni_po_ceklisti_template,
    input_variables=["answer", "checklist_json", "context"]
)
PROMPT_GENERISI_VARIJACIJE = PromptTemplate(
    template=prompt_generisi_varijacije_pitanja_template,
    input_variables=["original_question"]
)

# --- GLOBALNE PROMENLJIVE I KEŠ ---
app = FastAPI(title="Finalni Hibridni RAG API")
db = None # db se više ne koristi direktno u API endpointu, ali ostaje radi startup logike
embeddings = None
context_cache = {}
evaluation_cache = {}

# --- FastAPI Middleware i Startup ---
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
@app.on_event("startup")
def load_rag_components():
    global db, embeddings
    print("--- Pokretanje servera: Učitavanje RAG komponenti ---")
    if not os.path.exists(DB_FAISS_PATH):
        print(f"GREŠKA: Vektorska baza '{DB_FAISS_PATH}' nije pronađena!")
        return
    try:
        # Učitavamo samo embeddings. `db` objekat više nije neophodan globalno za API pozive.
        embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL, model_kwargs={'device': 'cpu'})
        # Možemo uraditi probno učitavanje da potvrdimo da je baza ispravna
        db_test = FAISS.load_local(DB_FAISS_PATH, embeddings, allow_dangerous_deserialization=True)
        print("--- RAG komponente (Embeddings i test baze) uspešno učitane. ---")
    except Exception as e:
        print(f"Greška pri učitavanju RAG komponenti: {e}")
        embeddings = None

class EvaluacijaRequest(BaseModel):
    pitanje: str
    odgovor: str
    lekcija: str = None
    predmet: str = None

def prevedi_poene_u_ocenu(poeni: float) -> int:
    if poeni >= 65: return 4
    elif poeni >= 39: return 3
    elif poeni >= 20: return 2
    else: return 1

@app.post("/proveri-odgovor")
async def handle_evaluacija(request_data: EvaluacijaRequest):
    if embeddings is None: # Proveravamo samo da li su embeddings učitani
        raise HTTPException(status_code=503, detail="Vektorska baza (ili embeddings) nije učitana.")

    originalno_pitanje = request_data.pitanje
    odgovor_za_proveru = request_data.odgovor
    lekcija, predmet = request_data.lekcija, request_data.predmet
    current_time = time.time()

    eval_cache_key = f"{originalno_pitanje}::{odgovor_za_proveru}"
    if eval_cache_key in evaluation_cache and (current_time - evaluation_cache[eval_cache_key]['timestamp'] < CACHE_TTL_SECONDS):
        print(f"--- POGODAK U KEŠU (EVALUACIJA) ---")
        return evaluation_cache[eval_cache_key]['data']

    print(f"Primljeno za evaluaciju: Pitanje='{originalno_pitanje}'")

    # === FAZA 1: BRZA TRIJAŽA (0, 5, ili "IZMEĐU") ===
    print("Faza 1: Izvršavanje brze trijaže...")
    try:
        prompt_za_triage = PROMPT_TRIAGE_TREE.format(question=originalno_pitanje, answer=odgovor_za_proveru)
        triage_str = INTERNI_AI_POZIV(prompt_za_triage, model=INTERNI_MODEL_NAZIV)
        triage_data = json.loads(re.sub(r'^\s*```[a-z-]*\n|\n```\s*$', '', triage_str.strip()))
        triage_rezultat = triage_data.get("triage_rezultat")
        print(f"Rezultat trijaže: {triage_rezultat}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Greška tokom faze trijaže: {e}")

    if triage_rezultat == 0 or triage_rezultat == 5:
        print("Faza 1.1: Odgovor je ekstreman (0 ili 5). Vraćam direktan rezultat.")
        finalni_podaci = {"ocena_numericka": triage_rezultat, "ocenjene_stavke": [], "rezime_evaluacije": triage_data.get("obrazloženje", "Evaluacija završena u fazi trijaže.")}
        evaluation_cache[eval_cache_key] = {'data': finalni_podaci, 'timestamp': current_time}
        return finalni_podaci

    print("Faza 2: Odgovor zahteva detaljnu analizu.")

    # FAZA 2.1: Generisanje podataka za pretragu
    print("Faza 2.1: Generisanje varijacija pitanja za poboljšanu pretragu.")
    slicna_pitanja, potencijalni_odgovor, kljucne_reci = [], "", []
    try:
        prompt_za_varijacije = PROMPT_GENERISI_VARIJACIJE.format(original_question=originalno_pitanje)
        varijacije_str = INTERNI_AI_POZIV(prompt_za_varijacije, model=INTERNI_MODEL_NAZIV)
        cist_json_varijacija = re.sub(r'^\s*```[a-z-]*\n|\n```\s*$', '', varijacije_str.strip())
        generisani_podaci = json.loads(cist_json_varijacija)

        slicna_pitanja = generisani_podaci.get("slicna_pitanja", [])
        potencijalni_odgovor = generisani_podaci.get("potencijalni_odgovor", "")
        kljucne_reci = generisani_podaci.get("kljucne_reci", [])

        print(f" -> Generisano sličnih pitanja: {len(slicna_pitanja)}")
        print(f" -> Generisan potencijalni odgovor: {'Da' if potencijalni_odgovor else 'Ne'}")
        print(f" -> Generisano ključnih reči: {kljucne_reci}")

    except Exception as e:
        print(f"UPOZORENJE: Greška pri generisanju varijacija pitanja: {e}. Nastavljam sa osnovnom pretragom.")

    try:
        # =================================================================
        # === POZIV ISPRAVLJEN U SKLADU SA TVOJOM DEFINICIJOM FUNKCIJE ===
        # =================================================================
        rezultati_pretrage = await izvrsi_paralelnu_pretragu(
            originalno_pitanje=originalno_pitanje,
            slicna_pitanja=slicna_pitanja,
            provera_odgovor=potencijalni_odgovor,
            provera_kljucne_reci=kljucne_reci,
            db_path=DB_FAISS_PATH,              # <-- ISPRAVLJENO: Prosleđuje se putanja do baze
            embeddings=embeddings,              # <-- ISPRAVLJENO: Prosleđuje se embeddings objekat
            predmet=predmet,
            lekcija=lekcija,
            broj_rezultata=BROJ_REZULTATA        # <-- ISPRAVLJENO: Ime parametra je 'broj_rezultata'
        )
        # =================================================================

        if rezultati_pretrage and isinstance(rezultati_pretrage, list):
             print(f"Paralelna pretraga vratila {len(rezultati_pretrage)} rezultata.")
             pronadjen_kontekst = "\n\n---\n\n".join([str(rezultat) for rezultat in rezultati_pretrage])
        else:
            pronadjen_kontekst = "Nije pronađen relevantan kontekst putem paralelne pretrage."
            
        if not pronadjen_kontekst.strip():
             pronadjen_kontekst = "Nije pronađen relevantan kontekst putem paralelne pretrage."

    except Exception as e:
        print(f"Greška tokom izvršavanja paralelne pretrage: {e}")
        pronadjen_kontekst = "Greška pri dobijanju konteksta."



    # KORAK 2.2: KREIRANJE ČEK-LISTE
    print("Faza 2.2: Kreiranje ček-liste za detaljno ocenjivanje.")
    print("NEKA PRIMENA EVO JE "+ pronadjen_kontekst)
    try:
        prompt_za_stavke = PROMPT_KREIRAJ_CEKLISTU.format(question=originalno_pitanje)
        stavke_str = INTERNI_AI_POZIV(prompt_za_stavke, model=INTERNI_MODEL_NAZIV)
        cist_json_str = re.sub(r'^\s*```[a-z-]*\n|\n```\s*$', '', stavke_str.strip())
        generisane_stavke_data = json.loads(cist_json_str)
        lista_stavki = generisane_stavke_data.get("stavke_za_proveru", [])

        if not lista_stavki:
            raise ValueError("AI nije uspeo da generiše stavke za proveru.")

        broj_stavki = len(lista_stavki)
        poeni_po_stavci = round(100 / broj_stavki, 2)
        finalna_ceklista_lista = [{"stavka": stavka_text, "max_poena": poeni_po_stavci} for stavka_text in lista_stavki]
        checklist_json = json.dumps(finalna_ceklista_lista)
        
        print(f"Generisano {broj_stavki} stavki, svaka nosi {poeni_po_stavci} poena.")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Greška pri kreiranju ček-liste: {e}")

    # KORAK 2.3: DETALJNO OCENJIVANJE PO POENIMA (1-4)
    print("Faza 2.3: Izvršavanje detaljnog ocenjivanja po poenima za ocene 1-4.")
    try:
        prompt_za_ocenu = PROMPT_OCENI_PO_CEKLISTI.format(answer=odgovor_za_proveru, checklist_json=checklist_json, context=pronadjen_kontekst)
        finalni_rezultat_str = INTERNI_AI_POZIV(prompt_za_ocenu, model=INTERNI_MODEL_NAZIV)
        ai_analiza = json.loads(re.sub(r'^\s*```[a-z-]*\n|\n```\s*$', '', finalni_rezultat_str.strip()))
        
        ukupno_poena = ai_analiza.get("ukupno_osvojeno_poena", 0)
        print(f"Ukupno osvojeno poena: {ukupno_poena}/100")
        numericka_ocena = prevedi_poene_u_ocenu(ukupno_poena)
        
        strukturirani_odgovor = {
            "ocena_numericka": numericka_ocena,
            "ocenjene_stavke": ai_analiza.get("detaljna_analiza_po_stavkama", []),
            "rezime_evaluacije": f"Odgovor je detaljno analiziran. Osvojeno je {ukupno_poena:.2f}/100 poena, što odgovara oceni {numericka_ocena}."
        }
        
        evaluation_cache[eval_cache_key] = {'data': strukturirani_odgovor, 'timestamp': current_time}
        return strukturirani_odgovor

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Greška tokom finalne evaluacije po poenima: {e}")