from typing import Dict, Any, List

def izracunaj_i_primeni_bonus(podaci: Dict[str, Any]) -> Dict[str, Any]:
    """
    Prima parsiran JSON sa evaluacijom, primenjuje logiku za bonus poene,
    i vraća ažuriran JSON objekat.
    """
    try:
        # Bezbedno pristupanje podacima, sa podrazumevanim vrednostima ako nešto fali
        evaluacija = podaci.get("evaluacija", {})
        ocenjene_stavke = evaluacija.get("2_ocenjene_stavke", [])
        preliminarni_obracun = evaluacija.get("3_preliminarni_obracun", {})
        finalna_validacija = evaluacija.get("4_finalna_validacija", {})
        finalni_rezultat = podaci.get("finalni_rezultat", {})
        
        preliminarna_ocena = preliminarni_obracun.get("preliminarna_ocena", 0)

        if not ocenjene_stavke:
            print("Bonus logika preskočena: Nema ocenjenih stavki.")
            return podaci # Vrati original ako nema podataka za rad

        # Korak 1: Prebrojavanje kategorija
        broj_potpuno_pokriveno = 0
        broj_pokriveno = 0
        broj_ostalih = 0

        for stavka in ocenjene_stavke:
            kategorija = stavka.get("kategorija")
            if kategorija == "potpuno_tačan":
                broj_potpuno_pokriveno += 1
            elif kategorija == "uglavnom_tačan":
                broj_pokriveno += 1
            else:
                broj_ostalih += 1

        # Korak 2: Provera uslova
        uslov_A_ispunjen = (broj_ostalih < 2)
        # Uslov B ima smisla proveravati samo ako je Uslov A ispunjen
        uslov_B_ispunjen = uslov_A_ispunjen and (broj_potpuno_pokriveno >= broj_pokriveno)

        # Korak 3: Izračunavanje bonusa
        bonus_poeni = 0
        obrazlozenje_bonusa = "Bonus nije primenjen."

        if uslov_A_ispunjen:
            bonus_poeni += 10
            obrazlozenje_bonusa = "Bonus od 5 poena dodat jer su sve stavke 'pokriveno' ili 'potpuno_pokriveno'."
        
        if uslov_B_ispunjen:
            bonus_poeni += 10 # Dodajemo JOS 5, ukupno 10
            obrazlozenje_bonusa = "Ukupni bonus od 10 poena dodat (5 za pokrivenost + 5 za dominaciju 'potpuno_pokriveno')."


        print(f"--- Logika za bonus ---")
        print(f"Stavke: Potpuno: {broj_potpuno_pokriveno}, Pokriveno: {broj_pokriveno}, Ostalih: {broj_ostalih}")
        print(f"Uslov A (sve pokriveno/potpuno): {uslov_A_ispunjen}")
        print(f"Uslov B (dominacija potpuno): {uslov_B_ispunjen}")
        print(f"Dodatni bonus poeni: {bonus_poeni}")

        # Korak 4: Ažuriranje konačne ocene i JSON objekta
        if bonus_poeni > 0:
            konacna_ocena = preliminarna_ocena + bonus_poeni
            # Ograničavanje ocene na maksimalno 100
            konacna_ocena = min(konacna_ocena, 100.0)

            # Ažuriranje celog objekta
            finalna_validacija["konacna_ocena"] = konacna_ocena
            finalna_validacija["obrazlozenje"] = obrazlozenje_bonusa
            
            finalni_rezultat["ocena_numericka"] = round(konacna_ocena)
            finalni_rezultat["ocena_tekstualna"] = f"{round(konacna_ocena)}/100"
            # Opciono: ažuriranje i rezimea
            if "rezime_evaluacije" in finalni_rezultat:
                 finalni_rezultat["rezime_evaluacije"] += f" Primenjen je bonus od {bonus_poeni} poena."

    except Exception as e:
        print(f"GREŠKA u logici za bonus: {e}")
        # U slučaju greške, vraćamo originalne podatke da ne srušimo ceo proces
        return podaci
        
    return podaci