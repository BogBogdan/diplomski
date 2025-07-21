import requests
import json

# Adresa na kojoj radi endpoint za evaluaciju
API_URL = "http://127.0.0.1:8000/proveri-odgovor"

# Podaci koje šaljemo: pitanje i odgovor koji želimo da evaluiramo
# NAMERNO smo stavili blago pogrešan odgovor da bismo testirali evaluaciju.
# (Tačno je U = I * R, a ne U = I / R)
evaluacija_payload = {
    "pitanje": "Šta je globalni direktorijum?",
    "odgovor": "Globalni direktorijum je osnovni folder na lokalnom disku, obično označen sa C:\\, iz kojeg proizilaze svi ostali fajlovi."
}

print(f"--- Slanje zahteva na endpoint za evaluaciju: {API_URL} ---")
print(f"Pitanje: '{evaluacija_payload['pitanje']}'")
print(f"Odgovor za proveru: '{evaluacija_payload['odgovor']}'")
print("-" * 50)

try:
    # Šaljemo POST zahtev. Timeout je duži jer AI obrada traje.
    response = requests.post(API_URL, json=evaluacija_payload, timeout=180)

    # Proveravamo statusni kod odgovora.
    # raise_for_status() će automatski baciti grešku za status kodove 4xx ili 5xx.
    response.raise_for_status()

    print("✅ USPEH! Server je vratio uspešan odgovor.")
    
    # Učitavamo JSON podatke iz odgovora
    data = response.json()
    
    print("\n" + "="*50)
    print("REZULTAT EVALUACIJE")
    print("="*50)
    
    # Ispisujemo ključne delove odgovora servera
    print(f"\n[OCENA]: {data.get('ocena', 'N/A')}")
    print(f"\n[OBJAŠNJENJE]:\n{data.get('objasnjenje', 'N/A')}")
    
    # Opciono, možete otkomentarisati da vidite kontekst
    # print("\n" + "-"*50)
    # print("[KONTEKST KORIŠĆEN ZA EVALUACIJU]:")
    # print(data.get('koriscen_kontekst', 'Nema konteksta.'))
    # print("="*50)

except requests.exceptions.HTTPError as e:
    # Greške koje vraća server (npr. 404, 500, 503)
    print(f"❌ GREŠKA! Server je vratio status kod: {e.response.status_code}")
    print("Ceo odgovor servera:")
    try:
        # Pokušaj da ispišeš JSON grešku ako postoji
        print(e.response.json())
    except json.JSONDecodeError:
        print(e.response.text)

except requests.exceptions.RequestException as e:
    # Greške pri konekciji (npr. ako server nije pokrenut)
    print(f"❌ GREŠKA PRI KONEKCIJI: Nije moguće povezati se sa serverom na {API_URL}.")
    print("   Da li ste pokrenuli main.py server? (uvicorn main:app --reload)")
    print(f"   Detalji greške: {e}")