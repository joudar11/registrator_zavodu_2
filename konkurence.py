import re
import os
from datetime import datetime, date
import subprocess
import webbrowser
from pathlib import Path
import sys

from playwright.sync_api import sync_playwright

from data import (
    JMENO, DIVIZE, URL, LOGIN, HESLO
)

if len(sys.argv) == 4:
    JMENO = sys.argv[1]
    DIVIZE = sys.argv[2]
    URL = sys.argv[3]

CREATE = True
FOLDER = "konkurence"
TIME = datetime.now().replace(microsecond=0).strftime("%Y-%m-%d_%H-%M-%S")
LOGNAME = f"konkurence-{URL.split("/")[-1]}-{JMENO}"
KONZOLE = False
FIRST_RUN = True
HEADER_LEN = None

DIVIZE_KONVERZE = {"Pistole": "Pi", "Optik/Pistole": "OptPi",
                   "PDW": "PDW"}  # Převod z divize DATA na tento skript
DIVIZE_V_POHARU = {"Pi": "Pi", "OptPi": "Opt", "PDW": "PDW"}

DIVIZE = DIVIZE_KONVERZE[DIVIZE]


today = date.today()
datum_zari = date(today.year, 9, 1)

if today >= datum_zari:
    POHAR1 = int(datetime.now().year) + 1
else:
    POHAR1 = int(datetime.now().year)


POHAR2 = POHAR1 - 1
POHAR3 = POHAR1 - 2

URL_CUP3 = f"https://www.loslex.cz/cup/{int(datetime.now().year) - 2024}"
URL_CUP2 = f"https://www.loslex.cz/cup/{int(datetime.now().year) - 2024 + 1}"
URL_CUP1 = f"https://www.loslex.cz/cup/{int(datetime.now().year) - 2024 + 2}"
SELECTOR_LOGIN_FORM = r"body > div.min-h-screen.bg-gray-100.dark\:bg-gray-900 > nav > div.max-w-7xl.mx-auto.px-4.md\:px-6.lg\:px-8 > div > div.hidden.space-x-1.items-center.md\:-my-px.md\:ml-10.md\:flex > button.inline-flex.items-center.px-1.border-b-2.border-transparent.text-sm.font-medium.leading-5.text-gray-500.dark\:text-gray-400.hover\:text-gray-700.dark\:hover\:text-gray-300.hover\:border-gray-300.dark\:hover\:border-gray-700.focus\:outline-none.focus\:text-gray-700.dark\:focus\:text-gray-300.focus\:border-gray-300.dark\:focus\:border-gray-700.transition.duration-150.ease-in-out"
SELECTOR_LOGIN_BUTTON = r"body > div.fixed.inset-0.overflow-y-auto.px-4.py-6.sm\:px-0.z-2000 > div.mb-6.bg-white.dark\:bg-gray-800.rounded-lg.overflow-hidden.shadow-xl.transform.transition-all.sm\:w-full.sm\:max-w-md.sm\:mx-auto > div > form > div.flex.items-center.justify-end.mt-4 > button"
SELECTOR_USER = r"#login"
SELECTOR_PASS = r"#password"
SELECTOR_DIVIZE_POHAR = f"#division-{DIVIZE_V_POHARU[DIVIZE]}-tab"

jmena = []
vysledky = []


def smazat_log() -> None:
    global FOLDER
    global LOGNAME
    filename = f"{LOGNAME}.html"
    path = os.path.join(FOLDER, filename)
    if os.path.isfile(path):
        os.remove(path)
        print(f"Soubor '{path}' byl smazán.")
    return


def print_konzole(content: str) -> None:
    if KONZOLE:
        print(content)


