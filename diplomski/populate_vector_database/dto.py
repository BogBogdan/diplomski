# dto.py

import json
import re
from typing import List, Dict, Any

def object_parser(json_string_od_ai: str) -> List[Dict[str, Any]]:
    """
    Čisti, parsira i transformiše JSON string od AI modela.
    Za svaki objekat, kreira rečnik sa ključevima 'embedding_text' i 'metadata'.
    'metadata' sadrži SAMO ključne reči.
    """
    if not isinstance(json_string_od_ai, str) or not json_string_od_ai.strip():
        return []

    try:
        # 1. Čišćenje i parsiranje
        cist_json_string = re.sub(r'^\s*```json\n|\n```\s*$', '', json_string_od_ai.strip())
        lista_objekata = json.loads(cist_json_string)
        
        if not isinstance(lista_objekata, list):
            return []
            
        finalna_lista = []
        
        for obj in lista_objekata:
            if not isinstance(obj, dict):
                continue

            # 1. Kreiramo tekst za embedding
            kontekst = obj.get('context', '')
            deskripcija = obj.get('description', '')
            pitanja_lista = [p.get('name', '') for p in obj.get('potentialAction', [])]
            pitanja_tekst = " ".join(pitanja_lista)
            
            spojeni_tekst = f"Deskripcija: {deskripcija}\n\nPitanja: {pitanja_tekst}\n\nOriginalni Sadržaj: {kontekst}"

            # 2. Kreiramo metapodatke - SAMO KEYWORDS
            meta = {
                "keywords": obj.get('keywords', [])
            }
            
            # 3. Pakujemo sve u jedan rečnik
            finalna_lista.append({
                "embedding_text": spojeni_tekst,
                "metadata": meta
            })
            
        return finalna_lista

    except Exception:
        return []