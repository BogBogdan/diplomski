import os
import sys
import fitz  # PyMuPDF biblioteka
from langchain_text_splitters import RecursiveCharacterTextSplitter
from typing import List
import numpy as np
from PIL import Image  # Važno za analizu slika
import io 


trenutna_putanja = os.path.dirname(os.path.abspath(__file__))
koren_projekta = os.path.abspath(os.path.join(trenutna_putanja))

if koren_projekta not in sys.path:
    sys.path.append(koren_projekta)

from util_functions import ocisti_tekst


def ekstraktuj_i_podeli_tekst(
    pdf_file: str, 
    img_output_dir: str = "izvucene_slike",
    chunk_size: int = 2000,
    chunk_overlap: int = 200,
    min_dimenzija: int = 20,
    min_velicina_kb: float = 2.0,
    prag_tamne: int = 60,         # Pikseli tamniji od ove vrednosti su "tamni"
    prag_svetle: int = 195,       # Pikseli svetliji od ove vrednosti su "svetli"
    minimalni_procenat: float = 1.0 # Min % tamnih I svetlih piksela da bi slika prošla
) -> List[str]:

    print(f">>> Koristim funkciju sa analizom distribucije boja <<<")
    try:
        if not os.path.exists(img_output_dir): os.makedirs(img_output_dir)
            
        doc = fitz.open(pdf_file)
        ceo_dokument_tekst = ""
        broj_sacuvanih_slika = 0

        for page_index, page in enumerate(doc):
            slajd_broj = page_index + 1

            # if file_type == "pp":
            #     ceo_dokument_tekst += f"\n\n--- SLAJD {slajd_broj} ---\n"
            
            tekst_sa_slajda = page.get_text("text")
            # POZIVAMO NAŠU NOVU, PAMETNU FUNKCIJU ZA ČIŠĆENJE
            cleaned_text = ocisti_tekst(tekst_sa_slajda)
            
            if cleaned_text:
                ceo_dokument_tekst += cleaned_text + "\n"

            image_list = page.get_images(full=True)
            slike_na_slajdu_za_tekst = []

            if image_list:
                for image_index, img_info in enumerate(image_list, start=1):
                    try:
                        base_image = doc.extract_image(img_info[0])
                        if base_image.get("width", 0) < min_dimenzija or base_image.get("height", 0) < min_dimenzija:
                            continue
                        if (len(base_image["image"]) / 1024.0) < min_velicina_kb:
                            continue
                        
                        # --- NOVI FILTER: Analiza distribucije boja ---
                        slika_obj = Image.open(io.BytesIO(base_image["image"]))
                        slika_siva = slika_obj.convert("L")
                        niz_piksela = np.array(slika_siva)
                        
                        # Izračunavanje procenta tamnih i svetlih piksela
                        ukupan_broj_piksela = niz_piksela.size
                        broj_tamnih = np.sum(niz_piksela < prag_tamne)
                        broj_svetlih = np.sum(niz_piksela > prag_svetle)
                        
                        procenat_tamnih = (broj_tamnih / ukupan_broj_piksela) * 100
                        procenat_svetlih = (broj_svetlih / ukupan_broj_piksela) * 100
                        
                        # Logika filtera: Odbaci ako nema dovoljno tamnih ILI nema dovoljno svetlih
                        if procenat_tamnih < minimalni_procenat or procenat_svetlih < minimalni_procenat:
                            # print(f"  > Slika {image_index} ODBAČENA: Tamni: {procenat_tamnih:.2f}%, Svetli: {procenat_svetlih:.2f}%")
                            continue

                        # Ako je slika prošla sve, čuvamo je
                        image_filename = f"slajd_{slajd_broj}_slika_{image_index}.{base_image['ext']}"
                        image_path = os.path.join(img_output_dir, image_filename)
                        with open(image_path, "wb") as img_file:
                            img_file.write(base_image["image"])
                        
                        slike_na_slajdu_za_tekst.append(image_filename)
                        broj_sacuvanih_slika += 1
                    except Exception:
                        continue

            # if slike_na_slajdu_za_tekst:
            #     if file_type == "pp":
            #         ceo_dokument_tekst += "\n[Smislene slike na ovom slajdu:]\n"
            #     else:
            #         ceo_dokument_tekst += "\n[Relevantne slike na ovoj stranici:]\n"
                ceo_dokument_tekst += "\n[Relevantne slike za ovaj deo:]\n"
                for fname in slike_na_slajdu_za_tekst:
                    ceo_dokument_tekst += f"- {fname}\n"

        doc.close()

        # if broj_sacuvanih_slika == 0 and not any(c.strip() for c in ceo_dokument_tekst.split("---") if "SLAJD" in c):
        #     print("Upozorenje: Nije izvučen nikakav smisleni sadržaj.")
        #     return []


        text_splitter = RecursiveCharacterTextSplitter(
                separators=["\n\n", "\n", " ", ""],
                chunk_size=chunk_size, 
                chunk_overlap=chunk_overlap 
            )

        chunks = text_splitter.split_text(ceo_dokument_tekst)
        print(f"\nObrada završena. Sačuvano {broj_sacuvanih_slika} smislenih slika.")
        print(f"Sadržaj podeljen na {len(chunks)} delova.")
        return chunks
    except Exception as e:
        print(f"Došlo je do neočekivane globalne greške: {e}")
        return []
