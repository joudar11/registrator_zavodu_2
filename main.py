# --- Standardní knihovny ---
import os
import time
import random
import smtplib
from datetime import datetime, timedelta
from email.message import EmailMessage
import re
import sys
from check_version import zkontroluj_a_aktualizuj
if __name__ == "__main__":
    global_env = (len(sys.argv) == 2 and sys.argv[1] == "global")
    zkontroluj_a_aktualizuj(global_env)

# --- Externí knihovny ---
from playwright.sync_api import sync_playwright, TimeoutError

# --- Lokální moduly ---
from data import (
    JMENO, CISLO_DOKLADU, CLENSKE_ID, DIVIZE, URL,
    LOGIN, HESLO, SQUAD,
    EMAIL_P, EMAIL_U, MZ, ZACATECNIK, STAVITEL,
    ROZHODCI, POZNAMKA, PRITELKYNE, JMENO_PRITELKYNE, RANDOM_WAIT, EMAIL_PROVIDER
)
import vytvor_ics

LIMIT = 25  # Po tomto počtu neúspěšných pokusů se program ukončí
divider = "=" * 30  # Pouze pro tisk ve stringu
finished = None  # Sem se následně uloží čas dokončení registrace
datum_zavodu = None  # Sem se následně uloží datum závodu (pro odeslání mailem)
nazev_zavodu = None  # Sem se následně uloží název závodu (pro odeslání mailem)
SEKUND = 2.2  # Jak dlouho po nastání času registrace má skript refreshnout stránku
ics_file = None
STALE_BEZI_MINUT = 45 #Kolik minut před registrací poslat potvrzovací email, že skript stále běží
REGISTRACE_STAV = None
DATUM_CAS_REGISTRACE = None

fatal_error = False

REG_URL = "https://www.loslex.cz/contest/registration"
# Bere si divizi do proměnné, se kterou je možné v rámci main dále pracovat a měnit ji (pro ochranu proti neexistující  divizi)
DIVIZE_local = DIVIZE
# Převedení int squadu na str a proměnnou v této funkci pro pozdější použití a změny
SQUAD_local = str(SQUAD)
POKUS_TIME = None  # Čas zahájení pokusu o registraci (pro název log souboru)

EMAIL_PROVIDERS = ("PROTON", "GMAIL", "PROTON-TOKEN")

# Selectory pro login
SELECTOR_TLACITKO_PRIHLASIT = r"body > div.min-h-screen.bg-gray-100.dark\:bg-gray-900 > nav > div.max-w-7xl.mx-auto.px-4.md\:px-6.lg\:px-8 > div > div.hidden.space-x-1.items-center.md\:-my-px.md\:ml-10.md\:flex > button.inline-flex.items-center.px-1.border-b-2.border-transparent.text-sm.font-medium.leading-5.text-gray-500.dark\:text-gray-400.hover\:text-gray-700.dark\:hover\:text-gray-300.hover\:border-gray-300.dark\:hover\:border-gray-700.focus\:outline-none.focus\:text-gray-700.dark\:focus\:text-gray-300.focus\:border-gray-300.dark\:focus\:border-gray-700.transition.duration-150.ease-in-out"  # tlačítko pro zobrazení login formuláře
SELECTOR_INPUT_LOGIN = r"#login"
SELECTOR_INPUT_HESLO = r"#password"
SELECTOR_TLACITKO_LOGIN = r"body > div.fixed.inset-0.overflow-y-auto.px-4.py-6.sm\:px-0.z-2000 > div.mb-6.bg-white.dark\:bg-gray-800.rounded-lg.overflow-hidden.shadow-xl.transform.transition-all.sm\:w-full.sm\:max-w-md.sm\:mx-auto > div > form > div.flex.items-center.justify-end.mt-4 > button"

