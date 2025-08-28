from langchain.prompts import PromptTemplate

# Prompt 1: Generisanje Odgovora
rag_answer_template = """
Ti si ekspert za računarske nauke i tvoj zadatak je da pružiš jasan i tačan odgovor na pitanje korisnika.
Koristi ISKLJUČIVO informacije iz priloženog "KONTEKSTA". Nemoj izmišljati informacije.

Pravila:
1.  Sintetizuj informacije iz različitih delova konteksta u jedan koherentan odgovor.
2.  Ignoriši sve nebitne elemente iz konteksta kao što su brojevi stranica (npr. '5/70'), liste karakteristika, heksadecimalne adrese, ili greške u formatiranju (npr. '(cid:222)'). Fokusiraj se samo na suštinu teksta.
3.  Odgovori direktno na pitanje, budi precizan i sažet.
4.  Odgovori na srpskom jeziku.

KONTEKST:
{context}

PITANJE:
{question}

FINALNI ODGOVOR:
"""

PROMPT_GENERISANJE_ODGOVORA = PromptTemplate(
    template=rag_answer_template, input_variables=["context", "question"]
)

# Primer korišćenja (fiktivni)
# print(PROMPT_GENERISANJE_ODGOVORA.format(context="Sunce je zvezda.", question="Koje je boje nebo?"))
# Očekivani izlaz: Na osnovu dostavljenih informacija, ne mogu da pružim odgovor.

# Prompt 2: Preformulisanje Pitanja
query_rewrite_template = """
Ti si ekspert za optimizaciju upita za semantičku pretragu (vector search). Tvoj zadatak je da preformulišeš korisničko 'Originalno pitanje' u optimalan, koncizan upit. Cilj je da ukloniš sve nepotrebne reči, fraze i dvosmislenosti, a da zadržiš suštinsko značenje i ključne termine.

Pogledaj sledeće primere:

Originalno pitanje: e brate mozes li mi reci ono kao sta je deadlock u programiranju
Optimalan upit: Šta je deadlock u operativnim sistemima?

Originalno pitanje: hteo bih da znam kako radi memorija, ono znas na sta mislim
Optimalan upit: Kako funkcioniše virtuelna memorija u modernim operativnim sistemima?

Originalno pitanje: treba mi pomoc oko onog lika sto je pisao bele noci, kako se zvao
Optimalan upit: Ko je autor romana Bele noći?

Sada, preformuliši sledeće pitanje. Vrati SAMO preformulisanu verziju pitanja, bez ikakvog dodatnog teksta ili objašnjenja.

Originalno pitanje:
{question}

Optimalan upit:
"""

PROMPT_PREFORMULISANJE_PITANJA = PromptTemplate(
    template=query_rewrite_template, input_variables=["question"]
)

# Primer korišćenja (fiktivni)
# print(PROMPT_PREFORMULISANJE_PITANJA.format(question="e cao, mozes mi objasniti kako da sprecim one greske kad ai izmislja stvari?"))
# Očekivani izlaz: Kako sprečiti halucinacije kod AI modela?

