import fitz  # PyMuPDF biblioteka




def proveri_poreklo_pdf(pdf_file: str) -> str:
    """
    Finalna, poboljšana verzija koja proverava 'creator', 'producer' i 'title' polja.
    """
    try:
        doc = fitz.open(pdf_file)
        metadata = doc.metadata
        doc.close()

        # Konvertujemo sve relevantne metapodatke u mala slova za lakšu pretragu
        creator = metadata.get('creator', '').lower()
        producer = metadata.get('producer', '').lower()
        title = metadata.get('title', '').lower() # DODATO: proveravamo i naslov

        # Prioritetna provera - tražimo "powerpoint" ili "ppt" u bilo kom od ključnih polja
        if 'powerpoint' in creator or 'powerpoint' in producer or 'powerpoint' in title:
            return "PowerPoint"
        if '.ppt' in title: # Proveravamo i ekstenziju .ppt ili .pptx u naslovu
            return "PowerPoint"

        # Provera za Word
        if 'word' in creator or 'msword' in creator or 'word' in title:
            return "Word"

        # Opšta provera za Microsoft ako specifične nisu uspele
        if 'microsoft' in creator or 'microsoft' in producer:
            return "Microsoft Office Document"

        return "Unknown"

    except Exception as e:
        print(f"Greška pri čitanju metapodataka: {e}")
        return "Error"
# --- POMOĆNA FUNKCIJA 2: Analiza strukture ---

def debug_analiziraj_strukturu(pdf_file: str):
    """
    Ispisuje detaljne informacije o strukturi PDF-a radi debagovanja.
    """
    try:
        doc = fitz.open(pdf_file)
        
        if len(doc) == 0:
            print("Rezultat: Prazan dokument")
            return

        all_widths = []
        all_heights = []
        for i, page in enumerate(doc):
            width = page.rect.width
            height = page.rect.height
            all_widths.append(width)
            all_heights.append(height)

        # Uzimamo prvu stranicu kao referencu
        first_page_width = all_widths[0]
        first_page_height = all_heights[0]
        
        # --- Heurističke provere sa ispisom ---
        
        # 1. Da li je landscape?
        is_landscape = first_page_width > first_page_height
        # 2. Koji je tačan aspect ratio?
        if first_page_height == 0:
            return
        aspect_ratio = first_page_width / first_page_height
  
        # 3. Da li upada u naše definisane opsege za prezentaciju?
        is_4_3_ratio = (1.25 < aspect_ratio < 1.45)
        is_16_9_ratio = (1.65 < aspect_ratio < 1.85)
        is_presentation_ratio = is_4_3_ratio or is_16_9_ratio

        # 4. Da li su sve stranice identične veličine?
        sizes_are_consistent = all(w == first_page_width and h == first_page_height for w, h in zip(all_widths, all_heights))

        # Finalna odluka na osnovu starih pravila
        final_decision = "Neodređeno"
        if is_landscape and is_presentation_ratio and sizes_are_consistent:
            final_decision = "Verovatno prezentacija"
        elif not is_landscape:
            final_decision = "Verovatno tekstualni dokument (portrait)"
        
        doc.close()
        return final_decision
    
    except Exception as e:
        print(f"Došlo je do greške: {e}")


def main_chack_pdf(pdf_file: str) -> str:
    """
    Glavna funkcija koja proverava PDF fajl i vraća njegov tip.
    """
    # Prvo proveravamo poreklo PDF-a
    poreklo = proveri_poreklo_pdf(pdf_file)
    
    if poreklo == "PowerPoint":
        return "PowerPoint"
    
    # Ako nije PowerPoint, proveravamo strukturu
    struktura = debug_analiziraj_strukturu(pdf_file)
    
    if struktura == "Verovatno prezentacija":
        return "PowerPoint"
    
    return "Word" if poreklo == "Word" else "Unknown"