# test_bully_vs_ring.py

import requests
import json
import re
import time

# Adresa na kojoj radi endpoint za evaluaciju
API_URL = "http://127.0.0.1:8000/proveri-odgovor"

# Pitanje dizajnirano da proizvede detaljnu ček-listu
pitanje = "Uporedi detaljno algoritme Bully i Ring za izbor koordinatora. Za oba algoritma, objasni sledeće: 1. Kako proces inicira izborni proces nakon što detektuje pad koordinatora? 2. Kome se šalju inicijalne 'elect' poruke? 3. Kako se određuje pobednik izbora? 4. Koji je glavni nedostatak svakog od ovih algoritama?"

# Lista odgovora, od 0/10 do 10/10, prilagođena kompleksnom pitanju
test_slucajevi = [
    {
        "ocekivana_ocena": "0/10",
        "tekst": "To su protokoli za slanje poruka."
    },
    {
        "ocekivana_ocena": "1/10",
        "tekst": "Bully je kad jači pobedi, a Ring je kad poruka ide u krug."
    },
    {
        "ocekivana_ocena": "2/10",
        "tekst": "U Bully algoritmu, proces šalje poruku svima i pobednik je onaj sa najvećim brojem. U Ringu, šalje komšiji." # Spominje oba, ali netačno/nepotpuno.
    },
    {
        "ocekivana_ocena": "3/10",
        "tekst": "Ring: šalje poruku u krug, ko je najjači na listi taj pobeđuje. Mana mu je što je spor." # Ne spominje Bully uopšte. Pokriva 3/4 za Ring.
    },
    {
        "ocekivana_ocena": "4/10",
        "tekst": "Bully: 1. Inicijacija počinje kada proces Pi detektuje pad i pošalje `elect` poruku. 2. Poruke se šalju isključivo procesima sa višim prioritetom (ID-em). 3. Ako Pi ne dobije odgovor u određenom roku, on pobeđuje i obaveštava sve sa `coordinator` porukom. Ako dobije odgovor, odustaje i čeka pobednika. 4. Nedostatak je potencijalno veliki broj poruka i osetljivost na pad procesa tokom izbora." # Pokriva 3/4 za Bully, ali 0/4 za Ring. Daje i pogrešnu manu.
    },
    {
        "ocekivana_ocena": "5/10",
        "tekst": "Bully: šalje poruke svima sa većim ID-em. Ako mu se niko ne javi, on je pobednik. Mana mu je što je spor." # Pokriva 3/4 za Bully, ali 0/4 za Ring. Daje i pogrešnu manu.
    },
    {
        "ocekivana_ocena": "6/10",
        "tekst": "Bully: Proces koji detektuje pad šalje `elect` poruku svim procesima sa višim ID-em. Ako ne dobije odgovor, proglašava sebe koordinatorom. Ako dobije odgovor, odustaje i čeka. Ring: Pi kreira listu, stavi svoj ID i pošalje je desnom susedu. Kada mu se lista vrati, on iz nje odredi pobednika (max ID) i objavi ga. Nedostaci nisu navedeni." # Odličan opis procesa, ali namerno izostavljene mane.
    },
    {
        "ocekivana_ocena": "7/10",
        "tekst": "Bully: Inicijator šalje 'elect' procesima sa višim ID. Ako ne dobije odgovor, pobeđuje i šalje `coordinator` poruku. Mana je (N-1) poruka. Ring: Inicijator šalje listu [i] desnom susedu. Svaki proces dodaje svoj ID. Kad se vrati, inicijator nađe max i objavi pobednika. Mana je što je spor." # Detaljnije od 6/10, ali i dalje ne savršeno.
    },
    {
        "ocekivana_ocena": "7/10",
        "tekst": "Bully: šalje poruke procesima sa ID-em većim od svog. Ako mu niko ne odgovori, on postaje koordinator. Mana je puno poruka. Ring: Proces pošalje listu sa svojim ID-em komšiji. Lista kruži, pobednik je onaj sa najvećim ID-em. Mana je što je spor." # Solidan, ali površan odgovor za sve stavke. Očekujemo 70/100.
    },
        {
        "ocekivana_ocena": "8/10",
        "tekst": "Bully šalje 'elect' poruke onima sa višim ID-em. Pobednik je onaj ko ne dobije odgovor. Ring šalje listu komšiji, pobednik je max ID na listi." # Spominje oba, ali ne spominje mane uopšte.
    },
    {
        "ocekivana_ocena": "9/10",
        "tekst": "Bully: 1. Pi šalje `elect` poruke procesima Pj gde j > i. 2. Ako Pi ne dobije odgovor u roku T, pobeđuje i šalje `coordinator` poruku. Ako dobije, odustaje. 3. Nedostatak je potencijalno veliki broj poruka. Ring: 1. Pi kreira listu [i] i šalje je desnom susedu. 2. Svaki proces dodaje svoj ID i prosleđuje je. 3. Kad se vrati do Pi, on nađe max sa liste i objavi pobednika. 4. Nedostatak je vreme potrebno da poruka obiđe ceo prsten." # Skoro savršeno, fale sitni detalji.
    },
    {
        "ocekivana_ocena": "10/10",
        "tekst": "Bully: 1. Inicijacija počinje kada proces Pi detektuje pad i pošalje `elect` poruku. 2. Poruke se šalju isključivo procesima sa višim prioritetom (ID-em). 3. Ako Pi ne dobije odgovor u određenom roku, on pobeđuje i obaveštava sve sa `coordinator` porukom. Ako dobije odgovor, odustaje i čeka pobednika. 4. Nedostatak je potencijalno veliki broj poruka i osetljivost na pad procesa tokom izbora. \nRing: 1. Inicijacija počinje kada Pi detektuje pad, kreira listu kandidata sa svojim ID-em `[i]`. 2. Poruka se šalje samo jednom procesu - desnom susedu. 3. Svaki proces dodaje svoj ID na listu i prosleđuje je. Kada se poruka vrati inicijatoru Pi, on bira proces sa najvećim ID-em sa liste i šalje `coordinator` poruku. 4. Nedostatak je što je algoritam spor (zahteva pun krug) i nije otporan na pad bilo kog procesa u prstenu tokom izbora." # Udžbenički odgovor.
    }
]


