import re
import os
import csv
import sys
from datetime import datetime
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

from check_version import zkontroluj_a_aktualizuj
if __name__ == "__main__":
    global_env = (len(sys.argv) == 2 and sys.argv[1] == "global")
    zkontroluj_a_aktualizuj(global_env)

# Import autentizace ze souboru data.py
from data import LOGIN, HESLO
# Import selektorů a kalendáře z konkurence.py
from konkurence import (
    DIVIZE_V_POHARU, URL_CUP1, URL_CUP2, URL_CUP3,
    POHAR1, POHAR2, POHAR3,
    SELECTOR_LOGIN_FORM, SELECTOR_USER, SELECTOR_PASS,
    SELECTOR_LOGIN_BUTTON,
    FOLDER,
)

# Regulární výraz pro parsování českého formátu data – kompilujeme jednou globálně
DATE_RE = re.compile(r'(\d{1,2})\.[\s\u00A0]*(\d{1,2})\.[\s\u00A0]*(\d{4})')


def parsuj_panel_bs(html: str, divize_klic: str, pohar_rok: str) -> list[list]:
    """
    Parsuje HTML jednoho panelu divize pomocí BeautifulSoup – žádné round-tripy
    do prohlížeče, vše v čistém Pythonu.
    """
    soup = BeautifulSoup(html, "html.parser")
    rows = []

    # Každý střelec je reprezentován dvojicí sousedních div.border-gray-400 + div.flex.gap-x-1
    # Najdeme všechny kontejnery střelců
    shooter_containers = soup.select("div.border.border-gray-400.bg-gray-100")

    for container in shooter_containers:
        # --- Pořadí ---
        rank_div = container.select_one("div.w-5")
        try:
            pohar_rank = int(rank_div.get_text(strip=True).rstrip(".")) if rank_div else ""
        except ValueError:
            pohar_rank = ""

        # --- Jméno ---
        name_div = container.select_one("div.w-36")
        if not name_div:
            continue
        name = name_div.get_text(separator=" ", strip=True)
        name = name.replace("\u00A0", " ").replace("\u200b", "")
        name = " ".join(name.split())
        if not name or "(MZ)" in name:
            continue

        # --- Celková % poháru ---
        total_pct_div = container.select_one("div.w-20.text-right")
        pohar_total_pct = total_pct_div.get_text(strip=True).replace("%", "").strip() if total_pct_div else ""

        # --- Boxy závodů jsou v sousedním divu (next sibling) ---
        boxes_container = container.find_next_sibling("div")
        if not boxes_container:
            continue

        for box in boxes_container.select("div.border.rounded-md.p-1.w-20.cursor-help"):
            # Procenta závodu
            pct_div = box.select_one("div.text-center")
            pct_zavod = pct_div.get_text(strip=True).replace("%", "").strip() if pct_div else ""

            # Započítaný (zelený) vs. škrtnutý (šedý)
            cls = box.get("class", [])
            cls_str = " ".join(cls)
            zapocitany = "Ano" if "border-green-400" in cls_str or "bg-green-100" in cls_str else "Ne"

            # Název, odkaz a datum závodu z odkazu
            link = box.select_one("a")
            title_zavod = (link.get("title") or "").strip() if link else ""
            link_zavod = (link.get("href") or "").strip() if link else ""

           # Datum – hledáme v textu boxu
            box_text = box.get_text(separator=" ")
            datum_zavod = ""
            m = DATE_RE.search(box_text)
            if m:
                d, mo, y = m.group(1), m.group(2), m.group(3)
                try:
                    datum_zavod = datetime.strptime(f"{d}.{mo}.{y}", "%d.%m.%Y").strftime("%Y-%m-%d")
                except ValueError:
                    datum_zavod = f"{d}.{mo}.{y}"

            rows.append([
                pohar_rok,
                divize_klic,
                pohar_rank,
                name,
                pohar_total_pct,
                datum_zavod,
                title_zavod,
                link_zavod,
                pct_zavod,
                zapocitany,
            ])

    return rows


def parsuj_sezonu(page, url_cup: str, pohar_rok: str) -> list[list]:
    """
    Načte stránku sezóny JEDNOU a projde všechny divize přepínáním záložek.
    HTML každého panelu stáhne jediným voláním inner_html() a předá BeautifulSoup.
    """
    print(f"\n📊 Sezóna: {pohar_rok}  →  {url_cup}")
    page.goto(url_cup)
    # Počkáme na načtení stránky – první záložka musí být viditelná
    page.wait_for_selector('ul[role="tablist"]', timeout=15_000)

    vsechny_radky = []

    for divize_klic, divize_kod in DIVIZE_V_POHARU.items():
        tab = page.locator(f'button[data-tabs-target="#division-{divize_kod}"]')
        if tab.count() == 0:
            print(f"  ⚠️  Divize '{divize_kod}' v této sezóně neexistuje, přeskakuji.")
            continue

        tab.click()
        # Čekáme jen na konkrétní panel – ne na celou stránku
        panel = page.locator(f'#division-{divize_kod}')
        panel.wait_for(state="visible", timeout=8_000)

        # Jediný round-trip: stáhneme celé HTML panelu
        html = panel.inner_html()
        radky = parsuj_panel_bs(html, divize_klic, pohar_rok)
        print(f"  📋 {divize_klic:20s} → {len(radky):4d} řádků")
        vsechny_radky.extend(radky)

    return vsechny_radky


def export_to_csv(data: list[list], filename: str) -> None:
    """Zapíše sebraná data do přehledného CSV souboru."""
    os.makedirs(FOLDER, exist_ok=True)
    full_path = f"{FOLDER}/{filename}"

    headers = [
        "Sezona",
        "Divize",
        "Celkove_Poradi_Pohar",
        "Jmeno",
        "Celkova_Procenta_Pohar",
        "Datum_Zavodu",
        "Nazev_Zavodu",
        "Odkaz_Zavodu",
        "Dosazena_Procenta_Zavod",
        "Zapocitany_Do_Poharu",
    ]

    with open(full_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerow(headers)
        writer.writerows(data)

    print(f"\n💾 Uloženo: {full_path}  ({len(data)} řádků celkem)")


def main() -> None:
    print("🚀 Export všech divizí – optimalizovaná verze")

    sezonove_konfigurace = [
        (URL_CUP1, POHAR1),
        (URL_CUP2, POHAR2),
        (URL_CUP3, POHAR3),
    ]

    vsechna_data = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        print("ℹ️  Přihlašuji se...")
        page.goto(URL_CUP1)
        page.click(SELECTOR_LOGIN_FORM)
        page.fill(SELECTOR_USER, LOGIN)
        page.fill(SELECTOR_PASS, HESLO)
        page.click(SELECTOR_LOGIN_BUTTON)
        page.wait_for_load_state("networkidle", timeout=15_000)

        for url_cup, pohar_rok in sezonove_konfigurace:
            vsechna_data.extend(parsuj_sezonu(page, url_cup, pohar_rok))

        browser.close()

    export_to_csv(vsechna_data, "los_pohar_casova_rada.csv")
    print("✅ Hotovo!")


if __name__ == "__main__":
    main()
