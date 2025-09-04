# POKRETANJE APLIKACIJE

Ovaj dokument sadrži uputstva za postavljanje i pokretanje svih komponenti projekta. Projekat se sastoji iz tri glavna dela:
1.  **Moodle Plugin (`aigrader`)**: Plugin za Moodle koji se integriše u sistem pitanja.
2.  **Skripta za punjenje baze (`database_filler`)**: Skripta za popunjavanje baze podataka sa početnim podacima.
3.  **AI Backend (`ai_backend`)**: API servis koji pruža AI funkcionalnosti.

Molimo vas da pratite korake redom za uspešnu instalaciju.

---

## 1. Moodle Plugin (`aigrader`)

Ovaj deo se odnosi na instalaciju prilagođenog Moodle plugina za ocenjivanje pomoću veštačke inteligencije.

### Preduslovi
*   Instaliran i konfigurisan **XAMPP** (ili drugi web server sa Apache, PHP i MariaDB/MySQL).
*   Funkcionalna **Moodle** instalacija.

### Instalacija
1.  **Kopiranje fajlova**:
    *   Kompletan folder `aigrader` iskopirajte u direktorijum za Moodle plugine tipa "pitanje" (question type). Putanja je obično:
        ```
        <putanja_do_moodle_foldera>/question/type/
        ```
    *   Nakon kopiranja, struktura bi trebalo da izgleda ovako: `<moodle_folder>/question/type/aigrader`.

2.  **Instalacija unutar Moodle-a**:
    *   Ulogujte se na vaš Moodle sajt kao **administrator**.
    *   Idite na **Site administration** > **Notifications**.
    *   Moodle će automatski detektovati novi plugin i pokrenuti proces instalacije (upgrade baze podataka).
    *   Pratite uputstva na ekranu i potvrdite instalaciju.

Nakon ovoga, "AI Grader" tip pitanja će biti dostupan prilikom kreiranja novih pitanja u kvizovima.

---

## 2. Skripta za punjenje baze (`database_filler`)

Ova skripta služi za popunjavanje baze podataka pitanjima i drugim podacima iz lokalnih fajlova.

### Priprema podataka
1.  Unutar `database_filler` foldera, uverite se da postoji folder po imenu `podaci`.
2.  Unutar foldera `podaci` možete kreirati podfoldere koji se zovu po predmetima (npr. `matematika`, `istorija`, `programiranje`).
3.  U te podfoldere stavite fajlove (.txt, .docx, itd.) iz kojih skripta treba da izvuče podatke.

### Instalacija i pokretanje
1.  **Otvorite terminal** (PowerShell, Command Prompt, itd.) i pozicionirajte se u `database_filler` folder:
    ```powershell
    cd putanja\do\projekta\database_filler
    ```

2.  **Kreirajte virtuelno okruženje** (ako već ne postoji):
    ```powershell
    python -m venv venv
    ```

3.  **Aktivirajte virtuelno okruženje**:
    *   Na Windowsu (PowerShell):
        ```powershell
        .\venv\Scripts\Activate.ps1
        ```
    *   Na Linux/macOS:
        ```bash
        source venv/bin/activate
        ```
    > **Napomena:** Ako na PowerShell-u dobijete grešku u vezi sa "Execution Policy", pokrenite `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process` pre aktivacije.

4.  **Instalirajte sve potrebne biblioteke**:
    ```powershell
    pip install -r requirements.txt
    ```

5.  **Pokrenite skriptu za popunjavanje baze**:
    ```powershell
    python start_population.py
    ```

6.  **Proverite bazu podataka** da biste se uverili da su podaci uspešno uneti.

---

## 3. AI Backend (`ai_backend`)

Ovo je FastAPI servis koji služi kao pozadina za AI operacije. Moodle plugin komunicira sa ovim servisom.

### Instalacija i konfiguracija
1.  **Otvorite novi terminal** i pozicionirajte se u `ai_backend` folder:
    ```powershell
    cd putanja\do\projekta\ai_backend
    ```

2.  **Kreirajte i aktivirajte virtuelno okruženje** (pratite korake 2 i 3 iz prethodnog odeljka).

3.  **Instalirajte sve potrebne biblioteke**:
    ```powershell
    pip install -r requirements.txt
    ```

4.  **Podesite API ključeve**:
    *   U `ai_backend` folderu, napravite novi fajl pod nazivom `.env`.
    *   Otvorite `.env` fajl i dodajte vaše API ključeve u sledećem formatu:
        ```ini
        OPENAI_API_KEY="sk-vas-openai-kljuc-ovde"
        GOOGLE_API_KEY="vas-google-gemini-kljuc-ovde"
        # Dodajte ostale potrebne varijable okruženja
        ```
    *   Sačuvajte i zatvorite fajl.

### Pokretanje servera
1.  Uverite se da vam je **aktivno virtuelno okruženje** za `ai_backend`.

2.  Pokrenite server pomoću `uvicorn`-a. Opcija `--reload` omogućava automatsko restartovanje servera prilikom svake izmene koda.
    ```powershell
    python -m uvicorn main:app --reload
    ```
3.  Ako je sve u redu, videćete poruku da server radi, obično na adresi `http://127.0.0.1:8000`.

Server je sada aktivan i spreman da prima zahteve od Moodle plugina.