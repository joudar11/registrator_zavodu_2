# --- Standardní knihovny ---
import os
import time
import random
import smtplib
from datetime import datetime, timedelta
from email.message import EmailMessage

# --- Externí knihovny ---
from playwright.sync_api import sync_playwright, TimeoutError

# --- Lokální moduly ---
from data import (
    JMENO, CISLO_DOKLADU, CLENSKE_ID, DIVIZE, URL,
    LOGIN, HESLO, DATUM_CAS_REGISTRACE, SQUAD,
    GOOGLE_P, GOOGLE_U, MZ, ZACATECNIK, STAVITEL,
    ROZHODCI, POZNAMKA, PRITELKYNE, JMENO_PRITELKYNE
)

LIMIT = 50 # Po tomto počtu neúspěšných pokusů se program ukončí
divider = "=" * 30
finished = None
datum_zavodu = None
nazev_zavodu = None

SQUAD = str(SQUAD)
REG_URL = "https://www.loslex.cz/contest/registration"
DIVIZE_local = DIVIZE # Bere si divizi do proměnné, se kterou je možné v rámci main dále pracovat a měnit ji (pro ochranu proti neexistující  divizi)
POKUS_TIME = None # Čas zahájení pokusu o registraci (pro log)

SELECTOR_TLACITKO_PRIHLASIT = r"body > div.min-h-screen.bg-gray-100.dark\:bg-gray-900 > nav > div.max-w-7xl.mx-auto.px-4.md\:px-6.lg\:px-8 > div > div.hidden.space-x-1.items-center.md\:-my-px.md\:ml-10.md\:flex > button.inline-flex.items-center.px-1.border-b-2.border-transparent.text-sm.font-medium.leading-5.text-gray-500.dark\:text-gray-400.hover\:text-gray-700.dark\:hover\:text-gray-300.hover\:border-gray-300.dark\:hover\:border-gray-700.focus\:outline-none.focus\:text-gray-700.dark\:focus\:text-gray-300.focus\:border-gray-300.dark\:focus\:border-gray-700.transition.duration-150.ease-in-out"  # tlačítko pro zobrazení login formuláře
SELECTOR_INPUT_LOGIN = r"#login"
SELECTOR_INPUT_HESLO = r"#password"
SELECTOR_TLACITKO_LOGIN = r"body > div.fixed.inset-0.overflow-y-auto.px-4.py-6.sm\:px-0.z-2000 > div.mb-6.bg-white.dark\:bg-gray-800.rounded-lg.overflow-hidden.shadow-xl.transform.transition-all.sm\:w-full.sm\:max-w-md.sm\:mx-auto > div > form > div.flex.items-center.justify-end.mt-4 > button"

SELECTOR_INPUT_JMENO = r"#username"
SELECTOR_INPUT_DOKLAD = r"#licenceid"
SELECTOR_CHECKBOX_CLEN = r"#lexmember"
SELECTOR_INPUT_CLENSKE_ID = r"#lexhash"
SELECTOR_SELECT_DIVIZE = r"#contest_division_id"
SELECTOR_SQUAD = f"#squad-{SQUAD}"
SELECTOR_CHECKBOX_GDPR = r"#gdpr"
SELECTOR_TLACITKO_REGISTRACE = r"#regform > div.flex.flex-col.items-center.justify-center > button"
SELECTOR_CHECKBOX_MZ = r'#notcomp[type="checkbox"]'
SELECTOR_INPUT_POZNAMKA = r"#note"
SELECTOR_CHECKBOX_ROZHODCI = r"#referee"
SELECTOR_CHECKBOX_STAVITEL = r"#builder"
SELECTOR_CHECKBOX_ZACATECNIK = r"#rookie"
SELECTOR_DATUM = r"body > div.min-h-screen.bg-gray-100.dark\:bg-gray-900 > main > div.py-4 > div > div > div > div:nth-child(1) > div.grid.grid-cols-auto.lg\:grid-cols-fitfirst.gap-x-2.lg\:gap-x-4.gap-y-2 > div:nth-child(10)"
SELECTOR_NAZEV = r"body > div.min-h-screen.bg-gray-100.dark\:bg-gray-900 > main > div.py-4 > div > div > div > div:nth-child(1) > div.justify-center.items-baseline.text-xl.font-bold.flex"

