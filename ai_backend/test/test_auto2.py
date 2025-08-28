import requests
import json
import time
import re
# Adresa na kojoj radi endpoint za evaluaciju
API_URL = "http://127.0.0.1:8000/proveri-odgovor"

# Jedno pitanje koje se koristi za sve testove
pitanje = "Kako proces u Ring algoritmu inicira izbor novog koordinatora?"

# Lista svih odgovora koje želimo da testiramo, od 0/10 do 10/10
# Prilagođeno da liči na odgovore pravih studenata
test_slucajevi = [
    {
        "ocekivana_ocena": "0/10",
        "tekst": "Svi procesi glasaju ko ce biti novi." # Potpuno pogrešan mehanizam, ali ima veze sa "izborom"
    },
    {
        "ocekivana_ocena": "1/10",
        "tekst": "Pošalje poruku." # Apsolutni minimum, spominje se ključna akcija ali bez ikakvog konteksta
    },
    {
        "ocekivana_ocena": "2/10",
        "tekst": "Javi se onom do sebe u krugu." # Tačno, ali krajnje pojednostavljeno. Uvodi koncept "suseda".
    },
    {
        "ocekivana_ocena": "3/10",
        "tekst": "Ako vidi da je koordinator pao, on pokrene election poruku i posalje je dalje." # Uvodi okidač (pad koordinatora) i naziv poruke.
    },
    {
        "ocekivana_ocena": "4/10",
        "tekst": "Prvo vidi da koordinator ne radi. Onda napravi neku listu i pošalje election poruku komšiji." # Dodaje ključni detalj - "lista", iako je nejasno šta ona sadrži.
    },
    {
        "ocekivana_ocena": "5/10",
        "tekst": "Proces koji primeti problem napravi listu, stavi svoj ID u nju, i onda tu listu posalje sledećem u krugu." # Ključni korak! Objašnjava šta se stavlja u listu (svoj ID).
    },
    {
        "ocekivana_ocena": "6/10",
        "tekst": "Proces koji je skontao da je šef pao, on započinje izbore. Kreira poruku za izbor (election) u koju stavi svoj ID i prosledi je svom desnom susedu. Ta poruka onda ide u krug." # Dobar, konverzacijski odgovor. Tačan i dodaje kontekst "ide u krug".
    },
    {
        "ocekivana_ocena": "7/10",
        "tekst": "Proces Pi, kada detektuje pad, kreira novu, praznu listu kandidata. U tu listu doda svoj identifikator i onda šalje poruku `elect` sa tom listom svom susedu." # Formalniji jezik, koristi "Pi" i "identifikator". Vrlo solidan odgovor.
    },
    {
        "ocekivana_ocena": "8/10",
        "tekst": "U prstenu, proces P(i) koji detektuje pad koordinatora kreira *election* poruku. U tu poruku upisuje svoj ID. Zatim šalje tu poruku svom sledećem susedu. Svrha je da poruka obiđe krug i da se u nju dodaju ID-jevi ostalih procesa." # Odličan odgovor. Objašnjava i "kako" i delimično "zašto" (svrha).
    },
    {
        "ocekivana_ocena": "9/10",
        "tekst": "Kada proces Pi uoči da koordinator ne odgovara, on inicira izborni proces. Prvo, kreira novu, praznu aktivnu listu. Zatim, u tu listu dodaje svoj sopstveni identifikator (ili prioritet), i. Nakon toga, šalje poruku `elect(lista)` svom desnom susedu u prstenastoj topologiji." # Skoro savršen odgovor, koristi sve ključne termine.
    },
    {
        "ocekivana_ocena": "10/10",
        "tekst": "Proces Pi, u sistemu organizovanom kao logički prsten, inicira izborni proces (election) u trenutku kada detektuje da koordinator nije dostupan. Inicijacija se sastoji iz dva koraka: 1) Kreira se nova, inicijalno prazna, aktivna lista procesa. 2) Proces Pi u tu listu dodaje sopstveni identifikator (i) i šalje poruku `elect` koja sadrži tu listu svom sledećem susedu u prstenu (successor)." # "Zlatni standard" - udžbenički odgovor.
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
        # Korak 1: Šaljemo zahtev i dobijamo odgovor
        # Ovde sam vratio jednostavniji `json=` poziv jer ste rekli da radi,
        # a problem očigledno nije u slanju nego u primanju podataka.
        response = requests.post(API_URL, json=evaluacija_payload, timeout=180)
        response.raise_for_status()
        print("✅ USPEH! Server je vratio uspešan odgovor.")
        
        # Korak 2: Učitavamo JSON podatke koje je server vratio
        # 'data' sada sadrži {'ocena': ..., 'objasnjenje': ...}
        data = response.json()
        
        # Ispisujemo ceo dobijeni rečnik radi provere
        print("\n" + "="*50)
        print("CEO ODGOVOR SA SERVERA:")
        print("="*50)

        # Korak 3: Izvući string sa detaljnom evaluacijom iz polja "objasnjenje"
        detaljna_evaluacija_string = data.get("objasnjenje", "{}") # Vraćamo prazan JSON string ako "objasnjenje" ne postoji

        # Korak 4: Očistiti taj string od Markdown ```json ... ``` omotača
        pattern = r'^\s*```[a-z-]*\n|\n```\s*$'
        cist_json_string = re.sub(pattern, '', detaljna_evaluacija_string.strip())

        # Korak 5: Parsirati očišćeni string u novi Python rečnik
        detaljni_podaci = json.loads(cist_json_string)

        # Korak 6: SADA možemo bezbedno da pristupimo ugnježdenim poljima
        finalni_rezultat = detaljni_podaci.get("finalni_rezultat", {})
        evaluacija_deo = detaljni_podaci.get("evaluacija", {})

        # Korak 7: Finalni ispis
        print("\n" + "="*50)
        print("REZULTAT EVALUACIJE")
        print("="*50)
        
        print(f"\n[DOBIJENA OCENA]: {finalni_rezultat.get('ocena_tekstualna', 'N/A')}")
        print(f"[REZIME]: {finalni_rezultat.get('rezime_evaluacije', 'N/A')}")
        print("\n[DETALJNA EVALUACIJA (JSON)]:")
        print(json.dumps(evaluacija_deo, indent=2, ensure_ascii=False))
        print("="*50)

    except json.JSONDecodeError as e:
        print("\n❌❌❌ GREŠKA: JSONDecodeError! ❌❌❌")
        print("Nije bilo moguće parsirati JSON iz polja 'objasnjenje'.")
        print(f"Detalji greške: {e}")
        # Ispisujemo problematični string koji smo pokušali da parsiramo
        if 'cist_json_string' in locals():
            print("Pokušali smo da parsiramo ovo:", cist_json_string)
        elif 'detaljna_evaluacija_string' in locals():
            print("Pokušali smo da parsiramo ovo (pre čišćenja):", detaljna_evaluacija_string)

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