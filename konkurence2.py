import re
import os
from datetime import datetime, date, timedelta
import webbrowser
from pathlib import Path
import sys
from ftplib import FTP_TLS
from check_version import zkontroluj_a_aktualizuj
import io
import ftplib
import ssl

if __name__ == "__main__":
    global_env = (len(sys.argv) == 2 and sys.argv[1] == "global")
    zkontroluj_a_aktualizuj(global_env)

from playwright.sync_api import sync_playwright

from data import (
    JMENO, DIVIZE, URL, LOGIN, HESLO
)

ftp_script = Path(__file__).parent / "ftp_konkurence.py"
if ftp_script.exists():
    from ftp_konkurence import (
        host, username, password, remote_dir, visit
    )
else:
    visit = ""

if len(sys.argv) == 4:
    JMENO = sys.argv[1]
    DIVIZE = sys.argv[2]
    URL = sys.argv[3]
    
if JMENO == "None":
    JMENO = None

DIVIZE_KONVERZE = {"Pistole": "Pi", "Optik/Pistole": "OptPi",
                   "PDW": "PDW", "Malá pistole": "MPi"}
DIVIZE_V_POHARU = {"Pi": "Pi", "OptPi": "Opt", "PDW": "PDW", "MPi": "MPi", "KPi": "KPi"}

DIVIZE = DIVIZE_KONVERZE[DIVIZE]

CREATE = True
FOLDER = "konkurence"
TIME = datetime.now().replace(microsecond=0).strftime("%Y-%m-%d_%H-%M-%S")
LOGNAME = f"konkurence-{URL.split('/')[-1]}-{JMENO}-{DIVIZE}"
KONZOLE = False
FIRST_RUN = True
HEADER_LEN = None
LAST12_SUMS = {}
CUTOFF_12M = date.today() - timedelta(days=365)

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
SELECTOR_DATUM = r"body > div.min-h-screen.bg-gray-100.dark\:bg-gray-900 > main > div.py-4 > div > div > div > div:nth-child(1) > div.grid.grid-cols-auto.lg\:grid-cols-fitfirst.gap-x-2.lg\:gap-x-4.gap-y-2 > div:nth-child(10)"

jmena = []
extra_jmena = []
vysledky = []


def upload_ftps(host: str, username: str, password: str, remote_dir: str) -> None:
    local_path = Path(f"{FOLDER}/{LOGNAME}.html").resolve()
    
    if not local_path.exists():
        print(f"❌ Soubor {local_path} neexistuje.")
        return

    print(f"🔗 Připojuji se k FTP serveru {host} (standardní režim)...")
    try:
        with open(local_path, "rb") as f:
            bio = io.BytesIO(f.read())

        with ftplib.FTP(host) as ftp:
            ftp.login(user=username, passwd=password)
            ftp.set_pasv(True)
            
            try:
                ftp.cwd(remote_dir)
            except Exception:
                dirs = remote_dir.strip("/").split("/")
                path = ""
                for d in dirs:
                    path += f"/{d}"
                    try:
                        ftp.cwd(path)
                    except Exception:
                        ftp.mkd(path)
                        ftp.cwd(path)
            
            ftp.storbinary(f"STOR {local_path.name}", bio)
            
        print(f"✅ Soubor {local_path.name} byl úspěšně nahrán na {host}:{remote_dir}")
    except Exception as e:
        print(f"❌ Chyba při nahrávání na FTP: {e}")


def smazat_log() -> None:
    global FOLDER
    global LOGNAME
    filename = f"{LOGNAME}.html"
    path = os.path.join(FOLDER, filename)
    if os.path.isfile(path):
        os.remove(path)
        print(f"✅ Soubor '{path}' byl smazán.")
    return


def pridat_extra_jmena():
    if not extra_jmena:
        return
    global jmena
    for extra_jmeno in extra_jmena:
        if extra_jmeno not in jmena:
            jmena.append(extra_jmeno)


