# Automatická registrace na LOS závod

Vylepšený skript, který automaticky provádí registraci na závod LOS Lex pomocí knihovny Playwright. Nevyžaduje žádné zadávání údajů v konzoli – vše si načítá z konfiguračního souboru `data.py`.

## Součástí je:
### Časovaná registrace (main.py)
- Automatické přihlášení do systému
- Odeslání potvrzovacího e-mailu s .ics událostí
- Notifikace přítelkyni ❤️
- Logování do souboru
- Automatické opakování registrace při selhání (max. 25 pokusů - lze změnit v proměnné "LIMIT" v main.py)
- Pokud zvolená divize nebyla v závodě otevřena, skript automaticky zvolí první možnou. Závodník tak nepřijde o místo a následně registraci může upravit.
- Pokud je zvolený squad plný, skript automaticky zkusí zvolit první volný squad v rozsahu 1 - 100.
- Ošetření většiny možných chyb od neodpovídajícího serveru po selhání emailového serveru - skript je možno nechat běžet bez dohledu a neselže.
### Registrace na plný závod (plny_zavod.py)
- Pokud závodník prosral začátek registrace a závod je plný, lze spustit soubor plny_zavod.py, který každých 30 minut kontroluje obsazenost a v případě volného místa spouští registrační skript <code>main.py</code>.
### Analýza konkurence (konkurence.py)
- Pokud si závodník chce vyjet konkurenci a zhodnotit svoje šance na úspěch, lze spustit skript konkurence.py.
- Skript vytváří a rovnou otevírá .html přehled závodníků, kteří jsou na zvolený závod registrováni ve stejné divizi.
- - Tito jsou seřazeni dle jejich průměrné procentuální úspěšnosti v poháru (Celkový součet procentních výsledků VŠECH závodů děleno počet těchto závodů - skript bere v potaz i závody, které se závodníkovi do poháru nepočítají, neboť jsou přes limit počítaných závodů).
- Závodník je vyznačen oranžově, konkurenční závodník, který je na prvním místě poháru, je vyznačen červeně.
- Data si skript bere vždy z aktuálního poháru a vypisuje ještě 2 předešlé poháry.
- Výstupem je .html přehled. Vzor je v souboru konkurence_sample.html.


## 📦 Požadavky