def statistika() -> None:
    global FIRST_RUN
    global HEADER_LEN
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(URL)
        print_and_log("")
        if FIRST_RUN:
            vytvoreno = datetime.now()
            vytvoreno_f = vytvoreno.strftime("%d.%m.%Y %H:%M")
            print_konzole(f'{'Závod:':<14}{page.title()} - {URL}')
            only_log(f'{'Závod:':<14}<a target="_blank" href="{URL}">{page.title()}</a>')
            print_and_log(f"{'Divize:':<14}{DIVIZE}")
            print_and_log(f"{'Vytvořeno:':<14}{vytvoreno_f}\n")
            only_log(f'<span style="background-color: #cccccc;">Závodník, který se nezůčastnil žádného pohárovéno závodu ve vybrané sezoně</span>')
            only_log(f'<span style="background-color: #fab1a0;">Závodník, který se v poháru ve vybrané sezoně umístil na jednom z prvních 3 míst</span>')
            only_log(f'<span style="background-color: #ffeaa7;">Vybraný závodník - {JMENO} </span>')
            only_log("")
        else:
            print_and_log("=" * HEADER_LEN)
            print_and_log("")
        print_konzole(f"{'Pohár:':<14}{POHAR1} - {URL_CUP1}")
        only_log(f'{'Pohár:':<14}<a target="_blank" href="{URL_CUP1}">{POHAR1}</a>')
        print_and_log("")

        page.click(SELECTOR_LOGIN_FORM)
        page.wait_for_selector(SELECTOR_USER)
        page.wait_for_selector(SELECTOR_PASS)
        page.fill(SELECTOR_USER, LOGIN)
        page.fill(SELECTOR_PASS, HESLO)
        page.wait_for_selector(SELECTOR_LOGIN_BUTTON)
        page.click(SELECTOR_LOGIN_BUTTON)

        page.wait_for_selector(f'[title="{DIVIZE}"]')
        els = page.locator(f'div[title="{DIVIZE}"]:visible')

        for i in range(els.count()):
            el = els.nth(i)
            # 1) první řádek = celé jméno (username bývá na dalším řádku)
            lines = el.inner_text().splitlines()
            raw_name = lines[0].strip() if lines else ""

            # 2) ignoruj (MZ)
            if " (MZ)" in raw_name:
                continue

            # 3) normalizace mezer a neviditelných znaků
            name = raw_name.replace("\u00A0", " ").replace("\u200b", "")
            name = " ".join(name.split())

            if name and (name != JMENO):
                jmena.append(name)

        jmena.append(JMENO)
        pohar(URL_CUP1, page)
        vypis()
        try:
            porovnat(POHAR1)
        except TypeError:
            pass
        vynuluj()
        FIRST_RUN = False
        print_and_log("")
        print_and_log("=" * HEADER_LEN)
        print_and_log("")
        pohar(URL_CUP2, page)
        print_konzole(f"{'Pohár:':<14}{POHAR2} - {URL_CUP2}")
        only_log(f'{'Pohár:':<14}<a href="{URL_CUP2}">{POHAR2}</a>')
        print_and_log("")
        vypis()
        try:
            porovnat(POHAR2)
        except TypeError:
            pass
        vynuluj()
        print_and_log("")
        print_and_log("=" * HEADER_LEN)
        print_and_log("")
        pohar(URL_CUP3, page)
        print_konzole(f"{'Pohár:':<14}{POHAR3} - {URL_CUP3}")
        only_log(f'{'Pohár:':<14}<a href="{URL_CUP3}">{POHAR3}</a>')
        print_and_log("")
        vypis()
        try:
            porovnat(POHAR3)
        except TypeError:
            pass
        browser.close()


def vypis():
    global vysledky
    global HEADER_LEN
# seřazení od nejlepšího
    vysledky.sort(key=lambda x: (
        x[-1] is None, -(x[-1] if x[-1] is not None else float("-inf"))))

    # výpis
    header = f"{'#':>3} | {
        '# POHÁR':>8} | {
        'JMÉNO':<35} | {
        '% POHÁR':>10} | {
            'ZÁVODY':>7} | {
                'PRŮMĚR %':>9}"
    print_and_log(header)
    print_and_log("-" * len(header))
    HEADER_LEN = len(header)

    i = 1
    for rank, name, pct, races, avg in vysledky:
        SPAN_BEGIN = ''
        SPAN_END = ''
        if name == JMENO:
            SPAN_BEGIN = '<span style="background-color: #ffeaa7;">'
            SPAN_END = '</span>'
        if (rank in range(1, 4)) and (name != JMENO):
            SPAN_BEGIN = '<span style="background-color: #fab1a0;">'
            SPAN_END = '</span>'
        if (rank == None) and (name != JMENO):
            SPAN_BEGIN = '<span style="background-color: #cccccc;">'
            SPAN_END = '</span>'
        if rank is None:
            print_konzole(
                f"{'-':>3} | {
                    '–':>8} | {
                    name:<35} | {
                    '–':>10} | {
                    races:>7} | {
                    '–':>9}")
            only_log(
                f"{SPAN_BEGIN}{'-':>3} | {
                    '–':>8} | {
                    name:<35} | {
                    '–':>10} | {
                    races:>7} | {
                    '–':>9}{SPAN_END}")
        else:
            pct_out = f"{pct:.2f}%" if pct is not None else "–"
            avg_out = f"{avg:.2f}%" if avg is not None else "–"
            print_konzole(
                f"{i:>3} | {
                    rank:>8} | {
                    name:<35} | {
                    pct_out:>10} | {
                    races:>7} | {
                    avg_out:>9}")
            only_log(
                f"{SPAN_BEGIN}{i:>3} | {
                    rank:>8} | {
                    name:<35} | {
                    pct_out:>10} | {
                    races:>7} | {
                    avg_out:>9}{SPAN_END}")
        i += 1
    pass