def print_konzole(content: str) -> None:
    if KONZOLE:
        print(content)


def init_html_file():
    os.makedirs(FOLDER, exist_ok=True)
    with open(f"{FOLDER}/{LOGNAME}.html", "w", encoding="utf-8") as f:
        f.write("""<!DOCTYPE html>
<html lang="cs">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Analýza konkurence</title>
    <style>
        :root {
            --bg-body: #f8fafc;
            --bg-card: #ffffff;
            --text-main: #0f172a;
            --text-muted: #64748b;
            --border-color: #e2e8f0;
            --primary-link: #2563eb;
            
            /* Highlights */
            --bg-user: #ffeaa7;
            --bg-top3-odd: #fab1a0;
            --bg-top3-even: #f7876e;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            background-color: var(--bg-body);
            color: var(--text-main);
            margin: 0;
            padding: 16px;
            line-height: 1.5;
        }

        .container {
            max-width: 1100px;
            margin: 0 auto;
        }

        .card {
            background: var(--bg-card);
            border-radius: 12px;
            border: 1px solid var(--border-color);
            box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.05);
            padding: 20px;
            margin-bottom: 24px;
        }

        h1, h2 {
            margin-top: 0;
            color: var(--text-main);
        }

        h1 { font-size: 1.5rem; }
        h2 { font-size: 1.25rem; }

        a {
            color: var(--primary-link);
            text-decoration: none;
        }

        a:hover { text-decoration: underline; }

        .info-grid {
            display: grid;
            grid-template-columns: auto 1fr;
            gap: 8px 16px;
            font-size: 14px;
            margin-bottom: 16px;
        }

        .info-label {
            color: var(--text-muted);
            font-weight: 600;
        }

        .legend {
            display: flex;
            flex-direction: column;
            gap: 6px;
            font-size: 13px;
            margin-top: 16px;
            padding-top: 16px;
            border-top: 1px dashed var(--border-color);
        }

        .legend-item {
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .legend-box {
            display: inline-block;
            width: 14px;
            height: 14px;
            border-radius: 3px;
            flex-shrink: 0;
        }

        .help-list {
            display: grid;
            grid-template-columns: auto 1fr;
            gap: 6px 12px;
            font-size: 12px;
            color: var(--text-muted);
            background: #f1f5f9;
            padding: 12px;
            border-radius: 8px;
            margin-top: 16px;
        }

        .table-wrapper {
            margin-top: 12px;
            width: 100%;
        }

        table {
            width: 100%;
            border-collapse: collapse;
            font-size: 14px;
            text-align: left;
        }

        th {
            background-color: #f1f5f9;
            color: var(--text-muted);
            font-weight: 600;
            text-transform: uppercase;
            font-size: 11px;
            letter-spacing: 0.05em;
            padding: 10px 12px;
            border-bottom: 1px solid var(--border-color);
        }

        td {
            padding: 8px 12px;
            border-bottom: 1px solid var(--border-color);
        }

        .text-right { text-align: right; }
        .text-center { text-align: center; }

        .comparison-note {
            background-color: #eff6ff;
            border-left: 4px solid var(--primary-link);
            padding: 10px 14px;
            margin-top: 16px;
            border-radius: 0 6px 6px 0;
            font-size: 14px;
        }

        /* Responsive kartové zobrazení pro mobily */
        @media (max-width: 640px) {
            body { padding: 8px; }
            .card { padding: 14px; }
            
            table, thead, tbody, th, td, tr {
                display: block;
            }

            thead tr {
                position: absolute;
                top: -9999px;
                left: -9999px;
            }

            tr {
                border: 1px solid var(--border-color);
                border-radius: 8px;
                margin-bottom: 12px;
                padding: 8px 12px;
                box-shadow: 0 1px 2px rgba(0,0,0,0.03);
            }

            td {
                border: none;
                border-bottom: 1px solid rgba(0,0,0,0.05);
                position: relative;
                padding-left: 50% !important;
                text-align: right !important;
                white-space: normal;
                min-height: 24px;
                display: flex;
                align-items: center;
                justify-content: flex-end;
            }

            td:last-child {
                border-bottom: none;
            }

            td::before {
                position: absolute;
                left: 12px;
                width: 45%;
                padding-right: 10px;
                white-space: nowrap;
                text-align: left;
                font-weight: 600;
                font-size: 11px;
                color: var(--text-muted);
                text-transform: uppercase;
                content: attr(data-label);
            }
        }
    </style>
</head>
<body>
<div class="container">
""")