- Python 3.12.6
- playwright
- Běžící Proton Bridge nebo Gmail účet se specifickým Google App Password (lze nastavit [zde](https://myaccount.google.com/apppasswords)) 
- Konfigurační soubor `data.py` s následujícím obsahem:

```python
JMENO = "Jan Novák"
# Celé jméno závodníka
CISLO_DOKLADU = "AL123456"
# Číslo ZP
CLENSKE_ID = "ABcdEfGh"
# LEX ID (volitelné - pokud nemáš, napiš None)
# CLENSKE_ID = None
DIVIZE = "Pistole"
# Název divize přesně dle výběru na webu (v drop down menu u registrace)
# DIVIZE = "Optik/Pistole"
URL = "https://www.loslex.cz/contest/292"
# URL konkrétního závodu
LOGIN = "jan.novak"
# Email pro přihlášení i notifikace
HESLO = "tajneheslo123"
# Heslo do systému LOS Lex
DATUM_CAS_REGISTRACE = "2025-06-15 20:00:00"
# Datum otevření registrace. Formát musí být RRRR-MM-DD HH:MM:SS
SQUAD = 1
# Číslo squadu, nebo r (v uvozovkách pro squad ROZHODČÍ)
EMAIL_P = "tajneheslo123"
# Proton Bridge nebo Gmail heslo pro SMTP
EMAIL_U = "jan.novak@pm.me"
# Proton Bridge nebo Gmail username odesílatele
MZ = False
# Mimo závod
ZACATECNIK = False
# Začátečník
STAVITEL = False
# Stavitel
ROZHODCI = False
# Rozhodčí
POZNAMKA = "..."
# Poznámka (volitelné) - Může být None
# POZNAMKA = None
PRITELKYNE = "jana.novakova@pm.me"
# Email přítelkyně (None, pokud jsi single)
# PRITELKYNE = None
JMENO_PRITELKYNE = "Jana"
# Křestní jméno přítelkyně v prvním pádu
# Pokud je přítelkyně None, nepoužívá se
RANDOM_WAIT = False
# Zda má skript před odesláním registrace čekat náhodný počet sekund mezi 2 a 3, aby registrace vypadala věrohodněji
INTERVAL = 1800
# V jakém intervalu v sekundách se má kontrolovat volné místo na plném závodě (s tímto údajem se pracuje pouze v plny_zavod.py)
EMAIL_PROVIDER = "PROTON"
# Poskytovatel emailových služeb. Možnosti jsou buď "PROTON" (S nainstalovaným Proton Bridge) nebo "GMAIL" (S specifickým Google apps password)
```

## ▶️ Spuštění

### Prvotní instalace před spuštěním:

Před tímto krokem je nutné mít nainstalovaný [Python](https://www.python.org/downloads/) a [Git](https://git-scm.com/install/).<br>
Spusť v příkazovém řádku následující příkazy, nebo si stáhni a spusť <code>install.bat</code>.<br>
Registrátor se ti nainstaluje do <code>C:\Users\TVUJ_USERNAME\AppData\Roaming</code>
```bash
cd %appdata%
git clone https://github.com/joudar11/registrator_zavodu_2
cd ./registrator_zavodu_2
python -m venv .venv
set VIRTUAL_ENV_DISABLE_PROMPT=
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt
playwright install
if exist data_sample.py ren data_sample.py data.py
```
### 🏁 Použití po instalaci:
#### Vytvoření konfigurace:
Přejmenuj soubor <code>data_sample.py</code> na <code>data.py</code> (toto automaticky dělá instalační skript <code>install.bat</code>) a vyplň ho.
#### Pokud registrace ještě nezačala:
spustit soubor <code>run.bat</code> (doporučeno)<br>
nebo (pokud nepracuješ v okně, kde jsi prováděl instalaci):
```bash
.venv\Scripts\Activate.ps1
python main.py
```
Pokud pracuješ v okně, kde jsi prováděl instalaci, stačí:
```bash
python main.py
```
#### Pokud registrace běží, ale závod je plný:
spustit soubor <code>plny_zavod.bat</code> (doporučeno)<br>
nebo (pokud nepracuješ v okně, kde jsi prováděl instalaci):
```bash
.venv\Scripts\Activate.ps1
python plny_zavod.py
```
Pokud pracuješ v okně, kde jsi prováděl instalaci, stačí:
```bash
python plny_zavod.py
```
#### Pokud závod ještě nebyl vyhlášen, registrace už je spuštěna a závodník chce analýzu konkurence:
spustit soubor <code>konkurence.bat</code> (doporučeno)<br>
nebo (pokud nepracuješ v okně, kde jsi prováděl instalaci):
```bash
.venv\Scripts\Activate.ps1
python konkurence.py
```
Pokud pracuješ v okně, kde jsi prováděl instalaci, stačí:
```bash
python konkurence.py
```
Je možné spustit s argumenty JMÉNO DIVIZE URL pro přepsání dat o závodě a závodníkovi v souboru <code>data.py</code>. I zde je však potřeba mít vyplněný soubor data.py, aby se skript mohl na webu LOSu přihlásit a zobrazit si celá jména.<br>
např:
```bash
python konkurence.py "Jan Novák" "Pistole" "https://www.loslex.cz/contest/313"
```
(Tato funkcionalita podporuje divize Pi, Opt a PDW. Ostatní divize autor jakožto zbytečné neuznává, proto jejich podpora nebude implementována.)

### Aktualizace na poslední verzi
```bash
git fetch --all
git reset --hard HEAD
git pull
```
nebo spuštěním souboru <code>update.bat</code>
