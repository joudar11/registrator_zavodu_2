from main import odeslat
from playwright.sync_api import sync_playwright, TimeoutError
from data import URL, EMAIL_U, LOGIN
import time
from email.message import EmailMessage

SELECTOR_VYSLEDKY_NADPIS = r"#anresults"
INTERVAL = 10

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(URL)
        print(f"Kontrola zveřejněných výsledků závodu {URL}:\n")
        while True:
            if page.locator(SELECTOR_VYSLEDKY_NADPIS).count() > 0:
                informuj_o_vysledcich()
                break
            else:
                print(f"Výsledky nebyly zveřejněny. Další kontrola za {INTERVAL} sekund.\n")
                time.sleep(INTERVAL)
                page.goto(URL)

def informuj_o_vysledcich() -> None:
    """Informuje závodníka o výsledcích"""
    msg = EmailMessage()
    msg['Subject'] = '🔫 Výsledky zveřejněny'
    msg['From'] = EMAIL_U
    msg['To'] = LOGIN
    msg.set_content(
        f"""Výslkedky závodu {URL} byly zveřejněny.\n\n\n(Automaticky generovaný email)""")

    # Odeslání e-mailu

    if odeslat(msg):
        print(
                        "✅ Odeslal jsem notifikační email o tom, že byly zveřejněny výsledky.")

if __name__ == "__main__":
    try:
        run()
    except Exception as e:
        print(f"Chyba {e}")