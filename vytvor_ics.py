# --- Standardní knihovny ---
from datetime import datetime
from ics import Calendar, Event

# --- Externí knihovny ---
from playwright.sync_api import sync_playwright

# --- Lokální moduly ---
from data import URL

# Slovník převodu měsíců
MESICE = {
    "ledna": 1, "února": 2, "března": 3, "dubna": 4,
    "května": 5, "června": 6, "července": 7, "srpna": 8,
    "září": 9, "října": 10, "listopadu": 11, "prosince": 12,
}

filename = "zavod.ics"

# CSS selektory a lokátory
NAZEV_LOCATOR = (
    "body > div.min-h-screen.bg-gray-100.dark\\:bg-gray-900 > "
    "main > div.py-4 > div > div > div > div:nth-child(1) "
    "> div.justify-center.items-baseline.text-xl.font-bold.flex"
)


def nacti_text_ze_stranky(page, label_text: str) -> str:
    """Vrátí text hodnoty z páru 'label : value'."""
    label = page.locator(f"xpath=//div[normalize-space()='{label_text}']").first
    value = label.locator("xpath=following-sibling::div[1]")
    value.wait_for(timeout=5000)
    return value.inner_text().strip()


def ziskej_data(page):
    """Získá název, datum a střelnici ze stránky závodu."""
    nazev = page.inner_text(NAZEV_LOCATOR).strip()
    datum_raw = nacti_text_ze_stranky(page, "Datum závodu:")
    strelnice = nacti_text_ze_stranky(page, "Střelnice:")

    den_str, mesic_str, rok_str = datum_raw.split()
    den = int(den_str.replace(".", ""))
    mesic = MESICE[mesic_str]
    rok = int(rok_str)

    datum = datetime(rok, mesic, den)

    return nazev, datum, strelnice, datum_raw


def vytvor_ics(nazev: str, datum: datetime, strelnice: str):
    """Vytvoří a uloží ICS soubor s událostí."""
    c = Calendar()
    e = Event(
        name=nazev,
        begin=datum.date(),
        location=strelnice
    )
    e.make_all_day()
    c.events.add(e)

    with open(filename, "w", encoding="utf-8") as f:
        f.writelines(c)

    print("✅ ICS soubor byl vytvořen.")


def main():
    """Hlavní funkce – načte stránku, získá data a uloží ICS."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        try:
            page.goto(URL, timeout=10000)
        except Exception as e:
            print(f"❌ Nelze načíst stránku {URL}.\n{e}")
            return

        if page.title() == "Nenalezeno":
            print(f"❌ Stránka závodu {URL} nebyla nalezena (404).")
            return

        nazev, datum, strelnice, datum_raw = ziskej_data(page)

        # print(f"Co : {nazev}")
        # print(f"Kdy: {datum_raw}")
        # print(f"Kde: {strelnice}")

        vytvor_ics(nazev, datum, strelnice)
        return filename


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"⚠️ Neošetřená chyba: {e}")