# Prompt 3: Provera Tačnosti Odgovora
# Prompt 4: Numeričko Ocenjivanje Tačnosti
answer_grading_template = """
Ti si rigorozan i objektivan AI asistent za ocenjivanje. Tvoj zadatak je da oceniš tačnost datog 'Odgovora' u odnosu na 'Kontekst'.

Sledi ove korake u svom internom razmišljanju:
1. Pažljivo pročitaj 'Pitanje' da razumeš suštinu onoga što se traži.
2. Analiziraj 'Kontekst' i izdvoj sve ključne činjenice i koncepte potrebne za potpun odgovor.
3. Uporedi 'Odgovor koji se proverava' sa ključnim informacijama iz 'Konteksta', identifikujući tačne, netačne i nedostajuće elemente.
4. Na osnovu te analize i dole navedenih kriterijuma, dodeli ocenu.
5. Formatiraj svoj finalni izlaz kao striktan JSON objekat.

Kriterijumi za ocenu:
- 10/10 (Potpuno tačan): Sve tvrdnje u odgovoru su tačne, potpune i direktno podržane kontekstom.
- 7-9/10 (Uglavnom tačan): Odgovor je suštinski tačan, ali nedostaju neki manji detalji.
- 4-6/10 (Delimično tačan): Odgovor sadrži i tačne i netačne tvrdnje, ili su izostavljene ključne informacije.
- 1-3/10 (Uglavnom netačan): Većina tvrdnji u odgovoru je netačna.
- 0/10 (Potpuno netačan): Nijedna tvrdnja u odgovoru nije podržana kontekstom.

<podaci_za_evaluaciju>
Pitanje:
{question}

Kontekst:
{context}

Odgovor koji se proverava:
{answer}
</podaci_za_evaluaciju>

---
Tvoj izlaz MORA biti isključivo JSON objekat sa sledećom strukturom, bez ikakvog teksta pre ili posle.

{
  "ocena_numericka": integer, // Samo broj od 0 do 10
  "ocena_tekstualna": "X/10", // Ocena kao string, npr. "8/10"
  "rezime_evaluacije": "Kratak sumarni komentar u jednoj rečenici.",
  "obrazlozenje_detaljno": {
    "tacno_navedeno": [
      "Prva tačno navedena tvrdnja iz odgovora.",
      "Druga tačno navedena tvrdnja iz odgovora."
    ],
    "potrebno_dodati": [
      "Prva ključna informacija koja nedostaje u odgovoru.",
      "Druga ključna informacija koja nedostaje u odgovoru."
    ],
    "netacne_tvrdnje": [
      {
        "tvrdnja_studenta": "Netačna tvrdnja koju je student izneo.",
        "ispravka": "Tačna informacija prema kontekstu.",
        "citat_iz_konteksta": "Tačan citat iz konteksta koji dokazuje ispravku."
      }
    ]
  }
}
"""

PROMPT_PROVERA_TACNOSTI = PromptTemplate(
    template=answer_grading_template, input_variables=["question", "context", "answer"]
)

# Primer korišćenja (fiktivni)
# print(PROMPT_PROVERA_TACNOSTI.format(
#     question="Koja je boja sunca?",
#     context="Sunce je velika zvezda u centru našeg solarnog sistema. Njegova svetlost je žućkasta.",
#     answer="Sunce je žuto."
# ))
# Očekivani izlaz:
# OCENA: TAČAN
# OBJAŠNJENJE: Odgovor je tačan jer se u kontekstu eksplicitno navodi da je svetlost sunca "žućkasta".