def get_summary():
    summary = f"""\n\nÚdaje použité při registraci:\n
    Jméno: {JMENO}\n
    Číslo ZP: {CISLO_DOKLADU}\n
    LEX ID: {CLENSKE_ID}\n
    Divize: {DIVIZE_local}\n
    Squad: {SQUAD}\n
    URL závodu: {URL}\n
    Login: {LOGIN}\n
    Datum a čas registrace: {DATUM_CAS_REGISTRACE}\n
    Mimo závod: {MZ}\n
    Rozhodčí: {ROZHODCI}\n
    Začátečník: {ZACATECNIK}\n
    Stavitel: {STAVITEL}\n
    Poznámka: {POZNAMKA}
    """
    return summary

def print_and_log(action: str):
    print(action)
    try:
        os.makedirs("logs", exist_ok=True)
    except Exception as e:
        print(f"❌ Nelze vytvořit složku logs: {e}")
        return
    with open(f"logs/log-{POKUS_TIME}.txt", "a", encoding="utf-8") as f:
        f.write(f"[{datetime.now()}] {action}\n")

def prihlasit(page):
    try:
        page.click(SELECTOR_TLACITKO_PRIHLASIT)
    except Exception as e:
        print_and_log(f"❌ Nelze kliknout na tlačítko pro zobrazení přihlášení: {e}")
        return False

    try:
        page.wait_for_selector(SELECTOR_INPUT_LOGIN)
        page.fill(SELECTOR_INPUT_LOGIN, LOGIN)
        page.fill(SELECTOR_INPUT_HESLO, HESLO)
    except Exception as e:
        print_and_log(f"❌ Nepodařilo se vyplnit přihlašovací údaje: {e}")
        return False

    try:
        page.wait_for_selector(SELECTOR_TLACITKO_LOGIN, state="visible", timeout=10000)
        page.click(SELECTOR_TLACITKO_LOGIN)
    except TimeoutError:
        print_and_log("❌ Tlačítko Přihlásit se nepodařilo kliknout – timeout.")
        return False