# Prolazimo kroz svaki test slučaj (svaki odgovor)
for i, test_case in enumerate(test_slucajevi):
    print("\n" + "#" * 80)
    print(f"### TESTIRANJE ODGOVORA {i+1}/{len(test_slucajevi)} (Očekivana ocena: {test_case['ocekivana_ocena']}) ###")
    print("#" * 80)

    evaluacija_payload = {
        "pitanje": pitanje,
        "odgovor": test_case['tekst']
    }

    print(f"--- Slanje zahteva na endpoint za evaluaciju: {API_URL} ---")
    print(f"Pitanje: '{evaluacija_payload['pitanje']}'")
    print(f"Odgovor za proveru: '{evaluacija_payload['odgovor']}'")
    print("-" * 50)

    try:
        response = requests.post(API_URL, json=evaluacija_payload, timeout=180)
        response.raise_for_status()
        print("✅ USPEH! Server je vratio uspešan odgovor.", response.json())
        
        detaljni_podaci = response.json()
        
        finalni_rezultat = detaljni_podaci.get("finalni_rezultat", {})
        
        # ############## KLJUČNA IZMENA JE OVDE ##############
        # Server vraća 'tekstualna_ocena', a ne 'ocena_tekstualna'.
        dobijena_ocena = finalni_rezultat.get('ocena_tekstualna', 'GREŠKA: Nije pronađen ključ "tekstualna_ocena"')
        # ######################################################
        
        # Takođe, za rezime je ključ 'rezime', a ne 'rezime_evaluacije'
        rezime = finalni_rezultat.get('rezime', 'N/A') 
        evaluacija_deo = detaljni_podaci.get("evaluacija", {})

        print("\n" + "="*50)
        print("REZULTAT EVALUACIJE")
        print("="*50)
        
        print(f"\n[DOBIJENA OCENA]: {dobijena_ocena}")
        print(f"[OČEKIVANA OCENA]: {test_case['ocekivana_ocena']}")
        print(f"[REZIME]: {rezime}")
        # print("\n[DETALJNA EVALUACIJA (JSON)]:")
        # print(json.dumps(evaluacija_deo, indent=2, ensure_ascii=False))
        print("="*50)

    except json.JSONDecodeError as e:
        print("\n❌❌❌ GREŠKA: JSONDecodeError! ❌❌❌")
        print("Nije bilo moguće parsirati JSON odgovor servera.")
        print(f"Detalji greške: {e}")
        print("Odgovor servera:", response.text)

    except requests.exceptions.HTTPError as e:
        print(f"❌ GREŠKA! Server je vratio status kod: {e.response.status_code}")
        print("Ceo odgovor servera:")
        try:
            print(e.response.json())
        except json.JSONDecodeError:
            print(e.response.text)

    except requests.exceptions.RequestException as e:
        print(f"❌ GREŠKA PRI KONEKCIJI: Nije moguće povezati se sa serverom na {API_URL}.")
        print("   Da li ste pokrenuli main.py server? (uvicorn main:app --reload)")
        print(f"   Detalji greške: {e}")
        break

    print("\n--- Pauza od 2 sekunde pre sledećeg zahteva ---")
    time.sleep(2)

print("\n" + "#" * 80)
print("### Svi testovi su završeni. ###")
print("#" * 80)