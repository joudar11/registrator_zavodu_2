from playwright.sync_api import sync_playwright
import time
from datetime import datetime, timedelta
import smtplib
from email.message import EmailMessage
import random
from playwright.sync_api import TimeoutError
from data import JMENO, CISLO_DOKLADU, CLENSKE_ID, DIVIZE, URL, LOGIN, HESLO, DATUM_CAS_REGISTRACE, SQUAD, GOOGLE_P, GOOGLE_U, MZ, ZACATECNIK, STAVITEL, ROZHODCI, POZNAMKA, PRITELKYNE, JMENO_PRITELKYNE

divider = "=" * 30
finished = None
datum_zavodu = None
nazev_zavodu = None

# --- SELEKTORY (uprav dle potřeby) ---
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
SELECTOR_CHECKBOX_MZ = r"#notcomp"
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
    Divize: {DIVIZE}\n
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

def registrace():
    print(divider)
    print(get_summary())
    print(divider)
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        try:
            page.goto(URL, timeout=15000)  # timeout můžeš snížit třeba na 15 s
        except Exception as e:
            print(f"❌ Nelze načíst stránku závodu. Server buď neodpovídá, nebo nejsi připojen k internetu.\n\n{e}")
            return False

        # Pokud je čas zadán → časovaný režim
        if DATUM_CAS_REGISTRACE is not None:
            try:
                cas_registrace = datetime.strptime(DATUM_CAS_REGISTRACE, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                print("❌ DATUM_CAS_REGISTRACE má špatný formát. Použij RRRR-MM-DD HH:MM:SS.")
                return

            cas_prihlaseni = cas_registrace - timedelta(seconds=30)

            print(f"⏳ Čekám na čas přihlášení: {cas_prihlaseni}")
            while datetime.now() < cas_prihlaseni:
                time.sleep(0.1)

            # Přihlášení
            print("🔐 Přihlašuji se...")
            page.click(SELECTOR_TLACITKO_PRIHLASIT)
            page.wait_for_selector(SELECTOR_INPUT_LOGIN)
            page.fill(SELECTOR_INPUT_LOGIN, LOGIN)
            page.fill(SELECTOR_INPUT_HESLO, HESLO)
            page.click(SELECTOR_TLACITKO_LOGIN)

            cilovy_cas = cas_registrace + timedelta(seconds=0.5)
            print(f"⏳ Čekám na čas registrace: {cilovy_cas}")
            while datetime.now() < cilovy_cas:
                time.sleep(0.05)

            # Refresh
            print("🔄 Refreshuji stránku...")
            page.reload()
            try:
                page.wait_for_load_state("load", timeout=5000)
            except TimeoutError:
                print("❌ Stránka nenalezla tlačítko registrace.")
                return False

        else:
            # Režim bez časování → rovnou přihlášení
            print("⚡ Přihlašuji se a rovnou registruji (bez časování)...")
            page.click(SELECTOR_TLACITKO_PRIHLASIT)
            page.wait_for_selector(SELECTOR_INPUT_LOGIN)
            page.fill(SELECTOR_INPUT_LOGIN, LOGIN)
            page.fill(SELECTOR_INPUT_HESLO, HESLO)
            page.click(SELECTOR_TLACITKO_LOGIN)

        try:
            page.wait_for_selector(SELECTOR_TLACITKO_REGISTRACE, timeout=5000)
        except TimeoutError:
            print("❌ Stránka nenalezla tlačítko registrace.")
            return False
        # Společná část registrace
        # page.fill(SELECTOR_INPUT_JMENO, JMENO)
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

        if MZ:
            page.check(SELECTOR_CHECKBOX_MZ)
        
        if STAVITEL:
            page.check(SELECTOR_CHECKBOX_STAVITEL)

        page.select_option(SELECTOR_SELECT_DIVIZE, label=DIVIZE)
        page.click(SELECTOR_SQUAD)
        page.check(SELECTOR_CHECKBOX_GDPR)
        delay = random.uniform(2, 3)
        print(f"⏳ Čekám {delay:.2f} sekundy...")
        time.sleep(delay)
        page.click(SELECTOR_TLACITKO_REGISTRACE)
        try:
            page.wait_for_selector(SELECTOR_DATUM, timeout=5000)
        except TimeoutError:
            print("❌ Registrace pravděpodobně selhala – nepodařilo se načíst datum závodu.")
            return False
        global finished
        finished = datetime.now()

        print("✅ Registrace dokončena.")
        page.wait_for_selector(SELECTOR_DATUM)
        global datum_zavodu
        try:
            datum_zavodu = page.inner_text(SELECTOR_DATUM, timeout=5000)
        except Exception as e:
            print(f"⚠️ Nepodařilo se získat datum závodu: {e}")
            datum_zavodu = "neznámé datum"
        global nazev_zavodu
        try:
            nazev_zavodu = page.inner_text(SELECTOR_NAZEV, timeout=5000)
        except Exception as e:
            print(f"⚠️ Nepodařilo se získat název závodu: {e}")
            nazev_zavodu = "neznámý název"

        if DATUM_CAS_REGISTRACE is not None:
            posli_email()
            informuj_pritelkyni()
        input("Stiskni ENTER pro zavření browseru a ukončení...")
        return True
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

    # Odeslání e-mailu
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(uzivatel, heslo)
        smtp.send_message(msg)
    print(f"✅ Shrnutí odesláno na {LOGIN}.")

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
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(uzivatel, heslo)
        smtp.send_message(msg)
    print(f"✅ {JMENO_PRITELKYNE} informována.")

# --- SPUŠTĚNÍ ---
if __name__ == "__main__":
    while True:
        if registrace():
            break
        print("❌ Pokus o registraci selhal. Zkouším znovu...")