# Selectory pro registraci
SELECTOR_INPUT_JMENO = r"#username"
SELECTOR_INPUT_DOKLAD = r"#licenceid"
SELECTOR_CHECKBOX_CLEN = r"#lexmember"
SELECTOR_INPUT_CLENSKE_ID = r"#lexhash"
SELECTOR_SELECT_DIVIZE = r"#contest_division_id"
SELECTOR_SQUAD = f"#squad-{SQUAD}"
SELECTOR_SQUAD1 = r"#squad-1"
SELECTOR_CHECKBOX_GDPR = r"#gdpr"
SELECTOR_TLACITKO_REGISTRACE = r"#regform > div.flex.flex-col.items-center.justify-center > button"
SELECTOR_CHECKBOX_MZ = r'#notcomp[type="checkbox"]'
SELECTOR_INPUT_POZNAMKA = r"#note"
SELECTOR_CHECKBOX_ROZHODCI = r"#referee"
SELECTOR_CHECKBOX_STAVITEL = r"#builder"
SELECTOR_CHECKBOX_ZACATECNIK = r"#rookie"
SELECTOR_ZBROJNI_OPRAVNENI = r"#has_falicence"

# Selectory pro scrapnutí dat
SELECTOR_DATUM = r"body > div.min-h-screen.bg-gray-100.dark\:bg-gray-900 > main > div.py-4 > div > div > div > div:nth-child(1) > div.grid.grid-cols-auto.lg\:grid-cols-fitfirst.gap-x-2.lg\:gap-x-4.gap-y-2 > div:nth-child(10)"
SELECTOR_NAZEV = r"body > div.min-h-screen.bg-gray-100.dark\:bg-gray-900 > main > div.py-4 > div > div > div > div:nth-child(1) > div.justify-center.items-baseline.text-xl.font-bold.flex"
SELECTOR_SPATNE_UDAJE = r"body > div.fixed.inset-0.overflow-y-auto.px-4.py-6.sm\:px-0.z-2000 > div.mb-6.bg-white.dark\:bg-gray-800.rounded-lg.overflow-hidden.shadow-xl.transform.transition-all.sm\:w-full.sm\:max-w-md.sm\:mx-auto > div > form > div:nth-child(3) > ul"


PRITELKYNE_INSERT_1 = ""
PRITELKYNE_INSERT_2 = ""
PRITELKYNE_INSERT_3 = "\nK registraci použil skript od Kryštofa Kliky: https://github.com/joudar11/registrator_zavodu_2"


if JMENO == "Kryštof Klika":
    PRITELKYNE_INSERT_1 = "svým úžasným Python skriptem "
    PRITELKYNE_INSERT_2 = "\nMiluju tě. ❤️"
    PRITELKYNE_INSERT_3 = ""

def get_summary() -> str:
    """Vytiskne do konzole shrnutí údajů použitých při registraci"""
    summary = f"""\nÚdaje použité při registraci:\n
    Jméno: {JMENO}\n
    Divize: {DIVIZE_local}\n
    Squad: {SQUAD_local}\n
    URL závodu: {URL}\n\n
    Číslo OP/EZP: {CISLO_DOKLADU}\n
    LEX ID: {CLENSKE_ID}\n
    Login: {LOGIN}\n
    Datum a čas registrace (nebo jejího konce, pokud již běží): {DATUM_CAS_REGISTRACE}\n\n
    Mimo závod: {MZ}\n
    Rozhodčí: {ROZHODCI}\n
    Začátečník: {ZACATECNIK}\n
    Stavitel: {STAVITEL}\n
    Poznámka: {POZNAMKA}
    """
    return summary


def print_and_log(action: str) -> None:
    """Zprávu předanou argumentem vytiskne do konzole a zároveň uloží na konec logu."""
    print(action)
    folder = "logs"  # složka, kam se uloží log
    try:
        os.makedirs(folder, exist_ok=True)
    except Exception as e:
        print(f"❌ Nelze vytvořit složku {folder}:\n{e}")
        return

    # Zápis do logu
    with open(f"{folder}/log-{POKUS_TIME}.txt", "a", encoding="utf-8") as f:
        f.write(f"[{datetime.now()}] {action}\n")


