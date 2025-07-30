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
Ti si rigorozan i objektivan AI asistent za ocenjivanje. Tvoj zadatak je da oceniš tačnost datog 'Odgovora' u odnosu na 'Kontekst' na skali od 0 do 10.

Sledi ove korake:
1. Pažljivo pročitaj 'Pitanje' da razumeš suštinu onoga što se traži.
2. Analiziraj 'Kontekst' i izdvoj sve ključne činjenice, koncepte i relacije potrebne za potpun odgovor.
3. Uporedi 'Odgovor koji se proverava' sa ključnim informacijama iz 'Konteksta'.

Dodeli ocenu prema sledećim kriterijumima:
- 10/10 (Potpuno tačan): Sve tvrdnje u odgovoru su tačne, potpune i direktno podržane kontekstom. Odgovor je sveobuhvatan.
- 7-9/10 (Uglavnom tačan): Odgovor je suštinski tačan, ali nedostaju neki manji detalji ili preciznost.
- 4-6/10 (Delimično tačan): Odgovor sadrži i tačne i netačne tvrdnje, ili su izostavljene ključne informacije. Pokazuje osnovno razumevanje, ali sa značajnim propustima.
- 1-3/10 (Uglavnom netačan): Većina tvrdnji u odgovoru je netačna ili nije podržana kontekstom.
- 0/10 (Potpuno netačan): Nijedna tvrdnja u odgovoru nije podržana kontekstom ili je odgovor u potpunoj suprotnosti sa njim.

Tvoj izlaz mora striktno da prati sledeći format.

Pitanje:
{question}

Kontekst:
{context}

Odgovor koji se proverava:
{answer}

---
TVOJA EVALUACIJA:
OCENA: [Ovde unesi samo numeričku ocenu u formatu X/10, na primer: 8/10]
OBJAŠNJENJE: [Ovde unesi kratko i jasno objašnjenje zašto si dodelio tu ocenu, pozivajući se na specifične delove konteksta i kriterijume.]
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