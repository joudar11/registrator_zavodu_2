from playwright.sync_api import sync_playwright
import re
from datetime import datetime
import subprocess
from data import (
    JMENO, DIVIZE, URL, LOGIN, HESLO
    )


DIVIZE_KONVERZE = {"Pistole": "Pi", "Optik/Pistole": "Opt"}  # Převod z divize DATA na tento skript
DIVIZE_V_POHARU = {"Pi": "Pi", "Opt": "OptPi"}


DIVIZE = DIVIZE_KONVERZE[DIVIZE]

URL_CUP = f"https://www.loslex.cz/cup/{int(datetime.now().year) - 2024 + 1}"
SELECTOR_LOGIN_FORM = r"body > div.min-h-screen.bg-gray-100.dark\:bg-gray-900 > nav > div.max-w-7xl.mx-auto.px-4.md\:px-6.lg\:px-8 > div > div.hidden.space-x-1.items-center.md\:-my-px.md\:ml-10.md\:flex > button.inline-flex.items-center.px-1.border-b-2.border-transparent.text-sm.font-medium.leading-5.text-gray-500.dark\:text-gray-400.hover\:text-gray-700.dark\:hover\:text-gray-300.hover\:border-gray-300.dark\:hover\:border-gray-700.focus\:outline-none.focus\:text-gray-700.dark\:focus\:text-gray-300.focus\:border-gray-300.dark\:focus\:border-gray-700.transition.duration-150.ease-in-out"
SELECTOR_LOGIN_BUTTON = r"body > div.fixed.inset-0.overflow-y-auto.px-4.py-6.sm\:px-0.z-2000 > div.mb-6.bg-white.dark\:bg-gray-800.rounded-lg.overflow-hidden.shadow-xl.transform.transition-all.sm\:w-full.sm\:max-w-md.sm\:mx-auto > div > form > div.flex.items-center.justify-end.mt-4 > button"
SELECTOR_USER = r"#login"
SELECTOR_PASS = r"#password"
SELECTOR_DIVIZE_POHAR = f"#division-{DIVIZE_V_POHARU[DIVIZE]}-tab"

jmena = []
vysledky = []


def statistika() -> None:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(URL)
        print("")
        print("Závod:  ", page.title(), " - ", URL)
        print("Pohár:  ", int(datetime.now().year), " - ", URL_CUP)
        print("Divize: ", DIVIZE)
        print("")

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
        page.goto(URL_CUP)
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
            f'div[role="tabpanel"]#division-{DIVIZE}:visible')

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

        # seřazení od nejlepšího
        vysledky.sort(key=lambda x: (x[-1] is None, -(x[-1] if x[-1] is not None else float("-inf"))))

        # výpis
        header = f"{
            '# pohár':>8} | {
            'Jméno':<35} | {
            '% pohár':>10} | {
                'Závody':>7} | {
                    'Průměr %':>9}"
        print(header)
        print("-" * len(header))

        for rank, name, pct, races, avg in vysledky:
            if rank is None:
                print(
                    f"{
                        '–':>8} | {
                        name:<35} | {
                        '–':>10} | {
                        races:>7} | {
                        '–':>9}")
            else:
                pct_out = f"{pct:.2f}%" if pct is not None else "–"
                avg_out = f"{avg:.2f}%" if avg is not None else "–"
                print(
                    f"{
                        rank:>8} | {
                        name:<35} | {
                        pct_out:>10} | {
                        races:>7} | {
                        avg_out:>9}")
        browser.close()


def muj_prumer() -> float:
    for record in vysledky:
        if record[1] == JMENO:
            return record[-1]


def porovnat() -> None:
    MUJ_PRUMER = muj_prumer()
    if vysledky[0][-1] < MUJ_PRUMER:
        porovnani = "horší"
    else:
        porovnani = "lepší"
    print(
        f"\nNejlepší závodník v tomto závodě ({vysledky[0][1]} - {vysledky[0][-1]}%) je v průměru {porovnani} než ty ({MUJ_PRUMER}%)!\n")
    lepsich_zavodniku = 0
    for record in vysledky:
        if record[1] != JMENO:
            lepsich_zavodniku += 1
        else:
            break
    print(f"V závodě je přihlášeno {lepsich_zavodniku} závodníků s lepším průměrem.")
    if input("Přeješ si registrovat? (Y/N): ") == "Y".lower():
        print("Spouštím registrační skript...")
        subprocess.Popen(["start", "cmd", "/k", "python main.py"], shell=True)


if __name__ == "__main__":
    statistika()
    porovnat()