def statistika() -> None:
    global FIRST_RUN
    global HEADER_LEN
    global LAST12_SUMS
    LAST12_SUMS = {}

    init_html_file()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(URL)
        print_and_log("")
        if FIRST_RUN:
            vytvoreno = datetime.now()
            datum_zavodu = page.inner_text(SELECTOR_DATUM, timeout=2000)
            vytvoreno_f = vytvoreno.strftime("%d. %m. %Y %H:%M")

            only_log('<div class="card">')
            only_log('<h1>📊 Přehled výsledků konkurence</h1>')
            only_log('<div class="info-grid">')
            
            if ftp_script.exists():
                only_log(f'<div class="info-label">Přehled:</div><div><a target="_blank" href="{visit}">{visit}</a></div>')
            
            print_konzole(f'Závod:            {page.title()} - {URL}')
            print_konzole(f"Divize:           {DIVIZE}")
            print_konzole(f"Datum závodu:     {datum_zavodu}")
            print_konzole(f"Vytvořeno:        {vytvoreno_f}")
            
            only_log(f'<div class="info-label">Závod:</div><div><a target="_blank" href="{URL}">{page.title()}</a></div>')
            only_log(f'<div class="info-label">Divize:</div><div>{DIVIZE}</div>')
            only_log(f'<div class="info-label">Datum závodu:</div><div>{datum_zavodu}</div>')
            only_log(f'<div class="info-label">Vygenerováno:</div><div><b>{vytvoreno_f}</b></div>')
            
            only_log('</div>')

            only_log('<div class="legend">')
            only_log('<div class="legend-item"><span class="legend-box" style="background-color: #b0b0b0;"></span><span style="color: #b0b0b0;">Závodník, který se nezúčastnil žádného pohárového závodu v hodnoceném období</span></div>')
            only_log('<div class="legend-item"><span class="legend-box" style="background-color: #fab1a0;"></span><span>Závodník, který se v poháru ve vybrané sezóně umístil na jednom z prvních 3 míst</span></div>')
            if JMENO:
                only_log(f'<div class="legend-item"><span class="legend-box" style="background-color: #ffeaa7;"></span><span>Vybraný závodník - {JMENO}</span></div>')
            only_log('</div>')

            only_log("""
            <div class="help-list">
                <div><b>#</b></div><div>Pořadí - řazeno dle průměrných výsledků v hodnoceném období</div>
                <div><b># POHÁR</b></div><div>Pořadí ve vybraném poháru</div>
                <div><b>% POHÁR</b></div><div>Procenta dosažená ve vybraném poháru</div>
                <div><b>ZÁVODY</b></div><div>Počet pohárových závodů, kterých se závodník v hodnoceném období zúčastnil</div>
                <div><b>PRŮMĚR %</b></div><div>Průměrný výsledek závodníka ve všech pohárových závodech v hodnoceném období</div>
                <div><b>PROJEKCE %</b></div><div>Předpokládaný procentní zisk, pokud všichni závodníci podají svůj průměrný výkon</div>
            </div>
            </div>
            """)

        print("ℹ️ Přihlašuji se...")
        page.click(SELECTOR_LOGIN_FORM)
        page.wait_for_selector(SELECTOR_USER)
        page.wait_for_selector(SELECTOR_PASS)
        page.fill(SELECTOR_USER, LOGIN)
        page.fill(SELECTOR_PASS, HESLO)
        page.wait_for_selector(SELECTOR_LOGIN_BUTTON)
        page.click(SELECTOR_LOGIN_BUTTON)

        print("ℹ️ Načítám závodníky...")
        try:
            page.wait_for_selector(f'[title="{DIVIZE}"]', timeout=5000)
        except Exception as e:
            print(f"Chyba - ukončuji\n\n{e}")
            sys.exit()
        els = page.locator(f'div[title="{DIVIZE}"]:visible')

        for i in range(els.count()):
            el = els.nth(i)
            lines = el.inner_text().splitlines()
            raw_name = lines[0].strip() if lines else ""

            if " (MZ)" in raw_name:
                continue

            name = raw_name.replace("\u00A0", " ").replace("\u200b", "")
            name = " ".join(name.split())

            if name:
                jmena.append(name)

        if JMENO is not None and (JMENO not in jmena):
            jmena.append(JMENO)
        pridat_extra_jmena()

        print(f"ℹ️ Hodnotím pohár {URL_CUP1}")
        pohar(URL_CUP1, page, zahrnout_do_12m=True)
        vypis(POHAR1, URL_CUP1)
        try:
            porovnat()
        except TypeError:
            pass
        only_log('</div>')
        vynuluj()
        FIRST_RUN = False

        print(f"ℹ️ Hodnotím pohár {URL_CUP2}")
        pohar(URL_CUP2, page, zahrnout_do_12m=True)
        vypis(POHAR2, URL_CUP2)
        try:
            porovnat()
        except TypeError:
            pass
        only_log('</div>')
        vynuluj()

        print(f"ℹ️ Hodnotím pohár {URL_CUP3}")
        pohar(URL_CUP3, page)
        vypis(POHAR3, URL_CUP3)
        try:
            porovnat()
        except TypeError:
            pass
        only_log('</div>')

        vynuluj()
        print(f"ℹ️ Hodnotím posledních 12 měsíců")

        vypis_poslednich_12_mesicu()
        try:
            porovnat(True)
        except TypeError:
            pass
        only_log('</div>')

        only_log("</div></body></html>")
        browser.close()


