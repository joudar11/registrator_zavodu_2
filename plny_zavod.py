# --- Standardní knihovny ---
import time
import smtplib
from datetime import datetime
from email.message import EmailMessage
import subprocess
import sys

# --- Externí knihovny ---
from playwright.sync_api import sync_playwright, TimeoutError

# --- Lokální moduly ---
from data import (
    EMAIL_P, EMAIL_U, LOGIN, URL, INTERVAL
)

LIMIT = 336 # Limit kolikrát se má kontrola zopakovat.

if len(sys.argv) == 2:
    if sys.argv[1] == "global":
        global_env = True
    else:
        global_env = False
else:
    global_env = False

def run() -> None:
    print("")
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            try:
                page.goto(URL, timeout=10000, wait_until="domcontentloaded")
            except Exception as e:
                print(f"❌ Nelze načíst stránku závodu. Server buď neodpovídá, nebo nejsi připojen k internetu.\n\n{e}")
                return False
            while True:
                try:
                    page.reload(wait_until="domcontentloaded", timeout=15000)
                except TimeoutError:
                    print("⚠️ Timeout při reloadu, zkouším dál…")
                    return False
                try:
                    label = page.locator("xpath=//div[normalize-space()='Počet registrovaných:']").first
                    value_div = label.locator("xpath=following-sibling::div[1]")
                    value_div.wait_for(timeout=5000)
                    pocet_text = value_div.inner_text().strip()
                    
                except Exception as e:
                    print(f"Chyba {e}. Opakuji.")
                    return False

                left, right = pocet_text.split("/", 1)
                pocet = int(left.strip())
                kapacita = int(right.strip().split()[0])

                if pocet < kapacita:
                    print("Volné místo!")
                    poslat_informaci()
                    if global_env:
                        subprocess.Popen(["start", "cmd", "/k", "run_GLOBAL.bat"], shell=True)
                    else:
                        subprocess.Popen(["start", "cmd", "/k", "run.bat"], shell=True)
                    return True
                else:
                    print(datetime.now().strftime("%H:%M:%S"))
                    print(f"Závod je plně obsazen ({pocet} z {kapacita}). Další kontrola za {int(INTERVAL/60)} minut.")
                    print(f"Jakmile se uvolní místo, budu informovat {LOGIN}.")
                    print("")

                time.sleep(INTERVAL)

    except Exception as e:
        return False

def poslat_informaci() -> None:
    msg = EmailMessage()
    msg['Subject'] = '✅ Uvolnilo se místo v závodě!'
    msg['From'] = EMAIL_U
    msg['To'] = LOGIN
    msg.set_content(
    f"""Ve sledovaném závodě {URL} se uvolnilo místo! Byl spuštěn registrační skript.
    
Toto je automatizovaný email."""
)

    # Odeslání e-mailu
    with smtplib.SMTP('127.0.0.1', 1025) as smtp:
        smtp.login(EMAIL_U, EMAIL_P)
        smtp.send_message(msg)

if __name__ == "__main__":
    while True:
        if run():
            break