def prihlasit(page) -> None:
    """Na stránce předané argumentem se přihlásí s použitím konstant importovaných na začátku."""
    global fatal_error
    try:
        page.click(SELECTOR_TLACITKO_PRIHLASIT)
    except Exception as e:
        print_and_log(
            f"❌ Nelze kliknout na tlačítko pro zobrazení přihlášení:\n{e}")
        return False

    try:
        page.wait_for_selector(SELECTOR_INPUT_LOGIN)
        page.fill(SELECTOR_INPUT_LOGIN, LOGIN)
        page.fill(SELECTOR_INPUT_HESLO, HESLO)
    except Exception as e:
        print_and_log(f"❌ Nepodařilo se vyplnit přihlašovací údaje:\n{e}")
        return False

    try:
        page.wait_for_selector(SELECTOR_TLACITKO_LOGIN,
                               state="visible", timeout=10000)
        page.click(SELECTOR_TLACITKO_LOGIN)
    except TimeoutError:
        print_and_log("❌ Tlačítko Přihlásit se nepodařilo kliknout – timeout.")
        return False
    if page.locator(SELECTOR_SPATNE_UDAJE).is_visible():
        print_and_log("❌❌❌ Špatné přihlašovací údaje! ❌❌❌")
        fatal_error = True
        return False
    return True

def nacti_text_ze_stranky(page, label_text: str) -> str:
    """Vrátí text hodnoty z páru 'label : value'."""
    label = page.locator(f"xpath=//div[normalize-space()='{label_text}']").first
    value = label.locator("xpath=following-sibling::div[1]")
    value.wait_for(timeout=5000)
    return value.inner_text().strip()

def parse_registrace_text(text: str) -> str | None:
    global REGISTRACE_STAV
    global fatal_error

    # mapa českých měsíců -> čísla
    mesiace = {
        "ledna": "01",
        "února": "02",
        "unora": "02",
        "brezna": "03",
        "března": "03",
        "dubna": "04",
        "května": "05",
        "kvetna": "05",
        "cervna": "06",
        "června": "06",
        "cervence": "07",
        "července": "07",
        "srpna": "08",
        "září": "09",
        "zari": "09",
        "října": "10",
        "rijna": "10",
        "listopadu": "11",
        "prosince": "12",
    }

    text_l = text.lower()

    # stav registrace
    if "registrace skončila" in text_l:
        REGISTRACE_STAV = "skoncila"
        fatal_error = True
        return None

    if "registrace začne" in text_l:
        REGISTRACE_STAV = "zacne"
    elif "registrace skončí" in text_l:
        REGISTRACE_STAV = "probiha"
    else:
        REGISTRACE_STAV = None

    # regex na zachycení data (např. 12. listopadu 2025 23:00)
    m = re.search(r"(\d{1,2})\. ([a-záéěíóúůýžščřďťň]+) (\d{4}) (\d{1,2}:\d{2})", text_l)
    if not m:
        return None

    den, mesic_text, rok, cas = m.groups()

    # převede český měsíc na číslo
    mesic_text = mesic_text.replace("ě", "e").replace("š", "s").replace("č", "c").replace("ř", "r").replace("ů", "u").replace("ž", "z").replace("á","a").replace("í","i").replace("ý","y").replace("ď","d").replace("ť","t").replace("ň","n").replace("ó","o").replace("ú","u").replace("é","e")

    mesic = mesiace.get(mesic_text)
    if not mesic:
        return None

    datum = f"{rok}-{mesic}-{int(den):02d} {cas}:00"
    return datum