def vypis(pohar: str, pohar_url: str):
    print(f"ℹ️ Zapisuji výsledky poháru {pohar} do tabulky")
    global vysledky
    koeficient = float(0)
    print_konzole(f"Hodnocené období: {pohar} - {pohar_url}")
    
    only_log('<div class="card">')
    only_log(f'<h2>Hodnocené období: <a href="{pohar_url}">Pohár {pohar}</a></h2>')
    only_log('<div class="table-wrapper"><table>')
    only_log("""<thead>
        <tr>
            <th class="text-center">#</th>
            <th class="text-center"># Pohár</th>
            <th>Jméno</th>
            <th class="text-right">% Pohár</th>
            <th class="text-right">Závody</th>
            <th class="text-right">Průměr %</th>
            <th class="text-right">Projekce %</th>
        </tr>
    </thead><tbody>""")

    vysledky.sort(key=lambda x: (
        x[-1] is None, -(x[-1] if x[-1] is not None else float("-inf"))))

    i = 1
    for rank, name, pct, races, avg in vysledky:
        SPAN_BEGIN = ''
        SPAN_END = ''
        row_style = ''

        if i == 1 and avg:
            koeficient = 100/avg
            projekce = 100

        if name == JMENO:
            if races == 0:
                row_style = 'background-color: #ffeaa7; color: #b0b0b0;'
            else:
                row_style = 'background-color: #ffeaa7;'
        elif rank in range(1, 4):
            if not (i % 2 == 0):
                row_style = 'background-color: #fab1a0;'
            else:
                row_style = 'background-color: #f7876e;'
        elif races == 0:
            row_style = 'color: #b0b0b0;'
        elif i % 2 == 0:
            row_style = 'background-color: #f8fafc;'

        if row_style:
            SPAN_BEGIN = f'<tr style="{row_style}">'
        else:
            SPAN_BEGIN = '<tr>'
        SPAN_END = '</tr>'

        if rank is None:
            print_konzole(f"{'-':>3} | {'–':>8} | {name:<35} | {'–':>10} | {races:>7} | {'–':>9} | {'–':>11}")
            only_log(f'{SPAN_BEGIN}'
                     f'<td data-label="#" class="text-center">-</td>'
                     f'<td data-label="# Pohár" class="text-center">–</td>'
                     f'<td data-label="Jméno">{name}</td>'
                     f'<td data-label="% Pohár" class="text-right">–</td>'
                     f'<td data-label="Závody" class="text-right">{races}</td>'
                     f'<td data-label="Průměr %" class="text-right">–</td>'
                     f'<td data-label="Projekce %" class="text-right">–</td>'
                     f'{SPAN_END}')
        else:
            projekce = avg * koeficient if avg else None
            pct_out = f"{pct:.2f}%" if pct is not None else "–"
            avg_out = f"{avg:.2f}%" if avg is not None else "–"
            projekce_out = f"{projekce:.2f}%" if projekce is not None else "–"
            
            print_konzole(f"{i:>3} | {rank:>8} | {name:<35} | {pct_out:>10} | {races:>7} | {avg_out:>9} | {projekce_out:>11}")
            only_log(f'{SPAN_BEGIN}'
                     f'<td data-label="#" class="text-center">{i}</td>'
                     f'<td data-label="# Pohár" class="text-center">{rank}</td>'
                     f'<td data-label="Jméno">{name}</td>'
                     f'<td data-label="% Pohár" class="text-right">{pct_out}</td>'
                     f'<td data-label="Závody" class="text-right">{races}</td>'
                     f'<td data-label="Průměr %" class="text-right">{avg_out}</td>'
                     f'<td data-label="Projekce %" class="text-right">{projekce_out}</td>'
                     f'{SPAN_END}')
        i += 1

    only_log('</tbody></table></div>')


