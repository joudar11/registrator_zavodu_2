# Automatická registrace na LOS závod

Vylepšený skript, který automaticky provádí registraci na závod LOS Lex pomocí knihovny Playwright. Nevyžaduje žádné zadávání údajů v konzoli – vše si načítá z konfiguračního souboru `data.py`.

## Součástí je:
- Automatická kontrola verze a pripadné spuštění aktualizace
### Časovaná registrace (main.py)
- Automatické přihlášení do systému
- Odeslání potvrzovacího e-mailu s .ics událostí
- Notifikace přítelkyni ❤️
- Logování do souboru
- Automatické opakování registrace při selhání (max. 25 pokusů - lze změnit v proměnné "LIMIT" v main.py)
- Pokud zvolená divize nebyla v závodě otevřena, skript automaticky zvolí první možnou. Závodník tak nepřijde o místo a následně registraci může upravit.
- Pokud je zvolený squad plný, skript automaticky zkusí zvolit první volný squad v rozsahu 1 - 100.
- Ošetření většiny možných chyb od neodpovídajícího serveru po selhání emailového serveru - skript je možno nechat běžet bez dohledu a neselže.
- Automatické načítání informací o stavu registrace, případně datu jejího spuštění.
- **Pozor - skript předpokládá, že závodník je držitelem zbrojního oprávnění a automaticky zaškrtává při registraci pole "Držitel zbrojního oprávnění"!**
### Registrace na plný závod (plny_zavod.py)
- Pokud závodník prosral začátek registrace a závod je plný, lze spustit soubor plny_zavod.py, který každých 30 minut kontroluje obsazenost a v případě volného místa spouští registrační skript <code>main.py</code>.
### Analýza konkurence (konkurence.py)
- Pokud si závodník chce vyjet konkurenci a zhodnotit svoje šance na úspěch, lze spustit skript konkurence.py.
- Skript vytváří a rovnou otevírá .html přehled závodníků, kteří jsou na zvolený závod registrováni ve stejné divizi.
- - Tito jsou seřazeni dle jejich průměrné procentuální úspěšnosti v poháru (Celkový součet procentních výsledků VŠECH závodů děleno počet těchto závodů - skript bere v potaz i závody, které se závodníkovi do poháru nepočítají, neboť jsou přes limit počítaných závodů).
- Závodník je vyznačen oranžově, konkurenční závodník, který je na prvním místě poháru, je vyznačen červeně.
- Data si skript bere vždy z aktuálního poháru a vypisuje ještě 2 předešlé poháry.
- Výstupem je .html přehled. Vzor je v souboru konkurence_sample.html.
- Pokud existuje soubor <code>ftp_konkurence.py</code>, skript automaticky nahraje přehled na FTP a otevře jeho umístění na webu.
### Kontrola zveřejněných výsledků (vysledky_zverejneny.py)
- Ideální ke spuštění na závodě při čekání na zveřejnění výsledků.
- Skript závodníka upozorní emailem, že byly zveřejněny výsledky.
- Kontrola každých 10 sekund.
### Stažení výsledků posledních 3 pohárů v CSV pro analýzu konkurence
- Stáhne všechny výslůedky v poháru pro datovou analýzu.


## 📦 Požadavky