def registrace(pokus: int) -> bool:
    """Hlavní část programu. Funkce obsahuje časování, volání přihlášení, volání funkcí pro doesílání emailů, verifikaci importovaných konstant, ochrany proti padnutí programu a fallbacky."""
    global DIVIZE_local
    global SQUAD_local
    global datum_zavodu
    global nazev_zavodu
    global finished
    global fatal_error
    global ics_file
    global DATUM_CAS_REGISTRACE

    # Shrnutí načtených údajů

    # Zahájení práce s prohlížečem
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # Pokud je server LOSu down, operace selže, funkce se ukončí a jede se od začátku, dokud server nebude odpovídat
        try:
            page.goto(URL, timeout=10000)
        except Exception as e:
            print_and_log(
                f"❌ Nelze načíst stránku závodu. Server buď neodpovídá, nebo nejsi připojen k internetu.\n\n{e}")
            return False

        if page.title() == "Nenalezeno":
            print_and_log(
                f"❌❌❌ Stránka závodu {URL} nebyla nalezena - 404 ❌❌❌")
            fatal_error = True
            return False
        
            
        datum_registrace_extrahovat = (nacti_text_ze_stranky(page, "Registrace:"))
        datum_registrace_extrahovano = parse_registrace_text(datum_registrace_extrahovat)
        DATUM_CAS_REGISTRACE = datum_registrace_extrahovano
        print(f"Stav registrace: {REGISTRACE_STAV}")
        if pokus == 1:
            print(divider, get_summary(), divider, sep="\n")

        # Pokud je čas zadán → časovaný režim
        if DATUM_CAS_REGISTRACE and pokus == 1 and REGISTRACE_STAV == "zacne":
            try:
                cas_registrace = datetime.strptime(
                    DATUM_CAS_REGISTRACE, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                # Opětovné spuštění by nemělo smysl, jelikož chyba je ve vadném vstupu.
                print_and_log(
                    "❌❌❌ DATUM_CAS_REGISTRACE má špatný formát. Použij RRRR-MM-DD HH:MM:SS. Ukončuji program. ❌❌❌")
                fatal_error = True
                return False

            # Přihlášení na registrační web proběhne 30s před spuštěním registrace
            cas_prihlaseni = cas_registrace - timedelta(seconds=30)
            cas_notifikace = cas_registrace - timedelta(minutes=STALE_BEZI_MINUT)
            notifikovano = False

            if int((cas_registrace - datetime.now()).total_seconds() // 60) > 60:
                try:
                    informuj_o_zacatku()
                except Exception as e:
                    print_and_log(
                        f"❌ Nepodařilo se odeslat zahajovací email. Pokračuji. {e}")

            # print_and_log(f"ℹ️ Čekám na čas přihlášení: {cas_prihlaseni}")
            
            if cas_registrace - datetime.now() > timedelta(minutes=60):
                print_and_log(f"ℹ️ Čekám do {cas_notifikace} na odeslání potvrzovacího e-mailu, "
              f"následně do {cas_registrace} na registraci.")
                while datetime.now() < cas_notifikace:
                    time.sleep(60)

                try:
                    stale_bezi()
                    print_and_log(
                        "✅ Odeslal jsem notifikační email o tom, že skript stále běží.")
                except Exception as e:
                    print_and_log(
                        "❌ Nepodařilo se odeslat pokračovací email. Pokračuji.")

            # while datetime.now() < cas_prihlaseni:
            #     time.sleep(0.1)

            # Přihlášení bylo původně zde


            # Uspání skriptu, dokud nenastane čas spuštění registrace
            cilovy_cas = cas_registrace + timedelta(seconds=SEKUND)
            print_and_log(f"ℹ️ Čekám na čas registrace: {cilovy_cas}")
            while datetime.now() < cilovy_cas:
                time.sleep(0.05)

            print_and_log("ℹ️ Přihlašuji se...")
            if not prihlasit(page):
                return False

            page.goto(URL, wait_until="networkidle")



            # Refresh po spuštění registrace, aby se zobrazily prvky formuláře
            # print_and_log("ℹ️ Refreshuji stránku...")
            # try:
            #     page.goto(URL, wait_until="domcontentloaded", timeout=2000)
            # except TimeoutError:
            #     print_and_log(
            #         "❌ Timeout při refreshi stránky – pokračuji dál.")
            #     return False

            # Čekání na načtení stránky po refreshi
            try:
                page.wait_for_load_state("load", timeout=2000)
            except TimeoutError:
                print_and_log("❌ Stránku registrace se nepodařilo načíst.")
                return False

        elif REGISTRACE_STAV == "probiha":
            # Režim bez časování → rovnou přihlášení
            print_and_log("ℹ️ Přihlašuji se a rovnou registruji...")
            if not prihlasit(page):
                return False
        else:
            if REGISTRACE_STAV == "skoncila":
                print_and_log("❌ Registrace již skončila.")
            else:
                print_and_log("❌ Neočekávaná chyba při rozhodování o stavu registrace.")
                fatal_error = True
            return False

        # try:
        #     page.wait_for_selector(SELECTOR_TLACITKO_REGISTRACE, timeout=4000)
        # except TimeoutError:
        #     print_and_log("❌ Stránka nenalezla tlačítko registrace.")
        #     return False

        # Toto ověření generovalo neustálé chyby a vlastně není potřebné

        # Společná část registrace
        try:
            page.fill(SELECTOR_INPUT_DOKLAD, CISLO_DOKLADU, timeout=3000)
            page.check(SELECTOR_ZBROJNI_OPRAVNENI, timeout=3000)
            if CLENSKE_ID:
                page.check(SELECTOR_CHECKBOX_CLEN, timeout=3000)
                page.fill(SELECTOR_INPUT_CLENSKE_ID, CLENSKE_ID, timeout=3000)
            if POZNAMKA:
                page.fill(SELECTOR_INPUT_POZNAMKA, POZNAMKA, timeout=3000)
            if ROZHODCI:
                page.check(SELECTOR_CHECKBOX_ROZHODCI, timeout=3000)
            if ZACATECNIK:
                page.check(SELECTOR_CHECKBOX_ZACATECNIK, timeout=3000)
            if MZ and not page.locator(SELECTOR_CHECKBOX_MZ).is_checked():
                page.check(SELECTOR_CHECKBOX_MZ, timeout=3000)
            if STAVITEL:
                page.check(SELECTOR_CHECKBOX_STAVITEL, timeout=3000)
        except Exception as e:
            print_and_log(
                f"❌ Nepodařilo se vyplnit registrační formulář:\n{e}")
            return False

        # Ošetření neplatné divize. Pokud zvolená divize není v závodu, bude zvolena první možná divize. Závodník si následně registraci upraví, ale nepřijde o místo v závodě.
        try:
            page.select_option(SELECTOR_SELECT_DIVIZE,
                               label=DIVIZE_local, timeout=500)
        except Exception:
            print_and_log(
                f"⚠️ Nepodařilo se vybrat divizi {DIVIZE_local} - vybírám první možnou divizi.")
            try:
                moznosti = page.locator(f"{SELECTOR_SELECT_DIVIZE} option")
                prvni_moznost = moznosti.nth(1).get_attribute("value")
                if prvni_moznost:
                    prvni_moznost_hodnota = moznosti.nth(1).text_content()
                    page.select_option(
                        SELECTOR_SELECT_DIVIZE, value=prvni_moznost)
                    print_and_log(
                        f"✅ Zvolena první dostupná divize: {prvni_moznost_hodnota}")
                    DIVIZE_local = prvni_moznost_hodnota
            except Exception as inner_e:
                print_and_log(
                    f"❌ Nepodařilo se vybrat první možnou divizi:\n{inner_e}")
                return False

        # Výběr squadu a ošetření plného/neexistujícího squadu
        # Skript zkusí postupně registraci do squadu 1 až 100. Pokud nenajde ani radio pro 100. squad, tato část kódu vrátí False a jede se znovu :).
        try:
            page.wait_for_selector(SELECTOR_SQUAD, timeout=1000)
            page.click(SELECTOR_SQUAD)
        except Exception as e:
            print_and_log(f"⚠️ Nepodařilo se vybrat squad {SQUAD}:\n{e}")
            success = False
            for squad_oprava in range(1, 101):
                try:
                    loc = page.locator(f"#squad-{squad_oprava}")
                    if loc.count() == 0:
                        continue  # squad v DOM vůbec není

                    print_and_log(f"⚠️ Zkouším zvolit squad {squad_oprava}.")
                    loc.click()
                    page.click(f"#squad-{squad_oprava}")
                    # krátké čekání na propsání stavu
                    page.wait_for_timeout(50)

                    checked = False
                    checked = loc.is_checked()

                    if checked:
                        print_and_log(f"✅ Zvolen squad {squad_oprava}.")
                        SQUAD_local = str(squad_oprava)
                        success = True
                        break
                    else:
                        print_and_log(
                            f"ℹ️ Squad {squad_oprava} se neoznačil – zkouším další.")
                except Exception as inner_e1:
                    print_and_log(
                        f"ℹ️ Squad {squad_oprava} nelze zvolit:\n{inner_e1}")
                    continue

            if not success:
                print_and_log(
                    f"❌ Nepodařilo se zvolit žádný squad v rozsahu od 1 do 100.")
                return False

        # Zaškrtnutí souhlasu s GDPR
        try:
            page.check(SELECTOR_CHECKBOX_GDPR)
        except Exception as e:
            print_and_log(f"❌ Nepodařilo se zaškrtnout souhlas s GDPR:\n{e}")
            return False

        # Uložení údajů ze závodu do globálních proměnných pro odeslání na mail.
        try:
            datum_zavodu = page.inner_text(SELECTOR_DATUM, timeout=2000)
        except Exception as e:
            print_and_log(f"⚠️ Nepodařilo se získat datum závodu:\n{e}")
            datum_zavodu = "neznámé datum"

        try:
            nazev_zavodu = page.inner_text(SELECTOR_NAZEV, timeout=2000)
        except Exception as e:
            print_and_log(f"⚠️ Nepodařilo se získat název závodu:\n{e}")
            nazev_zavodu = "neznámý název"

        # Čekání a odeslání registrace v náhodném intervalu + uložení času kliknutí do globální proměnné
        if RANDOM_WAIT and pokus == 1:
            delay = random.uniform(2, 3)
            print_and_log(f"ℹ️ Čekám {delay:.2f} sekundy...")
            time.sleep(delay)

        # Odeslání registrace a uložení času odeslání do proměnné k použití v logu.

        try:
            page.wait_for_selector(SELECTOR_TLACITKO_REGISTRACE, timeout=2000)
            page.click(SELECTOR_TLACITKO_REGISTRACE)
        except Exception as e:
            print_and_log(
                f"❌ Nepodařilo se kliknout na tlačítko registrace:\n{e}")
            return False
        finished = datetime.now()

        # Kontrola, že registrace proběhla (zobrazila se stránka e shrnutím registrace)
        max_wait = 8  # vteřin
        start_time = time.time()
        while not page.url.startswith(REG_URL):
            if page.url.endswith(r"#regform"):
                fatal_error = True
                print_and_log(f"❌ V konfiguračním souboru data.py je pravděpodobně chyba. Web LOS se po kliknutí na tlačítko registrace vrací zpět na formulář a registraci nepotvrzuje. Zkontroluj, zda například hodnoty None, True a False nejsou v uvozovkách.")
                return False
            if time.time() - start_time > max_wait:
                print_and_log(
                    f"❌ Registrace pravděpodobně selhala – URL se nezměnila do {max_wait} sekund.\nAktuální URL: {page.url}")
                return False
            time.sleep(0.1)

        print_and_log(
            f"✅ Registrace na závod {nazev_zavodu} - {datum_zavodu} dokončena.")

    # Informuje přítelkyni o datu a názvu závodu + o tom, že ji závodník miluje.
    if PRITELKYNE:
        try:
            informuj_pritelkyni()
        except Exception as e:
            print_and_log(f"❌ Nepodařilo se informovat přítelkyni:\n{e}")

    # Vytvoří ics k odeslání emailem
    try:
        ics_file = vytvor_ics.main()
        print_and_log("✅ .ics soubor vytvořen.")
    except Exception as e:
        print_and_log(f"❌ Nepodařilo se vytvořit .ics soubor:\n{e}")

    # Pošle závodníkovi shrnutí úspěšné reistrace a textový log.
    try:
        posli_email()
    except Exception as e:
        print_and_log(f"❌ Nepodařilo se poslat shrnutí na email:\n{e}")

    return True


def posli_email() -> None:
    """Pošle závodníkovi email se shrnutím úspěšné registrace."""
    msg = EmailMessage()
    msg['Subject'] = '✅ LOS Registrace proběhla'
    msg['From'] = EMAIL_U
    msg['To'] = LOGIN
    msg.set_content(
        f"""Registrace na závod proběhla úspěšně. V příloze nalezneš záznam o průběhu registrace a .ics událost pro uložení do kalendáře.

Závod: {nazev_zavodu}
Datum závodu: {datum_zavodu}

Čas odeslání formuláře: {finished}

{get_summary()
            .replace("\n\n", "\n")
            .replace("    ", "")
            .replace("registraci:", "registraci:\n")}"""
    )

    with open(f"logs/log-{POKUS_TIME}.txt", "rb") as f:
        msg.add_attachment(f.read(), maintype="text",
                           subtype="plain", filename=f"Registrace LOG.txt")

    if ics_file:
        with open(ics_file, "rb") as f:
            msg.add_attachment(f.read(), maintype="text", subtype="calendar",
                               filename="zavod.ics", disposition="attachment", params={"method": "REQUEST"})

    # Odeslání e-mailu
    if odeslat(msg):
        print_and_log(f"✅ Shrnutí odesláno na {LOGIN}.")


def posli_error(pokusy: int) -> None:
    """Funkce pro odeslání oznámení o chybě na závodníkův email"""
    msg = EmailMessage()
    msg['Subject'] = '❌ LOS Registrace neproběhla'
    msg['From'] = EMAIL_U
    msg['To'] = LOGIN
    msg.set_content(
        f"""❌ Registrace na závod neproběhla úspěšně.

❌ Při registraci došlo k fatální chybě nebo nebyl úspěšný ani jeden z {pokusy} provedených pokusů. Viz přiložený log.

{get_summary()
            .replace("\n\n", "\n")
            .replace("    ", "")
            .replace("registraci:", "registraci:\n")}"""
    )

    with open(f"logs/log-{POKUS_TIME}.txt", "rb") as f:
        msg.add_attachment(f.read(), maintype="text",
                           subtype="plain", filename=f"Registrace LOG.txt")

    # Odeslání e-mailu
    if odeslat(msg):
        print_and_log(f"✅ Shrnutí odesláno na {LOGIN}.")


def informuj_pritelkyni() -> None:
    """Informuje přřítelkyni o názvu a dni závodu a o citech, které pro ni závodník chová."""
    msg = EmailMessage()
    msg['Subject'] = '🔫 Tvůj kluk pojede na závod'
    msg['From'] = EMAIL_U
    msg['To'] = PRITELKYNE
    msg.set_content(
        f"""Tvůj kluk se {PRITELKYNE_INSERT_1}právě přihlásil na závod {nazev_zavodu} ({URL}). Datum závodu: {datum_zavodu}.\n\nBude potřebovat držet palce.\n{PRITELKYNE_INSERT_2}\n{PRITELKYNE_INSERT_3}\n\n(Automaticky generovaný email)""")

    # Odeslání e-mailu

    if odeslat(msg):
        print_and_log(f"✅ {JMENO_PRITELKYNE} informována.")


def informuj_o_zacatku() -> None:
    """Informuje závodníka o začátku skriptu"""
    msg = EmailMessage()
    msg['Subject'] = '🔫 Registrační skript spuštěn'
    msg['From'] = EMAIL_U
    msg['To'] = LOGIN
    msg.set_content(
        f"""Registrační skript na závod na závod {URL} byl spuštěn.\n\n{STALE_BEZI_MINUT} minut před začátkem registrace ({datetime.strptime(DATUM_CAS_REGISTRACE, "%Y-%m-%d %H:%M:%S") - timedelta(minutes=STALE_BEZI_MINUT)}) očekávej potvrzovací email, že skript stále běží.\n\n\n(Automaticky generovaný email)""")

    # Odeslání e-mailu

    if odeslat(msg):
        print_and_log(
                        "✅ Odeslal jsem notifikační email o tom, že skript byl spuštěn.")


def stale_bezi() -> None:
    """Informuje závodníka o běhu skriptu."""
    msg = EmailMessage()
    msg['Subject'] = '🔫 Registrační skript stále běží'
    msg['From'] = EMAIL_U
    msg['To'] = LOGIN
    msg.set_content(
        f"""Registrační skript na závod na závod {URL} v pořádku běží.\n\n\n(Automaticky generovaný email)""")

    # Odeslání e-mailu

    odeslat(msg)


def odeslat(msg: str) -> bool:
    try:
        if EMAIL_PROVIDER not in EMAIL_PROVIDERS:
            print_and_log(f"❌ Poskytovatel emailových služeb {EMAIL_PROVIDER} není implementován. Email nebyl odeslán.")
            return False
        elif EMAIL_PROVIDER == "PROTON":
            with smtplib.SMTP('127.0.0.1', 1025) as smtp:
                smtp.login(EMAIL_U, EMAIL_P)
                smtp.send_message(msg)
            return True
        elif EMAIL_PROVIDER == "PROTON-TOKEN":
            with smtplib.SMTP('smtp.protonmail.ch', 587) as smtp:
                smtp.starttls()
                smtp.login(EMAIL_U, EMAIL_P)
                smtp.send_message(msg)
            return True
        elif EMAIL_PROVIDER == "GMAIL":
            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
                smtp.login(EMAIL_U, EMAIL_P)
                smtp.send_message(msg)
            return True
        else:
            return False
    except Exception as e:
        print_and_log(f"Chyba: {e}")
        return False


def run():
    # Funkce spouští registraci stále dokola, dokud registrace nebude úspěšná, dokud nedojde k fatální chybě nebo dokud nebude dosažen maximální stanovený počet pokusů.
    # Fatální chybou se rozumí špatné přihlašovací údaje, špatný formát data a času nebo špatná URL závodu.

    # POKUS_TIME je konstanta, která se používá pouze pro název souboru s logem.
    global POKUS_TIME
    POKUS_TIME = datetime.now().replace(microsecond=0).strftime("%Y-%m-%d_%H-%M-%S")
    cislo_pokusu = 1
    while cislo_pokusu <= LIMIT:
        if cislo_pokusu != 1:
            print_and_log("❌ Pokus o registraci selhal. Zkouším znovu...")
        print_and_log(f"ℹ️ Pokus o registraci č. {cislo_pokusu} z {LIMIT}")
        if registrace(cislo_pokusu) or fatal_error:
            break
        cislo_pokusu += 1
    if cislo_pokusu > LIMIT:
        print_and_log(
            f"❌ Registrace selhala i po {LIMIT} pokusech. Skript končí.")
        try:
            posli_error(cislo_pokusu-1)
        except Exception as e:
            print_and_log(f"❌ Nepodařilo se poslat shrnutí na email:\n{e}")
    if fatal_error:
        print_and_log(
            f"❌ Registrace selhala - fatální chyba. Vzhledem k její povaze nemá smysl pokus opakovat. Skript končí.")
        try:
            posli_error(cislo_pokusu-1)
        except Exception as e:
            print_and_log(f"❌ Nepodařilo se poslat shrnutí na email:\n{e}")


def opravit_konfiguraci():
    global CLENSKE_ID
    global PRITELKYNE
    global POZNAMKA
    global SQUAD
    
    if CLENSKE_ID == "None":
        CLENSKE_ID = None
    if isinstance(SQUAD, str):
        try:
            SQUAD = int(SQUAD)
        except Exception as e:
            print_and_log("❌ Nepodařilo se převést SQUAD na INT.")
    if PRITELKYNE == "None":
        PRITELKYNE = None
    if POZNAMKA == "None":
        POZNAMKA = None


if __name__ == "__main__":
    try:
        opravit_konfiguraci()
        run()
    except KeyboardInterrupt:
        print("\nProgram ukončen uživatelem.")
    except Exception as e:
        print(f"❌ Neočekávaná chyba - Prosím, pošli screenshot na debug@krystofklika.cz \n {e}")
