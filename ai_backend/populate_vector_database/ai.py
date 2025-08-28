from typing import List

import sys
import os
import re
import time
from populate_vector_database.dto import object_parser

trenutna_putanja = os.path.dirname(os.path.abspath(__file__))
koren_projekta = os.path.abspath(os.path.join(trenutna_putanja, '..'))

if koren_projekta not in sys.path:
    sys.path.append(koren_projekta)

from ai_functions import pitaj_gemini_sa_slikama
from prompts import PROMPT_LOGICAL_CHUNKING_V2


def izdvoj_imena_slika_iz_stringa(tekst: str, img_direktorijum: str = "./izvucene_slike") -> List[str]:
   
    regex_slike = r'[\w-]+\.(?:jpg|jpeg|png|gif|bmp|webp)'
    imena_slika = re.findall(regex_slike, tekst, re.IGNORECASE)

    putanje_do_slika = [os.path.join(img_direktorijum, ime) for ime in imena_slika]
    
    return putanje_do_slika


def get_ai_chunks(lista_stringova: List[str], time_to_wait: int = 5, img_direktorijum: str = "./izvucene_slike") -> List[str]:

    finalni_obradjeni_chunkovi = []

    for i, chunk in enumerate(lista_stringova):
        imena_slika = izdvoj_imena_slika_iz_stringa(chunk, img_direktorijum)
        
        prethodni_chunk = lista_stringova[i-1] if i > 0 else "Nema prethodnog sadržaja."
        sledeci_chunk = lista_stringova[i+1] if i < len(lista_stringova) - 1 else "Nema sledećeg sadržaja."
        
        formatirani_prompt = PROMPT_LOGICAL_CHUNKING_V2.format(
            trenutni_chunk=chunk,
            prethodni_chunk=prethodni_chunk,
            sledeci_chunk=sledeci_chunk
        )

        ai_odgovor = ""
        while ai_odgovor == "":
            try:
                ai_odgovor = pitaj_gemini_sa_slikama(
                    prompt_tekst=formatirani_prompt,
                    lista_putanja_slika=imena_slika
                )
            except Exception as e:
                print(f"Greška pri pozivanju AI: {e}. Pokušavam ponovo za {time_to_wait} sekundi...")
            
            if ai_odgovor == "":
                time.sleep(time_to_wait)

        finalni_obradjeni_chunkovi.extend(object_parser(ai_odgovor))

        print(f"Obrađujem chunk {i+1}/{len(lista_stringova)}...")

        time.sleep(time_to_wait)

    return finalni_obradjeni_chunkovi