- Python 3.12.6
- playwright
- Běžící Proton Bridge, nakonfigurovaný Proton token, nebo Gmail účet se specifickým Google App Password (lze nastavit [zde](https://myaccount.google.com/apppasswords)) 
- Konfigurační soubor <code>data.py</code> s následujícím obsahem:

```python
JMENO = "Jan Novák"
# Celé jméno závodníka
CISLO_DOKLADU = "123456789"
# Číslo OP/EZP
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
# Poskytovatel emailových služeb. Možnosti jsou buď "PROTON" (S nainstalovaným Proton Bridge), "PROTON-TOKEN" (S nakonfigurovaným tokenem pro Proton mail), nebo "GMAIL" (S specifickým Google apps password)
```

- Volitelně konfigurační soubor <code>ftp_konkurence.py</code> k nahrání souborů na FTP:

```python
host=r"255.255.255.255" #FTPS host
username=r"username" #FTPS username
password=r"T@jneHeSl0" #FTPS heslo
remote_dir=r"/domena.cz/web/public/prehledy" #FTPS složka, kam nahrát skript
visit=r"https://domena.cz/public/prehledy/" #URL ke složce, kam se nahrává - tato cesta musí být přístupná http nebo https protokolem
```

## ▶️ Instalace a spuštění - Windows

### Prvotní instalace před spuštěním:

Před tímto krokem je nutné mít nainstalovaný [Python](https://www.python.org/downloads/) a [Git](https://git-scm.com/install/).<br>
Spusť v příkazovém řádku následující příkazy, nebo si stáhni a spusť <code>install.bat</code>.<br> (Pro instalaci a spouštění bez virtuálního prostředí použij soubory s příponou _*_GLOBAL*_.)<br>
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
- spustit soubor <code>run.bat</code> (doporučeno)<br>
- nebo (pokud nepracuješ v okně, kde jsi prováděl instalaci):
```bash
.venv\Scripts\Activate.ps1
python main.py
```
- Pokud pracuješ v okně, kde jsi prováděl instalaci, stačí:
```bash
python main.py
```
#### Pokud registrace běží, ale závod je plný:
- spustit soubor <code>plny_zavod.bat</code> (doporučeno)<br>
- nebo (pokud nepracuješ v okně, kde jsi prováděl instalaci):
```bash
.venv\Scripts\Activate.ps1
python plny_zavod.py
```
- Pokud pracuješ v okně, kde jsi prováděl instalaci, stačí:
```bash
python plny_zavod.py
```
#### Pokud závod ještě nebyl vyhlášen, registrace už je spuštěna a závodník chce analýzu konkurence:
- spustit soubor <code>konkurence.bat</code> (doporučeno)<br>
- nebo (pokud nepracuješ v okně, kde jsi prováděl instalaci):
```bash
.venv\Scripts\Activate.ps1
python konkurence.py
```
- Pokud pracuješ v okně, kde jsi prováděl instalaci, stačí:
```bash
python konkurence.py
```
- Je možné spustit s argumenty JMÉNO DIVIZE URL pro přepsání dat o závodě a závodníkovi v souboru <code>data.py</code>. I zde je však potřeba mít vyplněný soubor data.py, aby se skript mohl na webu LOSu přihlásit a zobrazit si celá jména.<br>
např:
```bash
python konkurence.py "Jan Novák" "Pistole" "https://www.loslex.cz/contest/313"
```
(Skrtipt <code>konkurence.py</code> podporuje divize Pi, Opt a PDW. Ostatní divize autor jakožto zbytečné neuznává, proto jejich podpora nebude nikdy implementována.)

#### Pokud závod již skončil a čekáš na výsledky:
- spustit soubor <code>vysledky_zverejneny.bat</code> (doporučeno)<br>
- nebo (pokud nepracuješ v okně, kde jsi prováděl instalaci):
```bash
.venv\Scripts\Activate.ps1
python vysledky_zverejneny.py
```
- Pokud pracuješ v okně, kde jsi prováděl instalaci, stačí:
```bash
python vysledky_zverejneny.py
```

### Aktualizace na poslední verzi
```bash
git fetch --all
git reset --hard HEAD
git pull
```
nebo spuštěním souboru <code>update.bat</code>


## ▶️ Instalace a spuštění - Linux

### Prvotní instalace před spuštěním:

Před tímto krokem je nutné mít nainstalovaný Python a Git. Toto provedeš následujícími příkazy v terminálu:<br>
``` bash
sudo apt update
sudo apt install -y git python3 python3-venv python3-pip
```
Stáhni a spusť soubor <code>install.sh</code> příkazem 
``` bash
bash install.sh
```
případně jednoduše tímto příkazem rovnou instaluj:

``` bash
curl -fsSL https://los.krystofklika.cz/install.sh | bash

```
<br>
Registrátor se ti nainstaluje do <code>/home/USER/Documents</code>

### 🏁 Použití po instalaci:
#### Vytvoření konfigurace:
Přejmenuj soubor <code>data_sample.py</code> na <code>data.py</code> (toto automaticky dělá instalační skript <code>install.sh</code>) a vyplň ho.

#### Pokud registrace ještě nezačala:
- spustit soubor <code>run.sh</code> příkazem 
```bash
bash run.sh
```
<br>

#### Pokud registrace běží, ale závod je plný:
- spustit soubor <code>plny_zavod.sh</code> příkazem 
```bash
bash plny_zavod.sh
```
<br>

#### Pokud závod ještě nebyl vyhlášen, registrace už je spuštěna a závodník chce analýzu konkurence:
- spustit soubor <code>konkurence.sh</code> příkazem 
```bash
bash konkurence.sh
```
<br>

- Je možné spustit s argumenty JMÉNO DIVIZE URL pro přepsání dat o závodě a závodníkovi v souboru <code>data.py</code>. I zde je však potřeba mít vyplněný soubor data.py, aby se skript mohl na webu LOSu přihlásit a zobrazit si celá jména.<br>
např:
```bash
python3 konkurence.py "Jan Novák" "Pistole" "https://www.loslex.cz/contest/313"
```
(Skrtipt <code>konkurence.py</code> podporuje divize Pi, Opt a PDW. Ostatní divize autor jakožto zbytečné neuznává, proto jejich podpora nebude nikdy implementována.)

#### Pokud závod již skončil a čekáš na výsledky:
- spustit soubor <code>vysledky_zverejneny.sh</code> příkazem 
```bash
bash vysledky_zverejneny.sh
```

#### Pokud chceš vygenerovat CSV soubor s výsledky poháru:
- spustit soubor <code>csv.sh</code> příkazem 
```bash
bash csv.sh
```
<br>

### Aktualizace na poslední verzi
```bash
git fetch --all
git reset --hard HEAD
git pull
```
nebo spuštěním souboru <code>update.sh</code>
