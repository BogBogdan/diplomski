import os
import openai
import google.generativeai as genai
import ollama
from dotenv import load_dotenv
from typing import List
from PIL import Image

load_dotenv()
print("Učitan .env fajl.")
# --- Inicijalizacija Klijenata ---

# 1. OpenAI Klijent
# Automatski traži ključ u 'OPENAI_API_KEY'
try:
    openai_client = openai.OpenAI()
    print("OpenAI klijent uspešno inicijalizovan.")
except Exception as e:
    openai_client = None
    print(f"Greška pri inicijalizaciji OpenAI klijenta. Proverite 'OPENAI_API_KEY'.")

# 2. Google Gemini Klijent
# Automatski traži ključ u 'GOOGLE_API_KEY'
try:
    genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
    print("Google Gemini klijent uspešno konfigurisan.")
    gemini_configured = True
except Exception as e:
    gemini_configured = False
    print(f"Greška pri konfiguraciji Google Gemini. Proverite 'GOOGLE_API_KEY'.")
    
# 3. Ollama Klijent
# Ne zahteva ključ, samo da je Ollama aplikacija pokrenuta.

# --- Definicije Funkcija ---

def pitaj_ai(poruka_korisnika: str, model: str = "gpt-3.5-turbo") -> str:
    """
    Šalje poruku OpenAI API-ju i vraća odgovor modela.
    """
    if not openai_client:
        return "Greška: OpenAI klijent nije inicijalizovan."
        
    try:
        response = openai_client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "Ti si koristan AI asistent."},
                {"role": "user", "content": poruka_korisnika}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Greška prilikom poziva OpenAI API-ja: {e}"

def pitaj_gemini_sa_slikama(prompt_tekst: str, lista_putanja_slika: List[str], model: str = "gemini-1.5-flash-latest") -> str:
    """
    Šalje tekstualni prompt i listu slika Gemini modelu.
    Ako slika na nekoj putanji ne postoji ili se ne može učitati, tiho je preskače i nastavlja sa ostalima.
    """
    if not gemini_configured:
        return "Greška: Google Gemini klijent nije pravilno konfigurisan. Proverite API ključ."

    try:
        # Odabir modela
        generative_model = genai.GenerativeModel(model)
        
        # Priprema sadržaja: Prvi element je tekst, a zatim slike
        sadrzaj_za_slanje = [prompt_tekst]
        
        for putanja in lista_putanja_slika:
            try:
                # Pokušavamo da učitamo sliku
                slika = Image.open(putanja)
                # Ako je uspešno, dodajemo je u listu za slanje
                sadrzaj_za_slanje.append(slika)
            except Exception:
                # Ako dođe do BILO KAKVE greške pri otvaranju slike (ne postoji, oštećena je...),
                # samo prelazimo na sledeću sliku bez prekida i bez poruke.
                continue
        
        # Slanje zahteva sa svim slikama koje su uspešno učitane
        response = generative_model.generate_content(sadrzaj_za_slanje)
        
        return response.text
        
    except Exception as e:
        # Ovaj blok sada hvata samo greške vezane za Gemini API, ne za učitavanje fajlova.
        return f"Greška prilikom poziva Gemini API-ja: {e}"

def pitaj_gemini(poruka_korisnika: str, model: str = "gemini-1.5-flash-latest") -> str:
    """
    Šalje poruku Google Gemini API-ju i vraća odgovor modela.
    """
    if not gemini_configured:
        return "Greška: Google Gemini nije konfigurisan."
        
    try:
        # Instanciramo model koji želimo da koristimo
        generative_model = genai.GenerativeModel(model)
        # Generišemo odgovor
        response = generative_model.generate_content(poruka_korisnika)
        return response.text
    except Exception as e:
        return f"Greška prilikom poziva Google Gemini API-ja: {e}"

def pitaj_ollama(poruka_korisnika: str, model: str = "llama3") -> str:
    """
    Šalje poruku lokalno pokrenutom Ollama modelu.
    NAPOMENA: Ollama aplikacija mora biti pokrenuta na vašem računaru.
    """
    try:
        response = ollama.chat(
            model=model, # Npr. "llama3", "mistral", "phi3"
            messages=[
                {"role": "user", "content": poruka_korisnika}
            ]
        )
        return response['message']['content']
    except ollama.ResponseError as e:
        return f"Greška od Ollama servera: {e.error}. Da li model '{model}' postoji? Probajte 'ollama pull {model}'."
    except Exception as e:
        return f"Greška pri komunikaciji sa Ollamom: {e}. Da li je Ollama pokrenuta?"

# --- Primeri Korišćenja ---
if __name__ == "__main__":
    pitanje = "Objasni koncept 'deadlock'-a u operativnim sistemima u tri rečenice."
    
    print("\n" + "="*50)
    print("Testiranje OpenAI modela...")
    print(f"Pitanje: {pitanje}")
    odgovor_openai = pitaj_ai(pitanje)
    print(f"Odgovor (OpenAI): \n{odgovor_openai}")
    print("="*50)

    print("\n" + "="*50)
    print("Testiranje Google Gemini modela...")
    print(f"Pitanje: {pitanje}")
    odgovor_gemini = pitaj_gemini(pitanje)
    print(f"Odgovor (Gemini): \n{odgovor_gemini}")
    print("="*50)

    print("\n" + "="*50)
    print("Testiranje lokalnog Ollama modela...")
    print("NAPOMENA: Ollama mora biti pokrenuta da bi ovo radilo!")
    print(f"Pitanje: {pitanje}")
    # Možete promeniti model u onaj koji imate skinut, npr. "mistral"
    odgovor_ollama = pitaj_ollama(pitanje, model="llama3") 
    print(f"Odgovor (Ollama): \n{odgovor_ollama}")
    print("="*50)