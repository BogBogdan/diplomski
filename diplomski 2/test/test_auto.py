import requests
import json
import time

# Adresa na kojoj radi endpoint za evaluaciju
API_URL = "http://127.0.0.1:8000/proveri-odgovor"

# Jedno pitanje koje se koristi za sve testove
pitanje = "Objasni detaljno kako funkcioniše dvofazni protokol prihvatanja (2PC), uključujući obe faze i šta se dešava u slučaju da svi učesnici pristanu, a šta ako barem jedan odustane."

# Lista svih odgovora koje želimo da testiramo, od 0/10 do 10/10
test_slucajevi = [
    {
        "ocekivana_ocena": "0/10",
        "tekst": "2PC protokol funkcioniše tako što koordinator sa najvišim prioritetom šalje poruku o izboru svim ostalim procesima, i ako mu niko ne odgovori, on postaje novi lider sistema."
    },
    {
        "ocekivana_ocena": "1/10",
        "tekst": "Ovaj protokol ima dve faze, sluze za razmenjivanje poruka."
    },
    {
        "ocekivana_ocena": "2/10",
        "tekst": "Dvofazni protokol prihvatanja služi da se procesi u distribuiranom sistemu dogovore. Ima dve faze gde se razmenjuju poruke."
    },
    {
        "ocekivana_ocena": "3/10",
        "tekst": "U prvoj fazi, koordinator pošalje poruku učesnicima. Ako mu odgovore, transakcija je uspešna."
    },
    {
        "ocekivana_ocena": "3.5/10",
        "tekst": "U prvoj fazi, koordinator pošalje poruku učesnicimai pita sve učesnike da li su spremni. Ako mu odgovore, transakcija ide u drugi deo."
    },
    {
        "ocekivana_ocena": "4/10",
        "tekst": "U prvoj fazi, koordinator pita sve učesnike da li su spremni. Ako većina odgovori potvrdno, u drugoj fazi koordinator šalje poruku za prihvatanje transakcije."
    },
    {
        "ocekivana_ocena": "5/10",
        "tekst": "Koordinator u prvoj fazi pita sve da li su spremni. Ako svi kažu \"da\", transakcija se odmah izvršava. Ako neko kaže \"ne\", koordinator samo ponovo pokrene ceo proces."
    },
    {
        "ocekivana_ocena": "6/10",
        "tekst": "Protokol ima dve faze. Faza 1: Koordinator šalje \"prepare\" poruku svim učesnicima. Svi učesnici koji su spremni odgovaraju sa \"ready\". Ako svi odgovore sa \"ready\", koordinator prelazi u Fazu 2. Faza 2: Koordinator šalje \"commit\" poruku svim učesnicima, koji onda lokalno potvrđuju transakciju."
    },
    {
        "ocekivana_ocena": "7/10",
        "tekst": "U prvoj fazi koordinator šalje \"prepare\" poruku i čeka odgovore. U drugoj fazi, ako su svi pristali, on šalje \"commit\" poruku. Ako neko nije pristao, on šalje \"abort\" poruku."
    },
    {
        "ocekivana_ocena": "7.5/10",
        "tekst": "U prvoj fazi koordinator šalje \"prepare\" poruku i čeka odgovore. U drugoj fazi, ako su svi pristali, on šalje \"commit\" poruku. Ako neko nije pristao, on šalje \"abort\" poruku. Tek nakon toga, obaveštava sve učesnike o odluci, koji onda sprovode odgovarajuće lokalne akcije."
    },
    {
        "ocekivana_ocena": "8/10",
        "tekst": "Faza 1: Koordinator šalje \"prepare\" poruku. Ako svi učesnici odgovore sa \"ready\", odluka je \"prihvati\". Ako barem jedan odgovori sa \"abort\" ili ne odgovori na vreme, odluka je \"prekini\". Faza 2: Koordinator obaveštava sve učesnike o odluci (commit/abort), nakon čega oni preduzimaju odgovarajuće lokalne akcije."
    },
    {
        "ocekivana_ocena": "9/10",
        "tekst": "Faza 1: Koordinator šalje \"prepare\" zahtev. Ako svi učesnici odgovore \"ready\", prelazi se na sledeću fazu. Ako ijedan odgovori \"abort\" ili istekne vreme, odluka je \"abort\". Faza 2: Koordinator prvo upisuje konačnu odluku (commit ili abort) u svoj log, a zatim šalje tu poruku svim učesnicima, koji onda izvršavaju lokalne akcije."
    },
    {
        "ocekivana_ocena": "10/10",
        "tekst": "U prvoj fazi, koordinator šalje \"prepare\" poruku svim učesnicima. Ako su svi spremni, odgovaraju sa \"ready\". Ako i samo jedan učesnik odgovori sa \"abort\" ili ne odgovori u zadatom roku, koordinator donosi odluku o prekidu. U drugoj fazi, koordinator prvo trajno upisuje konačnu odluku (<commit T> ili <abort T>) u svoj log, što je nepovratna akcija. Tek nakon toga, obaveštava sve učesnike o odluci, koji onda sprovode odgovarajuće lokalne akcije."
    }
]

