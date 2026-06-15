import re
import os
import csv
from datetime import datetime
from pathlib import Path
from playwright.sync_api import sync_playwright

# Import autentizace ze souboru data.py
from data import LOGIN, HESLO
# Import selektorů a kalendáře z konkurence.py
from konkurence import (
    DIVIZE_V_POHARU, URL_CUP1, URL_CUP2, URL_CUP3,
    POHAR1, POHAR2, POHAR3,
    SELECTOR_LOGIN_FORM, SELECTOR_USER, SELECTOR_PASS,
    SELECTOR_LOGIN_BUTTON, SELECTOR_DIVIZE_POHAR,
    FOLDER, DIVIZE
)

def parsuj_data_poharu(page, url_cup, pohar_rok):
    """
    Kompletně projde vybranou divizi v poháru a vytáhne podrobná historická data
    všech jednotlivých závodů pro každého střelce.
    """
    print(f"📊 Stahuji detailní data z poháru {pohar_rok} ({url_cup})...")
    page.goto(url_cup)
    page.click(SELECTOR_DIVIZE_POHAR)
    
    # Hlídáme striktně pouze tvoji divizi nastavenou v data.py
    target_div = DIVIZE_V_POHARU[DIVIZE]
    visible_panel = page.locator(f'div[role="tabpanel"]#division-{target_div}:visible')
    
    # Regulární výraz pro spolehlivé parsování českého formátu data
    date_re = re.compile(r'(\d{1,2}\.\s*[\u00A0]?\d{1,2}\.\s*[\u00A0]?\d{4})')
    
    # Najdeme všechny řádky se jmény v dané divizi
    name_cells = visible_panel.locator("div.w-36:visible").all()
    print(f"   -> Nalezeno {len(name_cells)} střelců v divizi {DIVIZE}")
    
    pohar_rows = []
    
    for cell in name_cells:
        raw_name = cell.text_content().strip()
        lines = raw_name.splitlines()
        name = lines[0].strip() if lines else ""
        
        # Ignorujeme závodníky mimo hodnocení (mimo závod)
        if " (MZ)" in name or not name:
            continue
            
        name = name.replace("\u00A0", " ").replace("\u200b", "")
        name = " ".join(name.split())
        
        # Najdeme nadřazený kontejner střelce pro přístup k celkovému pořadí a procentům
        row = cell.locator("xpath=ancestor::div[contains(@class,'border-gray-400')][1]").first
        
        rank_txt = row.locator("div.w-5:visible").first.text_content().strip().rstrip(".")
        try:
            pohar_rank = int(rank_txt)
        except:
            pohar_rank = ""
            
        pct_loc = cell.locator("xpath=following-sibling::div[contains(@class,'w-20') and contains(@class,'text-right')][1]")
        if pct_loc.count() == 0:
            pct_loc = row.locator("div.w-20.text-right:visible").first
        pohar_pct_raw = pct_loc.text_content().strip() if pct_loc.count() > 0 else ""
        pohar_total_pct = pohar_pct_raw.replace("%", "").strip()
        
        # Pod řádkem střelce leží kontejner s jednotlivými boxy závodů
        next_row = row.locator("+ div.flex.flex-row.gap-x-1.justify-center:visible")
        
        if next_row.count() > 0:
            boxes = next_row.locator("div.border.rounded-md.p-1.w-20.cursor-help:visible").all()
            for box in boxes:
                # 1. Získání procent z daného závodu
                val_raw = box.locator("div.text-center").first.text_content().strip()
                pct_zavod = val_raw.replace("%", "").strip()
                
                # Zjišťujeme, zda je box započítaný (zelený) nebo škrtnutý (šedý)
                class_attr = box.get_attribute("class") or ""
                zapocitany = "Ano" if "border-green-400" in class_attr or "bg-green-100" in class_attr else "Ne"
                
                # 2. Získání názvu závodu a přesného data z odkazu/atributů
                link_el = box.locator("a").first
                title_zavod = link_el.get_attribute("title") if link_el.count() > 0 else ""
                if not title_zavod:
                    title_zavod = box.get_attribute("title") or ""
                
                datum_zavod = ""
                sources = [
                    box.inner_text() or "",
                    box.text_content() or "",
                    title_zavod
                ]
                for src in sources:
                    m = date_re.search(src)
                    if m:
                        date_str = m.group(1).replace(" ", "").replace("\u00A0", "")
                        try:
                            # Převedeme na ISO formát (YYYY-MM-DD), který je ideální pro řazení a grafy
                            datum_zavod = datetime.strptime(date_str, "%d.%m.%Y").strftime("%Y-%m-%d")
                        except:
                            datum_zavod = date_str
                        break
                
                # Uložíme plochou strukturu dat: jeden řádek = jeden výsledek
                pohar_rows.append([
                    pohar_rok,
                    pohar_rank,
                    name,
                    pohar_total_pct,
                    datum_zavod,
                    title_zavod,
                    pct_zavod,
                    zapocitany
                ])
                
    return pohar_rows

def export_to_csv(data, filename):
    """Zapíše sebraná data do přehledného CSV souboru."""
    os.makedirs(FOLDER, exist_ok=True)
    full_path = f"{FOLDER}/{filename}"
    
    headers = [
        "Sezona", 
        "Celkove_Poradi_Pohar", 
        "Jmeno", 
        "Celkova_Procenta_Pohar", 
        "Datum_Zavodu", 
        "Nazev_Zavodu", 
        "Dozazena_Procenta_Zavod", 
        "Zapocitany_Do_Poharu"
    ]
    
    with open(full_path, "w", newline="", encoding="utf-8") as csv_file:
        writer = csv.writer(csv_file, delimiter=";")
        writer.writerow(headers)
        writer.writerows(data)
        
    print(f"💾 Výsledná časová řada úspěšně uložena do: {full_path}")

def main():
    print("🚀 Spouštím detailní datový export časových řad pro divizi:", DIVIZE)
    vsechna_data = []
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        print("ℹ️ Přihlašuji se do systému LOS...")
        page.goto(URL_CUP1)
        page.click(SELECTOR_LOGIN_FORM)
        page.fill(SELECTOR_USER, LOGIN)
        page.fill(SELECTOR_PASS, HESLO)
        page.click(SELECTOR_LOGIN_BUTTON)
        
        # Postupně stáhneme data ze všech tří sledovaných sezón
        vsechna_data.extend(parsuj_data_poharu(page, URL_CUP1, POHAR1))
        vsechna_data.extend(parsuj_data_poharu(page, URL_CUP2, POHAR2))
        vsechna_data.extend(parsuj_data_poharu(page, URL_CUP3, POHAR3))
        
        browser.close()
        
    # Exportujeme vše do jednoho velkého master souboru
    export_to_csv(vsechna_data, "los_pohar_casova_rada.csv")
    print("✅ Hotovo! Data jsou kompletně připravena pro analýzu a tvorbu grafů.")

if __name__ == "__main__":
    main()
