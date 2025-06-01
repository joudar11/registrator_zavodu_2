from playwright.sync_api import sync_playwright
import time
from datetime import datetime, timedelta
import smtplib
from email.message import EmailMessage
from data import JMENO, CISLO_DOKLADU, CLENSKE_ID, DIVIZE, URL, LOGIN, HESLO, DATUM_CAS_REGISTRACE, SQUAD, GOOGLE_P, GOOGLE_U

divider = "=" * 30
MIMO_ZAVOD = False

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

def get_summary():
    print(f"\n{divider}\n")
    print("Budou použity následující údaje:")
    print(f"""
    Jméno: {JMENO}\n
    Číslo ZP: {CISLO_DOKLADU}\n
    LEX ID: {CLENSKE_ID}\n
    Divize: {DIVIZE}\n
    Squad: {SQUAD}\n
    URL závodu: {URL}\n
    Login: {LOGIN}\n
    Heslo: {HESLO}\n
    Datum a čas registrace: {DATUM_CAS_REGISTRACE}
    """)
    print(f"{divider}\n")

    return

def registrace():
    get_summary()
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        page.goto(URL)

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
            page.wait_for_load_state("load")

        else:
            # Režim bez časování → rovnou přihlášení
            print("⚡ Přihlašuji se a rovnou registruji (bez časování)...")
            page.click(SELECTOR_TLACITKO_PRIHLASIT)
            page.wait_for_selector(SELECTOR_INPUT_LOGIN)
            page.fill(SELECTOR_INPUT_LOGIN, LOGIN)
            page.fill(SELECTOR_INPUT_HESLO, HESLO)
            page.click(SELECTOR_TLACITKO_LOGIN)

        page.wait_for_selector(SELECTOR_TLACITKO_REGISTRACE)
        # Společná část registrace
        # page.fill(SELECTOR_INPUT_JMENO, JMENO)
        page.fill(SELECTOR_INPUT_DOKLAD, CISLO_DOKLADU)

        if CLENSKE_ID:
            page.check(SELECTOR_CHECKBOX_CLEN)
            page.fill(SELECTOR_INPUT_CLENSKE_ID, CLENSKE_ID)

        page.select_option(SELECTOR_SELECT_DIVIZE, label=DIVIZE)
        page.click(SELECTOR_SQUAD)
        page.check(SELECTOR_CHECKBOX_GDPR)
        page.click(SELECTOR_TLACITKO_REGISTRACE)

        print("✅ Registrace dokončena.")
        if DATUM_CAS_REGISTRACE is not None:
            posli_email()
        input("Stiskni ENTER pro zavření browseru...")
        # browser.close()  # nech otevřené pro kontrolu


def posli_email():
    msg = EmailMessage()
    msg['Subject'] = '✅ LOS Registrace proběhla'
    msg['From'] = GOOGLE_U
    msg['To'] = LOGIN
    msg.set_content(f"""Registrace na LOS proběhla úspěšně.
                    
    Divize: {DIVIZE}
    Squad: {SQUAD}
    URL závodu: {URL}""")

    # Přihlašovací údaje
    uzivatel = GOOGLE_U
    heslo = GOOGLE_P

    # Odeslání e-mailu
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(uzivatel, heslo)
        smtp.send_message(msg)

# --- SPUŠTĚNÍ ---
if __name__ == "__main__":
    registrace()