def pohar(URL_z, page):
    # pohar

    page.goto(URL_z)
    page.click(SELECTOR_DIVIZE_POHAR)

    def _clean_percent(pct_raw: str):
        s = pct_raw.replace("%", "").strip()
        if s.count(".") > 1:
            parts = s.split(".")
            s = "".join(parts[:-1]) + "." + parts[-1]
        s = s.replace(",", "").strip()
        try:
            return float(s)
        except BaseException:
            return None

    # jen aktivní (viditelný) panel
    visible_panel = page.locator(
        f'div[role="tabpanel"]#division-{DIVIZE_V_POHARU[DIVIZE]}:visible')

    for name in jmena:
        if " (MZ)" in name:
            continue
        # přesná shoda jména (viditelná buňka)
        name_re = re.compile(rf'^\s*{re.escape(name)}\s*$', re.IGNORECASE)
        name_cell = visible_panel.locator(
            "div.w-36:visible", has_text=name_re).first
        if name_cell.count() == 0:
            vysledky.append((None, name, None, 0, None))
            continue

        # řádek s rankem/jménem/procenty
        row = name_cell.locator(
            "xpath=ancestor::div[contains(@class,'border-gray-400')][1]").first

        # pořadí
        rank_txt = row.locator(
            "div.w-5:visible").first.text_content().strip().rstrip(".")
        try:
            rank = int(rank_txt)
        except BaseException:
            rank = None

        # procenta v poháru
        pct_loc = name_cell.locator(
            "xpath=following-sibling::div[contains(@class,'w-20') and contains(@class,'text-right')][1]"
        )
        if pct_loc.count() == 0:
            pct_loc = row.locator("div.w-20.text-right:visible").first
        pct_raw = pct_loc.text_content().strip() if pct_loc.count() > 0 else ""
        pct = _clean_percent(pct_raw)

        # všechny závody – procenta z každého zeleného boxu
        next_row = row.locator(
            "+ div.flex.flex-row.gap-x-1.justify-center:visible")
        race_percents = []
        if next_row.count() > 0:
            for box in next_row.locator(
                    "div.border.rounded-md.p-1.w-20.cursor-help:visible").all():
                val_raw = box.locator(
                    "div.text-center").first.text_content().strip()
                val = _clean_percent(val_raw)
                if val is not None:
                    race_percents.append(val)

        race_count = len(race_percents)
        avg = round(
            sum(race_percents) / race_count,
            2) if race_count > 0 else None

        vysledky.append((rank, name, pct, race_count, avg))


def muj_prumer() -> float:
    global vysledky
    for record in vysledky:
        if record[1] == JMENO:
            return record[-1]


def porovnat(sezona: str) -> None:
    global FIRST_RUN
    if FIRST_RUN:
        singular = "je"
        plural = "mají"
    else:
        singular = "byl"
        plural = "měli"
    if vysledky[0][1] == JMENO:
        print_and_log("\nVybraný závodník je nejlepším přihlášeným závodníkem v tomto závodě!")
        return
    MUJ_PRUMER = muj_prumer()
    if MUJ_PRUMER is None:
        return
    print_and_log(
        f"\nNejlepší závodník {singular} v průměru v sezoně {sezona} o {(float(vysledky[0][-1]) - MUJ_PRUMER):.2f}% lepší než vybraný závodník.")
    lepsich_zavodniku = 0
    for record in vysledky:
        if record[1] != JMENO:
            lepsich_zavodniku += 1
        else:
            break
    print_and_log(
        f"Závodníků, kteří v sezoně {sezona} {plural} lepší průměrné výsledky než vybraný závodník: {lepsich_zavodniku}")


def print_and_log(action: str) -> None:
    global CREATE
    """Zprávu předanou argumentem vytiskne do konzole a zároveň uloží na konec logu."""
    print_konzole(action)
    try:
        os.makedirs(FOLDER, exist_ok=True)
    except Exception as e:
        print(f"❌ Nelze vytvořit složku {FOLDER}:\n{e}")
        return

    # Zápis do logu
    with open(f"{FOLDER}/{LOGNAME}.html", "a", encoding="utf-8") as f:
        if CREATE:
            f.write(f'<meta charset="UTF-8">\n<pre>')
            CREATE = False
        f.write(f"{action}<br>")


def only_log(action: str) -> None:
    global CREATE
    """Zprávu předanou argumentem uloží na konec logu."""
    try:
        os.makedirs(FOLDER, exist_ok=True)
    except Exception as e:
        print(f"❌ Nelze vytvořit složku {FOLDER}:\n{e}")
        return

    # Zápis do logu
    with open(f"{FOLDER}/{LOGNAME}.html", "a", encoding="utf-8") as f:
        if CREATE:
            f.write(f'<meta charset="UTF-8">\n<pre>')
            CREATE = False
        f.write(f"{action}<br>")


def vynuluj() -> None:
    global vysledky
    vysledky = []
    return


def run() -> None:
    smazat_log()
    statistika()
    with open(f"{FOLDER}/{LOGNAME}.html", "a", encoding="utf-8") as f:
        f.write(f'</pre>')
    webbrowser.open(Path(f"{FOLDER}/{LOGNAME}.html").resolve().as_uri())
#    if input(f"\nPřeješ si registrovat? (Y/N): ") == "Y".lower():
#        print("Spouštím registrační skript...")
#        subprocess.Popen(["start", "cmd", "/k", "python main.py"], shell=True)


if __name__ == "__main__":
    run()