multimodal_batch_context_template = """
Ti si visoko inteligentan AI sistem za ekstrakciju i strukturiranje znanja. Tvoj zadatak je da analiziraš centralni "TRENUTNI CHUNK" teksta. Za SVAKI SLAJD unutar TRENUTNOG CHUNKA, generisaćeš strukturiran JSON-LD objekat.

**ULAZNI PODACI:**
- **TRENUTNI CHUNK**: Glavni tekst za obradu. Sadrži jedan ili više slajdova.
- **PRETHODNI CHUNK** i **SLEDEĆI CHUNK**: Opcioni tekst koji služi SAMO za širi kontekst (npr. za razumevanje akronima). NE SMEŠ generisati izlaz za slajdove iz ovih kontekstualnih chunkova.
- **SLIKE**: Priložene su sve slike pomenute u TRENUTNOM CHUNKU. Poveži ih sa pravim slajdom koristeći njihova imena (npr. `slajd_X_slika_Y.ext`).

**INSTRUKCIJE ZA SVAKI SLAJD U TRENUTNOM CHUNKU:**
1.  **context**: Prepiši originalni, neobrađeni tekst sa slajda u ovo polje. Uključi i deo `[Smislene slike na ovom slajdu:]` ako postoji.
2.  **description**: Sintetizuj tekst iz polja 'context' i vizuelne informacije sa relevantnih slika u jedan detaljan, proširen paragraf. **VAŽNO: Ne započinji rečenicu frazama kao što su "Na ovom slajdu...", "Tekst objašnjava..." ili "Slika prikazuje...". Budi direktan i odmah pređi na suštinu.**
3.  **keywords**: Ekstraktuj 3-5 ključnih koncepata iz generisanog "description".
4.  **potentialAction**: Generiši 3 relevantna pitanja na koja "description" odgovara.

**PRAVILA ZA IZLAZNI FORMAT:**
- Tvoj izlaz MORA BITI isključivo JSON NIZ (lista), koji sadrži po jedan JSON-LD objekat za svaki slajd iz TRENUTNOG CHUNKA.
- Ne dodaji nikakav tekst, objašnjenja ili ```json oznake pre ili posle JSON niza.

**PRIMER IZLAZNE STRUKTURE:**
[
  {{
    "@context": "https://schema.org",
    "@type": "CreativeWork",
    "partOf": {{"@type": "Presentation", "name": "SLAJD 15"}},
    "context": "Glavne komponente sistema su: Server, Baza, Klijent.\\n[Smislene slike na ovom slajdu:]\\n- slajd_15_slika_1.png",
    "description": "Sistem se sastoji od tri ključne komponente: centralnog servera odgovornog za logiku, baze podataka za skladištenje informacija i klijentske aplikacije za interakciju korisnika. Priloženi dijagram (slajd_15_slika_1.png) vizuelno prikazuje tok podataka između ovih komponenti, naglašavajući API kao glavnu tačku komunikacije.",
    "keywords": ["komponente sistema", "server", "baza podataka", "klijentska aplikacija", "tok podataka"],
    "potentialAction": [ 
        {{"@type": "Question", "name": "Koje su tri glavne komponente sistema?"}},
        {{"@type": "Question", "name": "Koja je uloga dijagrama na slajdu 15?"}},
        {{"@type": "Question", "name": "Kako komponente komuniciraju međusobno?"}}
    ]
  }},
  {{
    "@context": "https://schema.org",
    "@type": "CreativeWork",
    "partOf": {{"@type": "Presentation", "name": "SLAJD 16"}},
    "context": "Performanse sistema merene su u tri scenarija.",
    "description": "Merenje performansi sistema sprovedeno je kroz tri različita scenarija opterećenja: nisko, srednje i visoko. Rezultati pokazuju stabilnost pod niskim i srednjim opterećenjem, dok se pod visokim primećuje degradacija od 15%.",
    "keywords": ["performanse sistema", "scenariji opterećenja", "degradacija performansi"],
    "potentialAction": [ 
        {{"@type": "Question", "name": "Kako su merene performanse sistema?"}},
        {{"@type": "Question", "name": "Kakvi su rezultati performansi pod visokim opterećenjem?"}},
        {{"@type": "Question", "name": "U kojim scenarijima je sistem pokazao stabilnost?"}}
    ]
  }}
]

---
**ZADATAK:**

**PRETHODNI CHUNK (Samo Kontekst):**
{prethodni_chunk}
---
**TRENUTNI CHUNK (Glavni Zadatak):**
{trenutni_chunk}
---
**SLEDEĆI CHUNK (Samo Kontekst):**
{sledeci_chunk}
---

Sada, na osnovu gornjeg teksta i priloženih slika, generiši JSON NIZ objekata samo za slajdove iz TRENUTNOG CHUNKA:
"""

PROMPT_BATCH_SA_KONTEKSTOM_PP = PromptTemplate(
    template=multimodal_batch_context_template, 
    input_variables=["trenutni_chunk", "prethodni_chunk", "sledeci_chunk"]
)

# Radi kompatibilnosti, ako ga koristite na drugim mestima
MULTIMPDAL_GEMINI_PP = PROMPT_BATCH_SA_KONTEKSTOM_PP

