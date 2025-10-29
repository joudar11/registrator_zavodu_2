import re
import os
from datetime import datetime, date, timedelta
import webbrowser
from pathlib import Path
import sys
from ftplib import FTP_TLS

from playwright.sync_api import sync_playwright

from data import (
    JMENO, DIVIZE, URL, LOGIN, HESLO
)


ftp_script = Path(__file__).parent / "ftp_konkurence.py"
if ftp_script.exists():
    from ftp_konkurence import(
        host, username, password, remote_dir, visit
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
LAST12_SUMS = {}        # ### NEW: jméno -> (součet_procent, počet_závodů)
CUTOFF_12M = date.today() - timedelta(days=365)  # ### NEW: hranice 12 měsíců

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

if today >= datum_zari:
    POHAR1_U = int(datetime.now().year)
else:
    POHAR1_U = int(datetime.now().year) - 1

URL_CUP3 = f"https://www.loslex.cz/cup/{POHAR1_U - 2024}"
URL_CUP2 = f"https://www.loslex.cz/cup/{POHAR1_U - 2024 + 1}"
URL_CUP1 = f"https://www.loslex.cz/cup/{POHAR1_U - 2024 + 2}"
SELECTOR_LOGIN_FORM = r"body > div.min-h-screen.bg-gray-100.dark\:bg-gray-900 > nav > div.max-w-7xl.mx-auto.px-4.md\:px-6.lg\:px-8 > div > div.hidden.space-x-1.items-center.md\:-my-px.md\:ml-10.md\:flex > button.inline-flex.items-center.px-1.border-b-2.border-transparent.text-sm.font-medium.leading-5.text-gray-500.dark\:text-gray-400.hover\:text-gray-700.dark\:hover\:text-gray-300.hover\:border-gray-300.dark\:hover\:border-gray-700.focus\:outline-none.focus\:text-gray-700.dark\:focus\:text-gray-300.focus\:border-gray-300.dark\:focus\:border-gray-700.transition.duration-150.ease-in-out"
SELECTOR_LOGIN_BUTTON = r"body > div.fixed.inset-0.overflow-y-auto.px-4.py-6.sm\:px-0.z-2000 > div.mb-6.bg-white.dark\:bg-gray-800.rounded-lg.overflow-hidden.shadow-xl.transform.transition-all.sm\:w-full.sm\:max-w-md.sm\:mx-auto > div > form > div.flex.items-center.justify-end.mt-4 > button"
SELECTOR_USER = r"#login"
SELECTOR_PASS = r"#password"
SELECTOR_DIVIZE_POHAR = f"#division-{DIVIZE_V_POHARU[DIVIZE]}-tab"

jmena = []
vysledky = []

def upload_ftps(host: str, username: str, password: str, remote_dir: str) -> None:
    """
    Nahraje hotový HTML soubor na FTPS server (FTP přes TLS).

    Args:
        host: adresa FTP serveru (např. "ftp.krystofklika.cz")
        username: uživatelské jméno
        password: heslo
        remote_dir: vzdálený adresář (např. "/public_html/konkurence")
    """

    local_path = Path(f"{FOLDER}/{LOGNAME}.html").resolve()
    if not local_path.exists():
        print(f"❌ Soubor {local_path} neexistuje – upload zrušen.")
        return

    print(f"🔗 Připojuji se k FTPS serveru {host} ...")
    try:
        ftps = FTP_TLS()
        ftps.connect(host, 21, timeout=15)  # port 990 pro implicitní FTPS
        ftps.auth()
        ftps.login(username, password)
        ftps.prot_p()  # přepne přenos do šifrovaného režimu

        try:
            ftps.cwd(remote_dir)
        except Exception:
            # vytvoření složky pokud neexistuje
            dirs = remote_dir.strip("/").split("/")
            path = ""
            for d in dirs:
                path += f"/{d}"
                try:
                    ftps.cwd(path)
                except Exception:
                    ftps.mkd(path)
                    ftps.cwd(path)

        with open(local_path, "rb") as f:
            ftps.storbinary(f"STOR {local_path.name}", f)

        print(f"✅ Soubor {local_path.name} byl úspěšně nahrán na {host}:{remote_dir}")
        ftps.quit()
    except Exception as e:
        print(f"❌ Chyba při uploadu přes FTPS: {e}")


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
    global LAST12_SUMS
    LAST12_SUMS = {}

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(URL)
        print_and_log("")
        if FIRST_RUN:
            vytvoreno = datetime.now()
            vytvoreno_f = vytvoreno.strftime("%d. %m. %Y %H:%M")
            if ftp_script.exists():
                only_log(f'{"Přehled:":<18}<a target="_blank" href="{visit}">{visit}</a>')
            print_konzole(f'{'Závod:':<18}{page.title()} - {URL}')
            only_log(f'{'Závod:':<18}<a target="_blank" href="{URL}">{page.title()}</a>')
            print_and_log(f"{'Divize:':<18}{DIVIZE}")
            print_and_log(f"{'Vytvořeno:':<18}{vytvoreno_f}\n")
            only_log(f'<span style="color: #b0b0b0;">Závodník, který se nezůčastnil žádného pohárovéno závodu v hodnoceném období</span>')
            only_log(f'<span style="background-color: #fab1a0;">Závodník, který se v poháru ve vybrané sezoně umístil na jednom z prvních 3 míst</span>')
            if JMENO:
                only_log(f'<span style="background-color: #ffeaa7;">Vybraný závodník - {JMENO} </span>')
            only_log("")
        else:
            print_and_log("=" * HEADER_LEN)
            print_and_log("")
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

            if name:
                jmena.append(name)

        if JMENO and (JMENO not in jmena):
            jmena.append(JMENO)
        pohar(URL_CUP1, page, zahrnout_do_12m=True)
        vypis(POHAR1, URL_CUP1)
        try:
            porovnat()
        except TypeError:
            pass
        vynuluj()
        FIRST_RUN = False
        print_and_log("")
        print_and_log("=" * HEADER_LEN)
        print_and_log("")
        pohar(URL_CUP2, page, zahrnout_do_12m=True)
        print_and_log("")
        vypis(POHAR2, URL_CUP2)
        try:
            porovnat()
        except TypeError:
            pass
        vynuluj()
        print_and_log("")
        print_and_log("=" * HEADER_LEN)
        print_and_log("")
        pohar(URL_CUP3, page)
        print_and_log("")
        vypis(POHAR3, URL_CUP3)
        try:
            porovnat()
        except TypeError:
            pass

        vynuluj()

        vypis_poslednich_12_mesicu()
        try:
            porovnat(True)
        except TypeError:
            pass

        only_log("\n\n\n\n\n\n")

        browser.close()


def vypis(pohar: str, pohar_url: str):
    global vysledky
    global HEADER_LEN
    koeficient = float(0)
    print_konzole(f"{'Hodnocené období:':<18}{pohar} - {pohar_url}")
    only_log(f'{'Hodnocené období:':<18}<a href="{pohar_url}">Pohár {pohar}</a>')
    print_and_log("")
# seřazení od nejlepšího
    vysledky.sort(key=lambda x: (
        x[-1] is None, -(x[-1] if x[-1] is not None else float("-inf"))))

    # výpis
    header = f"{'#':>3} | {
        '# POHÁR':>8} | {
        'JMÉNO':<35} | {
        '% POHÁR':>10} | {
            'ZÁVODY':>7} | {
                'PRŮMĚR %':>9} | {
                'PROJEKCE %':>11}"
    print_and_log(header)
    print_and_log("-" * len(header))
    HEADER_LEN = len(header)

    i = 1
    for rank, name, pct, races, avg in vysledky:
        SPAN_BEGIN = ''
        SPAN_END = ''
        if i == 1:
            koeficient = 100/avg
            projekce = 100
        if name == JMENO:
            SPAN_BEGIN = '<span style="background-color: #ffeaa7;">'
            SPAN_END = '</span>'
        elif (rank in range(1, 4)):
            if not (i % 2 == 0):
                SPAN_BEGIN = '<span style="background-color: #fab1a0;">'
                SPAN_END = '</span>'
            else:
                SPAN_BEGIN = '<span style="background-color: #f7876e;">'
                SPAN_END = '</span>'
        elif (races == 0):
            SPAN_BEGIN = '<span style="color: #b0b0b0;">'
            SPAN_END = '</span>'
        elif (i % 2 == 0):
            SPAN_BEGIN = '<span style="background-color: #f0f0f0;">'
            SPAN_END = '</span>'
        if rank is None:
            print_konzole(
                f"{'-':>3} | {
                    '–':>8} | {
                    name:<35} | {
                    '–':>10} | {
                    races:>7} | {
                    '–':>9} | {
                    '–':>11}")
            only_log(
                f"{SPAN_BEGIN}{'-':>3} | {
                    '–':>8} | {
                    name:<35} | {
                    '–':>10} | {
                    races:>7} | {
                    '–':>9} | {
                    '–':>11}{SPAN_END}")
        else:
            projekce = avg*koeficient
            pct_out = f"{pct:.2f}%" if pct is not None else "–"
            avg_out = f"{avg:.2f}%" if avg is not None else "–"
            projekce_out = f"{projekce:.2f}%" if projekce is not None else "–"
            print_konzole(
                f"{i:>3} | {
                    rank:>8} | {
                    name:<35} | {
                    pct_out:>10} | {
                    races:>7} | {
                    avg_out:>9} | {
                    projekce_out:>11}")
            only_log(
                f"{SPAN_BEGIN}{i:>3} | {
                    rank:>8} | {
                    name:<35} | {
                    pct_out:>10} | {
                    races:>7} | {
                    avg_out:>9} | {
                    projekce_out:>11}{SPAN_END}")
        i += 1
    pass