def vypis_poslednich_12_mesicu():
    print(f"ℹ️ Zapisuji posledních 12 měsíců do tabulky")
    global vysledky
    global jmena
    koeficient = float(0)
    vysledky = []
    
    for name in jmena:
        s, c = LAST12_SUMS.get(name, (0.0, 0))
        avg = round(s / c, 2) if c > 0 else None
        vysledky.append((None, name, None, c, avg))

    vysledky.sort(key=lambda x: (x[-1] is None, -(x[-1] if x[-1] is not None else float("-inf"))))

    print_konzole(f'Hodnocené období: {CUTOFF_12M:%d. %m. %Y} - {date.today():%d. %m. %Y}')
    
    only_log('<div class="card">')
    only_log(f'<h2>Hodnocené období: {CUTOFF_12M:%d. %m. %Y} - {date.today():%d. %m. %Y}</h2>')
    only_log('<div class="table-wrapper"><table>')
    only_log("""<thead>
        <tr>
            <th class="text-center">#</th>
            <th>Jméno</th>
            <th class="text-right">Závody</th>
            <th class="text-right">Průměr %</th>
            <th class="text-right">Projekce %</th>
        </tr>
    </thead><tbody>""")

    i = 1
    for rank, name, pct, races, avg in vysledky:
        if i == 1 and avg:
            koeficient = 100/float(avg)
            projekce = 100
        SPAN_BEGIN = ''
        SPAN_END = ''
        row_style = ''

        if name == JMENO:
            if races == 0:
                row_style = 'background-color: #ffeaa7; color: #b0b0b0;'
            else:
                row_style = 'background-color: #ffeaa7;'
        elif races == 0:
            row_style = 'color: #b0b0b0;'
        elif i % 2 == 0:
            row_style = 'background-color: #f8fafc;'

        if row_style:
            SPAN_BEGIN = f'<tr style="{row_style}">'
        else:
            SPAN_BEGIN = '<tr>'
        SPAN_END = '</tr>'

        if rank is None:
            if i == 1:
                projekce = 100
            else:
                projekce = (avg * koeficient) if (avg is not None and koeficient is not None and i != 1) else None
            projekce_out = f"{projekce:.2f}%" if projekce is not None else "–"
            avg_out = f"{avg:.2f}%" if avg is not None else "–"
            rank_disp = "–" if avg is None else i

            only_log(f'{SPAN_BEGIN}'
                     f'<td data-label="#" class="text-center">{rank_disp}</td>'
                     f'<td data-label="Jméno">{name}</td>'
                     f'<td data-label="Závody" class="text-right">{races}</td>'
                     f'<td data-label="Průměr %" class="text-right">{avg_out}</td>'
                     f'<td data-label="Projekce %" class="text-right">{projekce_out}</td>'
                     f'{SPAN_END}')
        i += 1

    only_log('</tbody></table></div>')