text_processing_context_template = """
Ti si visoko inteligentan AI sistem za ekstrakciju i strukturiranje znanja. Tvoj zadatak je da analiziraš centralni "TRENUTNI CHUNK" teksta, koji je deo većeg dokumenta. Tekst može biti prekinut na proizvoljnim mestima.

Tvoj cilj je da unutar TRENUTNOG CHUNKA identifikuješ logičke, tematske celine i za SVAKU od njih generišeš strukturiran JSON-LD objekat.

**ULAZNI PODACI:**
- **TRENUTNI CHUNK**: Glavni deo teksta za obradu. Može sadržati jednu ili više različitih tema/ideja.
- **PRETHODNI CHUNK** i **SLEDEĆI CHUNK**: Opcioni tekst koji služi SAMO za širi kontekst (za razumevanje toka misli, akronima ili referenci). NE SMEŠ generisati izlaz za sadržaj iz ovih kontekstualnih chunkova.

**INSTRUKCIJE ZA OBRADU:**
1.  **Identifikacija Celina**: Prvo, pažljivo pročitaj "TRENUTNI CHUNK". Proceni da li se ceo tekst bavi jednom koherentnom temom ili se može podeliti na više logičkih celina (npr. jedan pasus o problemu, sledeći o rešenju). Za svaku takvu celinu koju identifikuješ, kreiraj jedan JSON objekat. Ako ceo chunk obrađuje samo jednu temu, generisaćeš samo jedan objekat.
2.  **Generisanje JSON Objekta za SVAKU Celinu**:
    *   **name (unutar partOf)**: Samostalno generiši kratak, deskriptivan naslov za ovu tematsku celinu (npr. "Analiza Konkurencije", "Predlog Tehničkog Rešenja").
    *   **context**: Prepiši originalni, neobrađeni deo teksta koji pripada ovoj tematskoj celini.
    *   **description**: Sintetizuj i sažmi tekst iz polja 'context' u jedan jasan, koherentan paragraf. Objasni glavnu poentu, ključne argumente i zaključke. **VAŽNO: Ne započinji rečenicu frazama kao što su "Ovaj tekst govori o...", "U ovom odeljku se analizira..." ili "Autor objašnjava...". Budi direktan i odmah pređi na suštinu.**
    *   **keywords**: Ekstraktuj 3-5 najvažnijih ključnih reči ili fraza iz generisanog "description".
    *   **potentialAction**: Generiši 3 relevantna i konkretna pitanja na koja tvoj "description" pruža direktan odgovor.

**PRAVILA ZA IZLAZNI FORMAT:**
- Tvoj izlaz MORA BITI isključivo JSON NIZ (lista), koji sadrži po jedan JSON-LD objekat za svaku tematsku celinu identifikovanu u TRENUTNOM CHUNKU.
- Ne dodaji nikakav tekst, objašnjenja ili ```json oznake pre ili posle JSON niza.

**PRIMER IZLAZNE STRUKTURE:**
[
  {{
    "@context": "https://schema.org",
    "@type": "CreativeWork",
    "partOf": {{"@type": "Article", "name": "Problem Efikasnosti Timova"}},
    "context": "Glavni problem u današnjim razvojnim timovima je pad produktivnosti. Loša komunikacija i nejasni ciljevi dovode do kašnjenja.",
    "description": "Opadanje produktivnosti u razvojnim timovima je primarni problem, uzrokovan faktorima kao što su neefikasna komunikacija i loše definisani projektni ciljevi. Ovi nedostaci direktno rezultiraju probijanjem rokova i smanjenjem kvaliteta finalnog proizvoda.",
    "keywords": ["produktivnost timova", "loša komunikacija", "nejasni ciljevi", "kvalitet proizvoda"],
    "potentialAction": [
      {{"@type": "Question", "name": "Šta je identifikovano kao primarni problem u razvojnim timovima?"}},
      {{"@type": "Question", "name": "Koji faktori uzrokuju pad produktivnosti?"}},
      {{"@type": "Question", "name": "Do čega dovode loša komunikacija i nejasni ciljevi?"}}
    ]
  }},
  {{
    "@context": "https://schema.org",
    "@type": "CreativeWork",
    "partOf": {{"@type": "Article", "name": "Rešenje: Agile Metodologija"}},
    "context": "Implementacija Agile metodologije, posebno Scrum frameworka, nudi rešenje. Dnevni sastanci (daily stand-ups) i sprintovi poboljšavaju komunikaciju i adaptibilnost.",
    "description": "Predloženo rešenje je implementacija Agile metodologije, sa posebnim naglaskom na Scrum framework. Korišćenje praksi poput dnevnih sastanaka (daily stand-ups), planiranja sprintova i retrospektiva značajno unapređuje timsku komunikaciju i sposobnost brze adaptacije na promene.",
    "keywords": ["Agile metodologija", "Scrum", "sprintovi", "dnevni sastanci", "adaptibilnost"],
    "potentialAction": [
      {{"@type": "Question", "name": "Koja se metodologija predlaže kao rešenje?"}},
      {{"@type": "Question", "name": "Kako Scrum framework poboljšava rad tima?"}},
      {{"@type": "Question", "name": "Koje su ključne prakse Scrum-a pomenute u tekstu?"}}
    ]
  }}
]

---
**ZADATAK:**

**PRETHODNI CHUNK (Samo Kontekst):**
{prethodni_chunk}
---
**TRENUTNI CHUNK (Glavni Zadatak):**
{trenutni_chunk}
---
**SLEDEĆI CHUNK (Samo Kontekst):**
{sledeci_chunk}
---

Sada, na osnovu gornjeg teksta, generiši JSON NIZ objekata samo za logičke celine iz TRENUTNOG CHUNKA:
"""