def vypis_poslednich_12_mesicu():
    """Vytiskne '12M' tabulku: souhrn všech procent z posledních 12 měsíců přes aktuální a minulý pohár."""
    global vysledky
    global jmena
    koeficient = float(0)
    # připrav výsledky: (rank, name, pct, races, avg) — rank i pct nejsou relevantní → None
    vysledky = []
    for name in jmena:
        s, c = LAST12_SUMS.get(name, (0.0, 0))
        avg = round(s / c, 2) if c > 0 else None
        vysledky.append((None, name, None, c, avg))

    # stejné řazení jako ve vypis(): podle avg desc, None až nakonec
    vysledky.sort(key=lambda x: (x[-1] is None, -(x[-1] if x[-1] is not None else float("-inf"))))

    # hlavička v témže stylu (ponecháme '# POHÁR' – naplníme '12M' v řádcích)
    header = f"{'#':>3} | {
        'JMÉNO':<35} | {
            'ZÁVODY':>7} | {
                'PRŮMĚR %':>9} | {
                'PROJEKCE %':>11}"
    print_and_log("")
    print_and_log(f"{"=" * len(header)}{"\n\n"}")
    print_konzole(f'{'Hodnocené období:':<18} {CUTOFF_12M:%d. %m. %Y} - {date.today():%d. %m. %Y}')
    only_log(f'{'Hodnocené období:':<18} {CUTOFF_12M:%d. %m. %Y} - {date.today():%d. %m. %Y}')
    print_and_log("")
    print_and_log(header)
    print_and_log("-" * len(header))

    i = 1
    for rank, name, pct, races, avg in vysledky:
        if i == 1:
            koeficient = 100/float(avg)
            projekce = 100
        SPAN_BEGIN = ''
        SPAN_END = ''
        if name == JMENO:
            SPAN_BEGIN = '<span style="background-color: #ffeaa7;">'
            SPAN_END = '</span>'
        elif (races == 0):
            SPAN_BEGIN = '<span style="color: #b0b0b0;">'
            SPAN_END = '</span>'
        elif (i % 2 == 0):
            SPAN_BEGIN = '<span style="background-color: #f0f0f0;">'
            SPAN_END = '</span>'
        if rank is None:
            # „# POHÁR“ = '12M', '% POHÁR' = '–' (nedává smysl)
            if i == 1:
                projekce = 100
            else:
                projekce = (avg * koeficient) if (avg is not None and koeficient is not None and i != 1) else None
            projekce_out = f"{projekce:.2f}%" if projekce is not None else "–"
            avg_out = f"{avg:.2f}%" if avg is not None else "–"
            rank = "–" if avg is None else i
            only_log(
                f"{SPAN_BEGIN}{rank:>3} | {
                    name:<35} | {
                    races:>7} | {
                    avg_out:>9} | {
                    projekce_out:>11}{SPAN_END}")
        else:
            # sem se nedostaneme; rank je u 12M vždy None
            pass
        i += 1