def pohar(URL_z, page, zahrnout_do_12m=False):
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
                val_raw = box.locator("div.text-center").first.text_content().strip()
                val = _clean_percent(val_raw)

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


def porovnat(M12=False) -> None:
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
        only_log('<div class="comparison-note">')
        print_and_log("\nVybraný závodník je nejlepším přihlášeným závodníkem v tomto závodě!")
        only_log('</div>')
        return
        
    MUJ_PRUMER = muj_prumer()
    if MUJ_PRUMER is None:
        return

    only_log('<div class="comparison-note">')
    print_and_log(
        f'\nNejlepší závodník {singular} v průměru v hodnoceném období o {(float(vysledky[0][-1]) - MUJ_PRUMER):.2f} procentních bodů lepší než <span style="background-color: #ffeaa7; padding: 2px 4px; border-radius: 4px;">{JMENO}</span>.')
    
    lepsich_zavodniku = 0
    for record in vysledky:
        if record[1] != JMENO:
            lepsich_zavodniku += 1
        else:
            break
            
    print_and_log(
        f'Závodníků, kteří v hodnoceném období {plural} lepší průměrné výsledky než <span style="background-color: #ffeaa7; padding: 2px 4px; border-radius: 4px;">{JMENO}</span>: {lepsich_zavodniku}')
    only_log('</div>')


def print_and_log(action: str) -> None:
    """Zprávu vytiskne do konzole a zároveň uloží do HTML logu."""
    print_konzole(action)
    try:
        os.makedirs(FOLDER, exist_ok=True)
    except Exception as e:
        print(f"❌ Nelze vytvořit složku {FOLDER}:\n{e}")
        return

    with open(f"{FOLDER}/{LOGNAME}.html", "a", encoding="utf-8") as f:
        f.write(f"{action}<br>\n")


def only_log(action: str) -> None:
    """Zprávu uloží na konec HTML logu."""
    try:
        os.makedirs(FOLDER, exist_ok=True)
    except Exception as e:
        print(f"❌ Nelze vytvořit složku {FOLDER}:\n{e}")
        return

    with open(f"{FOLDER}/{LOGNAME}.html", "a", encoding="utf-8") as f:
        f.write(f"{action}\n")


def vynuluj() -> None:
    global vysledky
    vysledky = []
    return


def run() -> None:
    smazat_log()
    statistika()
    
    if ftp_script.exists():
        try:
            upload_ftps(
                host,
                username,
                password,
                remote_dir
            )
            smazat_log()
            if not os.listdir(FOLDER):
                try:
                    os.rmdir(FOLDER)
                    print(f"✅ Prázdná složka {FOLDER} byla smazána.")
                except Exception as e:
                    print(f"Chyba {e}")
            webbrowser.open(f"{visit}{LOGNAME}.html")
        except Exception as e:
            print(f"Chyba FTP: {e}")
    else:
        webbrowser.open(Path(f"{FOLDER}/{LOGNAME}.html").resolve().as_uri())


if __name__ == "__main__":
    try:
        run()
    except KeyboardInterrupt:
        print("\nProgram ukončen uživatelem.")
    except Exception as e:
        print(f"Neočekávaná chyba: {e}")