# --- Standardní knihovny ---
import time
import smtplib
from datetime import datetime
from email.message import EmailMessage
import subprocess
import sys
import platform
from check_version import zkontroluj_a_aktualizuj
if __name__ == "__main__":
    global_env = (len(sys.argv) == 2 and sys.argv[1] == "global")
    zkontroluj_a_aktualizuj(global_env)

# --- Externí knihovny ---
from playwright.sync_api import sync_playwright, TimeoutError

# --- Lokální moduly ---
from data import (
    EMAIL_P, EMAIL_U, LOGIN, URL, INTERVAL, EMAIL_PROVIDER
)

from main import EMAIL_PROVIDERS

LIMIT = 336  # kolikrát maximálně kontrolovat


def run() -> None:
    print("")
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            try:
                page.goto(URL, timeout=10000, wait_until="domcontentloaded")
            except Exception as e:
                print(f"❌ Nelze načíst stránku závodu. {e}")
                return

            attempts = 0
            while attempts < LIMIT:
                attempts += 1
                try:
                    try:
                        page.reload(wait_until="domcontentloaded", timeout=15000)
                    except TimeoutError:
                        print("⚠️ Timeout při reloadu, zkouším po pauze…")
                        time.sleep(INTERVAL)
                        continue

                    label = page.locator("xpath=//div[normalize-space()='Počet registrovaných:']").first
                    value_div = label.locator("xpath=following-sibling::div[1]")
                    value_div.wait_for(timeout=5000)
                    pocet_text = value_div.inner_text().strip()

                    left, right = pocet_text.split("/", 1)
                    pocet = int(left.strip())
                    kapacita = int(right.strip().split()[0])

                    if pocet < kapacita:
                        print("✅ Volné místo!")
                        poslat_informaci()
                        if platform.system() == "Linux":
                            subprocess.Popen(["./run.sh"], shell=True)
                        else:
                            if global_env:
                                subprocess.Popen(["start", "cmd", "/k", "run_GLOBAL.bat"], shell=True)
                            else:
                                subprocess.Popen(["start", "cmd", "/k", "run.bat"], shell=True)
                        return

                    print(datetime.now().strftime("%H:%M:%S"))
                    print(f"Závod je plně obsazen ({pocet} z {kapacita}). "
                          f"Další kontrola za {int(INTERVAL/60)} minut.")
                    print(f"Jakmile se uvolní místo, budu informovat {LOGIN}.\n")
                    time.sleep(INTERVAL)

                except Exception as e:
                    print(f"⚠️ Chyba: {e}. Opakuji po pauze…")
                    time.sleep(INTERVAL)
                    continue

            print(f"⏹️ Konec po {LIMIT} pokusech bez volného místa.")
    except Exception as e:
        print(f"❌ Neošetřená chyba v run(): {e}")

def poslat_informaci() -> None:
    msg = EmailMessage()
    msg['Subject'] = '✅ Uvolnilo se místo v závodě!'
    msg['From'] = EMAIL_U
    msg['To'] = LOGIN
    msg.set_content(
        f"""Ve sledovaném závodě {URL} se uvolnilo místo! Byl spuštěn registrační skript.

Toto je automatizovaný email."""
    )
    odeslat(msg)


def odeslat(msg: str) -> bool:
    if EMAIL_PROVIDER not in EMAIL_PROVIDERS:
        print(f"❌ Poskytovatel emailových služeb {EMAIL_PROVIDER} není implementován. Email nebyl odeslán.")
        return False
    if EMAIL_PROVIDER == "PROTON":
        with smtplib.SMTP('127.0.0.1', 1025) as smtp:
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

if __name__ == "__main__":
    try:
        run()
    except KeyboardInterrupt:
        print("\nProgram ukončen uživatelem.")
    except Exception as e:
        print(f"Neočekávaná chyba: {e}")