def pohar(URL_z, page, zahrnout_do_12m=False):  # ### CHANGED: nový parametr
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

    visible_panel = page.locator(
        f'div[role="tabpanel"]#division-{DIVIZE_V_POHARU[DIVIZE]}:visible')

    date_re = re.compile(r'(\d{1,2}\.\s*[\u00A0]?\d{1,2}\.\s*[\u00A0]?\d{4})')

    for name in jmena:
        if " (MZ)" in name:
            continue

        name_re = re.compile(rf'^\s*{re.escape(name)}\s*$', re.IGNORECASE)
        name_cell = visible_panel.locator("div.w-36:visible", has_text=name_re).first
        if name_cell.count() == 0:
            vysledky.append((None, name, None, 0, None))
            continue

        row = name_cell.locator("xpath=ancestor::div[contains(@class,'border-gray-400')][1]").first

        rank_txt = row.locator("div.w-5:visible").first.text_content().strip().rstrip(".")
        try:
            rank = int(rank_txt)
        except BaseException:
            rank = None

        pct_loc = name_cell.locator(
            "xpath=following-sibling::div[contains(@class,'w-20') and contains(@class,'text-right')][1]"
        )
        if pct_loc.count() == 0:
            pct_loc = row.locator("div.w-20.text-right:visible").first
        pct_raw = pct_loc.text_content().strip() if pct_loc.count() > 0 else ""
        pct = _clean_percent(pct_raw)

        next_row = row.locator("+ div.flex.flex-row.gap-x-1.justify-center:visible")
        race_percents = []
        if next_row.count() > 0:
            for box in next_row.locator("div.border.rounded-md.p-1.w-20.cursor-help:visible").all():
                # procento závodu
                val_raw = box.locator("div.text-center").first.text_content().strip()
                val = _clean_percent(val_raw)

                # datum závodu – vezmeme z celého boxu (pod procenty)
                datum = None
                try:
                    sources = [
                        box.inner_text() or "",
                        box.text_content() or "",
                        box.get_attribute("title") or "",
                        box.get_attribute("aria-label") or "",
                    ]
                    for src in sources:
                        m = date_re.search(src)
                        if m:
                            date_str = m.group(1).replace(" ", "").replace("\u00A0", "")
                            datum = datetime.strptime(date_str, "%d.%m.%Y").date()
                            break
                except BaseException:
                    datum = None

                if val is not None:
                    race_percents.append(val)

                    # agregace do „posledních 12M“ pokud:
                    # - je požadováno zahrnutí za tento pohár
                    # - a máme detekovaný datum v okně posledních 12 měsíců
                    if zahrnout_do_12m and (datum is not None) and (datum >= CUTOFF_12M):
                        s, c = LAST12_SUMS.get(name, (0.0, 0))
                        LAST12_SUMS[name] = (s + val, c + 1)

        race_count = len(race_percents)
        avg = round(sum(race_percents) / race_count, 2) if race_count > 0 else None

        vysledky.append((rank, name, pct, race_count, avg))



def muj_prumer() -> float:
    global vysledky
    for record in vysledky:
        if record[1] == JMENO:
            return record[-1]


def porovnat(M12 = False) -> None:
    if not JMENO:
        return
    global FIRST_RUN
    if FIRST_RUN or M12:
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
        f"\nNejlepší závodník {singular} v průměru v hodnoceném období o {(float(vysledky[0][-1]) - MUJ_PRUMER):.2f}% lepší než vybraný závodník.")
    lepsich_zavodniku = 0
    for record in vysledky:
        if record[1] != JMENO:
            lepsich_zavodniku += 1
        else:
            break
    print_and_log(
        f"Závodníků, kteří v hodnoceném období {plural} lepší průměrné výsledky než vybraný závodník: {lepsich_zavodniku}")


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
    if ftp_script.exists():
        try:
            upload_ftps(
                host,
                username,
                password,
                remote_dir
            )
            webbrowser.open(f"{visit}{LOGNAME}.html")
        except Exception as e:
            print(f"Chyba FTP: {e}")
    else:
        webbrowser.open(Path(f"{FOLDER}/{LOGNAME}.html").resolve().as_uri())


if __name__ == "__main__":
    run()
