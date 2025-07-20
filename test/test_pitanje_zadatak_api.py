# test_pitanje_zadatak.py

import requests
import json

# Adresa na kojoj radi tvoj FastAPI server
API_URL = "http://127.0.0.1:8000/pitanje-zadatak"

# Podaci koje šaljemo - i pitanje i zadatak
# Slobodno menjaj vrednosti da testiraš različite scenarije
payload = {
    "pitanje": "Koje su glavne odlike Llama 3 modela?",
    "zadatak": "Odgovori kratko i sažeto, u formi liste sa buletima."
}


print(f"--- Slanje zahteva na endpoint: {API_URL} ---")
print(f"Pitanje koje se šalje: '{payload['pitanje']}'")
print(f"Zadatak koji se šalje: '{payload['zadatak']}'")
print("-------------------------------------------------")

try:
    # Šaljemo POST zahtev sa našim podacima u JSON formatu
    response = requests.post(API_URL, json=payload, timeout=120)

    # Proveravamo statusni kod odgovora
    if response.status_code == 200:
        print("✅ USPEH! Server je vratio status kod 200 (OK).")
        
        # Učitavamo JSON podatke iz odgovora
        data = response.json()
        
        print("\nPrimljeni odgovor od servera:")
        print("-------------------------------------------------")
        print(f"Odgovor: {data.get('odgovor', 'Nije pronađen ključ "odgovor" u odgovoru.')}")
        print("-------------------------------------------------")
        
    else:
        # Ako status nije 200, ispisujemo grešku
        print(f"❌ GREŠKA! Server je vratio status kod: {response.status_code}")
        print("Ceo odgovor servera:")
        print(response.text)

except requests.exceptions.RequestException as e:
    # Hvatamo greške pri konekciji
    print(f"❌ GREŠKA PRI KONEKCIJI: Nije moguće povezati se sa serverom na {API_URL}.")
    print("   Da li ste pokrenuli main.py server? (uvicorn main:app --reload)")
    print(f"   Detalji greške: {e}")