def registrace():
    global DIVIZE_local
    print(divider)
    print(get_summary())
    print(divider)
    # Zahájení práce s prohlížečem
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        # Pokud je server LOSu down, operace selže, funkce se ukončí a jede se od začátku, dokud server nebude odpovídat
        try:
            page.goto(URL, timeout=10000) 
        except Exception as e:
            print_and_log(f"❌ Nelze načíst stránku závodu. Server buď neodpovídá, nebo nejsi připojen k internetu.\n\n{e}")
            return False

        # Pokud je čas zadán → časovaný režim
        if DATUM_CAS_REGISTRACE is not None:
            try:
                cas_registrace = datetime.strptime(DATUM_CAS_REGISTRACE, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                # Toto je jediná instance selhání programu, která funkci nespustí znovu. Opětovné spuštění by nemělo smysl, jelikož chyba je ve vadném vstupu.
                print_and_log("❌ DATUM_CAS_REGISTRACE má špatný formát. Použij RRRR-MM-DD HH:MM:SS. Ukončuji program.")
                return True

            cas_prihlaseni = cas_registrace - timedelta(seconds=30)

            print_and_log(f"⏳ Čekám na čas přihlášení: {cas_prihlaseni}")
            while datetime.now() < cas_prihlaseni:
                time.sleep(0.1)

            # Přihlášení
            print_and_log("🔐 Přihlašuji se...")
            prihlasit(page)

            cilovy_cas = cas_registrace + timedelta(seconds=0.5)
            print_and_log(f"⏳ Čekám na čas registrace: {cilovy_cas}")
            while datetime.now() < cilovy_cas:
                time.sleep(0.05)

            # Refresh po spuštění registrace
            print_and_log("🔄 Refreshuji stránku...")
            try:
                page.goto(URL, wait_until="domcontentloaded", timeout=5000)
            except TimeoutError:
                print_and_log("❌ Timeout při refreshi stránky – pokračuju dál.")
                return False
            try:
                page.wait_for_load_state("load", timeout=5000)
            except TimeoutError:
                print_and_log("❌ Stránku registrace se nepodařilo načíst.")
                return False

        else:
            # Režim bez časování → rovnou přihlášení
            print_and_log("⚡ Přihlašuji se a rovnou registruji (bez časování)...")
            prihlasit(page)

        # Kontrola, že server odpovídá - 5s. Pokud ne, funkce selže a jede se od začátku.
        try:
            page.wait_for_selector(SELECTOR_TLACITKO_REGISTRACE, timeout=5000)
        except TimeoutError:
            print_and_log("❌ Stránka nenalezla tlačítko registrace.")
            return False
        

        # Společná část registrace
        page.fill(SELECTOR_INPUT_DOKLAD, CISLO_DOKLADU)
        if CLENSKE_ID:
            page.check(SELECTOR_CHECKBOX_CLEN)
            page.fill(SELECTOR_INPUT_CLENSKE_ID, CLENSKE_ID)
        if POZNAMKA:
            page.fill(SELECTOR_INPUT_POZNAMKA, POZNAMKA)
        if ROZHODCI:
            page.check(SELECTOR_CHECKBOX_ROZHODCI)
        if ZACATECNIK:
            page.check(SELECTOR_CHECKBOX_ZACATECNIK)
        if MZ and not page.locator(SELECTOR_CHECKBOX_MZ).is_checked():
            page.check(SELECTOR_CHECKBOX_MZ)
        if STAVITEL:
            page.check(SELECTOR_CHECKBOX_STAVITEL)

        # Ošetření neplatné divize. Pokud zvolená divize není v závodu, bude zvolena první možná divize. Závodník si následně registraci upraví, ale nepřijde o místo v závodě.
        try:
            page.select_option(SELECTOR_SELECT_DIVIZE, label=DIVIZE_local, timeout=500)
        except Exception:
            print_and_log(f"⚠️ Nepodařilo se vybrat divizi {DIVIZE} - vybírám první možnou divizi.")
            try:
                moznosti = page.locator(f"{SELECTOR_SELECT_DIVIZE} option")
                prvni_moznost = moznosti.nth(1).get_attribute("value")
                if prvni_moznost:
                    prvni_moznost_hodnota = moznosti.nth(1).text_content()
                    page.select_option(SELECTOR_SELECT_DIVIZE, value=prvni_moznost)
                    print_and_log(f"⚠️ Zvolena první dostupná divize: {prvni_moznost_hodnota}")
                    DIVIZE_local = prvni_moznost_hodnota
            except Exception as inner_e:
                print_and_log(f"❌ Nepodařilo se vybrat první možnou divizi: {inner_e}")
                return False
        
        try:
            page.click(SELECTOR_SQUAD)
        except Exception as e:
            print_and_log(f"❌ Nepodařilo se vybrat squad {SQUAD}: {e}")
            return False
        
        try:
            page.check(SELECTOR_CHECKBOX_GDPR)
        except Exception as e:
            print_and_log(f"❌ Nepodařilo se zaškrtnout souhlas s GDPR: {e}")
            return False

        # Uložení údajů ze závodu do globálních proměnných pro odeslání na mail.
        global datum_zavodu
        try:
            datum_zavodu = page.inner_text(SELECTOR_DATUM, timeout=5000)
        except Exception as e:
            print_and_log(f"⚠️ Nepodařilo se získat datum závodu: {e}")
            datum_zavodu = "neznámé datum"
        global nazev_zavodu
        try:
            nazev_zavodu = page.inner_text(SELECTOR_NAZEV, timeout=5000)
        except Exception as e:
            print_and_log(f"⚠️ Nepodařilo se získat název závodu: {e}")
            nazev_zavodu = "neznámý název"

        # Čekání a odeslání registrace v náhodném intervalu + uložení času kliknutí do globální proměnné
        delay = random.uniform(2, 3)
        print_and_log(f"⏳ Čekám {delay:.2f} sekundy...")
        time.sleep(delay)
        try:
            page.wait_for_selector(SELECTOR_TLACITKO_REGISTRACE, timeout=5000)
            # page.click(SELECTOR_TLACITKO_REGISTRACE)
            page.goto("https://www.loslex.cz/contest/registration/10297")
        except Exception as e:
            print_and_log(f"❌ Nepodařilo se kliknout na tlačítko registrace: {e}")
            return False
        global finished
        finished = datetime.now()

        # Kontrola, že registrace proběhla (zobrazila se stránka registrace)
        max_wait = 8  # vteřin
        start_time = time.time()
        while not page.url.startswith(REG_URL):
            if time.time() - start_time > max_wait:
                print_and_log(f"❌ Registrace pravděpodobně selhala – URL se nezměnila do {max_wait} sekund.\nAktuální URL: {page.url}")
                return False
            time.sleep(0.1)
        
        print_and_log(f"✅ Registrace na závod {nazev_zavodu} - {datum_zavodu} dokončena.")

        # Po dokončení registrace počká specifikovaný čas a následně ukončuje program.
        max_wait = 60  # sekund
        start_time = time.time()
        print_and_log(f"⏳ Čekám {max_wait} sekund pro kontrolu uživatelem. Následně se ukončím.")
        informuj_pritelkyni()
        posli_email()
        while True:
            if time.time() - start_time > max_wait:
                return True
            time.sleep(1)

        return True # Toto volání je prakticky zbytečné, jde pouze o pojistku, kdyby selhala čekací funkce výše.
        
        # input("Stiskni ENTER pro zavření browseru a ukončení...")
        # return True
        # browser.close()  # nech otevřené pro kontrolu

def posli_email():
    msg = EmailMessage()
    msg['Subject'] = '✅ LOS Registrace proběhla'
    msg['From'] = GOOGLE_U
    msg['To'] = LOGIN
    msg.set_content(
    f"""Registrace na závod proběhla úspěšně.

Závod: {nazev_zavodu}
Datum závodu: {datum_zavodu}

Čas odeslání formuláře: {finished}

{get_summary()
    .replace("\n\n", "\n")
    .replace("    ", "")
    .replace("registraci:", "registraci:\n")}"""
)

    # Přihlašovací údaje
    uzivatel = GOOGLE_U
    heslo = GOOGLE_P
    
    with open(f"logs/log-{POKUS_TIME}.txt", "rb") as f:
        msg.add_attachment(f.read(), maintype="text", subtype="plain", filename=f"Registraction LOG.txt")

    # Odeslání e-mailu
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(uzivatel, heslo)
        smtp.send_message(msg)
    print_and_log(f"✅ Shrnutí odesláno na {LOGIN}.")

def informuj_pritelkyni():
    msg = EmailMessage()
    msg['Subject'] = '🔫 Tvůj kluk pojede na závod'
    msg['From'] = GOOGLE_U
    msg['To'] = PRITELKYNE
    msg.set_content(f"""Tvůj kluk se svým úžasným Python skriptem právě přihlásil na závod {nazev_zavodu}, který proběhne {datum_zavodu}.\n\nBude potřebovat držet palce.\n\nMiluju tě. ❤️\n\n\n(Automaticky generovaný email)""")

    # Přihlašovací údaje
    uzivatel = GOOGLE_U
    heslo = GOOGLE_P

    # Odeslání e-mailu

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(uzivatel, heslo)
            smtp.send_message(msg)
        print_and_log(f"✅ {JMENO_PRITELKYNE} informována.")
    except Exception as e:
        print_and_log(f"❌ Nepodařilo se informovat přítelkyni: {e}")

if __name__ == "__main__":
    # Funkce spouští registraci stále dokola, dokud registrace nebude úspěšná
    POKUS_TIME = datetime.now().replace(microsecond=0).strftime("%Y-%m-%d_%H-%M-%S")
    cislo_pokusu = 1
    while cislo_pokusu <= LIMIT:
        print_and_log(f"🔁 Pokus o registraci č. {cislo_pokusu} z {LIMIT}")
        if registrace():
            break
        print_and_log("❌ Pokus o registraci selhal. Zkouším znovu...")
        cislo_pokusu += 1
    if cislo_pokusu > LIMIT:
        print_and_log(f"❌ Registrace selhala i po {LIMIT} pokusech. Skript končí.")