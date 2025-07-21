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
answer_verification_template = """
Ti si precizan i nepristrasan AI evaluator. Tvoj jedini zadatak je da proceniš da li je dati 'Odgovor' tačan i u potpunosti podržan informacijama iz priloženog 'Konteksta'.

Sledi ove korake:
1. Pažljivo pročitaj 'Pitanje' da razumeš šta se traži.
2. Pažljivo pročitaj 'Kontekst' da identifikuješ relevantne činjenice.
3. Uporedi svaku tvrdnju iz 'Odgovora' sa činjenicama iz 'Konteksta'.

Nakon analize, donesi konačnu ocenu koristeći jednu od sledećih kategorija:
- TAČAN: Sve tvrdnje u odgovoru su direktno podržane kontekstom.
- DELIMIČNO TAČAN: Neke tvrdnje u odgovoru su tačne i podržane kontekstom, ali neke nisu ili su izostavljene važne informacije.
- NETAČAN: Tvrdnje u odgovoru su u suprotnosti sa kontekstom ili nisu uopšte spomenute u njemu.

Tvoj izlaz mora striktno da prati sledeći format, sa objašnjenjem za tvoju odluku.

Pitanje:
{question}

Kontekst:
{context}

Odgovor koji se proverava:
{answer}

---
TVOJA EVALUACIJA:
OCENA: [Ovde unesi jednu od tri kategorije: TAČAN, DELIMIČNO TAČAN, NETAČAN]
OBJAŠNJENJE: [Ovde unesi kratko i jasno objašnjenje zašto si doneo takvu ocenu, pozivajući se na specifične delove konteksta.]
"""

PROMPT_PROVERA_TACNOSTI = PromptTemplate(
    template=answer_verification_template, input_variables=["question", "context", "answer"]
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