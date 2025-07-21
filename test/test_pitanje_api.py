# test_pitanje.py (ispravljena verzija)

import requests
import json

# Adresa na kojoj radi tvoj FastAPI server
API_URL = "http://127.0.0.1:8000/pitanje"

# Pitanje koje želiš da pošalješ
# Slobodno promeni ovo pitanje u bilo šta što želiš da testiraš
pitanje_payload = {
    "pitanje": " Da li bi mogao da mi kazes sta memorijski prostor?"
}

print(f"--- Slanje zahteva na endpoint: {API_URL} ---")
print(f"Pitanje koje se šalje: '{pitanje_payload['pitanje']}'")
print("-------------------------------------------------")

try:
    # Šaljemo POST zahtev sa našim pitanjem u JSON formatu
    # Timeout je postavljen na 120 sekundi, jer LLM-u može trebati vremena da odgovori
    response = requests.post(API_URL, json=pitanje_payload, timeout=120)

    # Proveravamo statusni kod odgovora
    if response.status_code == 200:
        print("✅ USPEH! Server je vratio status kod 200 (OK).")
        
        # Učitavamo JSON podatke iz odgovora
        data = response.json()
        
        print("\nPrimljeni odgovor od servera:")
        print("-------------------------------------------------")
        # Koristimo .get() da izbegnemo grešku ako ključ ne postoji
        # OVDE JE ISPRAVKA: Uklonjeni su dupli navodnici oko reči 'odgovor'
        print(f"Odgovor: {data.get('odgovor', 'Nije pronađen ključ odgovor u odgovoru.')}")
        print("-------------------------------------------------")
        
        # Možeš otkomentarisati sledeću liniju ako želiš da vidiš i kontekst
        # print("\nKontekst koji je korišćen za generisanje odgovora:")
        # print(data.get('koriscen_kontekst', 'Nema konteksta.'))

    else:
        # Ako status nije 200, ispisujemo grešku
        print(f"❌ GREŠKA! Server je vratio status kod: {response.status_code}")
        print("Ceo odgovor servera:")
        print(response.text)

except requests.exceptions.RequestException as e:
    # Hvatamo greške pri konekciji (npr. ako server nije pokrenut)
    print(f"❌ GREŠKA PRI KONEKCIJI: Nije moguće povezati se sa serverom na {API_URL}.")
    print("   Da li ste pokrenuli main.py server? (uvicorn main:app --reload)")
    print(f"   Detalji greške: {e}")