# Prolazimo kroz svaki test slučaj (svaki odgovor)
for i, test_case in enumerate(test_slucajevi):
    print("\n" + "#" * 80)
    print(f"### TESTIRANJE ODGOVORA {i+1}/{len(test_slucajevi)} (Očekivana ocena: {test_case['ocekivana_ocena']}) ###")
    print("#" * 80)

    # Podaci koje šaljemo za ovaj konkretan odgovor
    evaluacija_payload = {
        "pitanje": pitanje,
        "odgovor": test_case['tekst']
    }

    print(f"--- Slanje zahteva na endpoint za evaluaciju: {API_URL} ---")
    print(f"Pitanje: '{evaluacija_payload['pitanje']}'")
    print(f"Odgovor za proveru: '{evaluacija_payload['odgovor']}'")
    print("-" * 50)

    try:
        # Šaljemo POST zahtev. Timeout je duži jer AI obrada traje.
        response = requests.post(API_URL, json=evaluacija_payload, timeout=180)

        # Proveravamo statusni kod odgovora.
        response.raise_for_status()

        print("✅ USPEH! Server je vratio uspešan odgovor.")
        
        # Učitavamo JSON podatke iz odgovora
        data = response.json()
        
        print("\n" + "="*50)
        print("REZULTAT EVALUACIJE")
        print("="*50)
        
        # Ispisujemo ključne delove odgovora servera
        print(f"\n[DOBIJENA OCENA]: {data.get('ocena', 'N/A')}")
        print(f"[OBJAŠNJENJE]:\n{data.get('objasnjenje', 'N/A')}")
        print("="*50)

    except requests.exceptions.HTTPError as e:
        # Greške koje vraća server (npr. 404, 500, 503)
        print(f"❌ GREŠKA! Server je vratio status kod: {e.response.status_code}")
        print("Ceo odgovor servera:")
        try:
            print(e.response.json())
        except json.JSONDecodeError:
            print(e.response.text)

    except requests.exceptions.RequestException as e:
        # Greške pri konekciji (npr. ako server nije pokrenut)
        print(f"❌ GREŠKA PRI KONEKCIJI: Nije moguće povezati se sa serverom na {API_URL}.")
        print("   Da li ste pokrenuli main.py server? (uvicorn main:app --reload)")
        print(f"   Detalji greške: {e}")
        # Ako ne možemo da se povežemo sa serverom, nema smisla nastavljati
        break

    # Pauza od 2 sekunde između zahteva da ne bismo preopteretili server
    print("\n--- Pauza od 2 sekunde pre sledećeg zahteva ---")
    time.sleep(2)

print("\n" + "#" * 80)
print("### Svi testovi su završeni. ###")
print("#" * 80)