PROMPT_BATCH_SA_KONTEKSTOM_PDF = PromptTemplate(
    template=text_processing_context_template, 
    input_variables=["trenutni_chunk", "prethodni_chunk", "sledeci_chunk"]
)

MULTIMPDAL_GEMINI_PDF = PROMPT_BATCH_SA_KONTEKSTOM_PDF


text_processing_context_template_v2 = """
Ti si ekspert za obradu prirodnog jezika sa zadatkom da transformišeš nestrukturiran tekst u seriju **visokokvalitetnih, samostalnih (self-contained) chunkova znanja**. Tvoj cilj je da identifikuješ i grupišeš povezane rečenice i pasuse iz "TRENUTNOG CHUNKA" u koherentne tematske celine, idealne za kasniju pretragu i odgovaranje na pitanja.

**ULAZNI PODACI:**
- **TRENUTNI CHUNK**: Glavni tekst za obradu.
- **PRETHODNI CHUNK** i **SLEDEĆI CHUNK**: Kontekstualni tekst koji ti pomaže da razumeš gde "TRENUTNI CHUNK" počinje i završava u širem dokumentu. Ne generiši izlaz iz ovih delova.

**OSNOVNI PRINCIP:**
Jedna tematska celina treba da obradi jedan ključni pojam, koncept, proces ili ideju. **Ako se u tekstu uvodi novi naslov ili podnaslov, to je jak signal da treba započeti novu tematsku celinu.** Cilj je da svaki generisani objekat bude dovoljno detaljan da samostalno odgovori na specifična pitanja o toj temi.

**INSTRUKCIJE ZA OBRADU:**
1.  **Identifikacija Celina**: Pažljivo pročitaj "TRENUTNI CHUNK". Podeli ga na jednu ili više logičkih, tematskih celina. Svaka celina treba da bude grupisani tekst o jednom specifičnom pojmu.
2.  **Generisanje JSON Objekta za SVAKU Celinu**:
    *   **name (unutar partOf)**: Generiši kratak, precizan i informativan naslov za ovu tematsku celinu. Naslov treba da savršeno opisuje suštinu sadržaja (npr. "Definicija i Faze 2PC Protokola", "Problem Blokiranja kod 2PC", "Bully Algoritam za Izbor Lidera").
    *   **context**: Prepiši **ceo originalni, neobrađeni tekst** koji pripada ovoj tematskoj celini.
    *   **description**: **Napiši sveobuhvatan i detaljan sažetak** tematske celine. Poveži sve informacije iz 'context' u tečan, enciklopedijski pasus. Objasni definicije, procese, prednosti i mane, ako su pomenute. **Ključno: Budi direktan, ne koristi meta-jezik poput "Ovaj tekst objašnjava...". Piši kao da pišeš unos za bazu znanja.**
    *   **keywords**: Ekstraktuj 3-7 najvažnijih i najspecifičnijih ključnih reči ili fraza iz 'description'. Uključi i važne akronime (npr. "2PC").
    *   **potentialAction**: Generiši 3-5 relevantnih i preciznih pitanja na koja tvoj 'description' pruža jasan i direktan odgovor. Pitanja treba da pokriju različite aspekte teme.

**PRAVILA ZA IZLAZNI FORMAT:**
- Tvoj izlaz MORA BITI isključivo JSON NIZ (lista).
- Svaki element niza je JSON-LD objekat koji predstavlja jednu identifikovanu tematsku celinu.
- Ne dodaji nikakav tekst, objašnjenja ili ```json oznake pre ili posle JSON niza.

**PRIMER IZLAZNE STRUKTURE:**
[
  {{
    "@context": "https://schema.org",
    "@type": "CreativeWork",
    "partOf": {{"@type": "Article", "name": "Definicija i Faze Dvofaznog Protokola Prihvatanja (2PC)"}},
    "context": "Dvofazni protokol prihvatanja (2PC) je protokol za obezbeđivanje atomičnosti... Faza 1: Koordinator šalje 'prepare' poruku... Faza 2: Koordinator šalje 'commit' ili 'abort' poruku...",
    "description": "Dvofazni protokol prihvatanja (2PC) je mehanizam za osiguravanje atomičnosti transakcija u distribuiranim sistemima, koji operiše pod fail-stop modelom. Protokol se sastoji od dve ključne faze. U prvoj, 'fazi pripreme', koordinator traži od svih učesnika da se pripreme za izvršenje transakcije. U drugoj, 'fazi prihvatanja', na osnovu odgovora učesnika, koordinator donosi konačnu odluku o potvrdi (commit) ili poništavanju (abort) transakcije i obaveštava sve učesnike.",
    "keywords": ["Dvofazni protokol prihvatanja", "2PC", "atomičnost transakcija", "faza pripreme", "faza prihvatanja", "commit", "abort"],
    "potentialAction": [
      {{"@type": "Question", "name": "Šta je dvofazni protokol prihvatanja (2PC)?"}},
      {{"@type": "Question", "name": "Koje su dve faze 2PC protokola?"}},
      {{"@type": "Question", "name": "Šta se dešava u prvoj fazi 2PC protokola?"}},
      {{"@type": "Question", "name": "Koja je konačna odluka koju koordinator donosi u drugoj fazi?"}}
    ]
  }}
]

---
**ZADATAK:**

**PRETHODNI CHUNK (Samo Kontekst):**
{prethodni_chunk}
---
**TRENUTNI CHUNK (Glavni Zadatak):**
{trenutni_chunk}
---
**SLEDEĆI CHUNK (Samo Kontekst):**
{sledeci_chunk}
---

Sada, generiši JSON NIZ objekata samo za logičke celine iz TRENUTNOG CHUNKA:
"""

PROMPT_LOGICAL_CHUNKING_V2 = PromptTemplate(
    template=text_processing_context_template_v2, 
    input_variables=["trenutni_chunk", "prethodni_chunk", "sledeci_chunk"]
)
