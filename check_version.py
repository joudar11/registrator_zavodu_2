import urllib.request
import sys
import subprocess
import platform
import os

def zkontroluj_a_aktualizuj(global_env = False):
    url_s_verzi = "https://los.krystofklika.cz/manifest.txt" 
    aktualni_verze_str = "02.01"
    """
    Stáhne verzi z URL, porovná ji číselně s lokální verzí.
    Pokud je na serveru novější, spustí update skript a ukončí tento program.
    """
    print(f"ℹ️ Ověřuji aktualizace na: {url_s_verzi}")

    try:
        # Timeout 3 sekundy, ať to nebrzdí start, pokud server neodpovídá
        with urllib.request.urlopen(url_s_verzi, timeout=3) as response:
            server_verze_str = response.read().decode('utf-8').strip()
    except Exception as e:
        print(f"❌ Chyba při kontrole verze (pokračuji bez update): {e}")
        return

    # Převedeme "02.00" na (2, 0) pro korektní matematické porovnání
    try:
        lokalni_tuple = tuple(map(int, aktualni_verze_str.split('.')))
        server_tuple = tuple(map(int, server_verze_str.split('.')))
    except ValueError:
        print(f"❌ Chyba: Neplatný formát verze. Server: '{server_verze_str}', Lokální: '{aktualni_verze_str}'")
        return

    print(f"ℹ️ Lokální verze: {lokalni_tuple} | Serverová verze: {server_tuple}")

    if server_tuple > lokalni_tuple:
        print("ℹ️ Nalezena novější verze! Spouštím aktualizační skript...")
        
        operacni_system = platform.system()
        
        # Cesta ke skriptům [Inference] Předpokládám, že leží vedle tohoto skriptu
        if global_env:
            win_script = "update_GLOBAL.bat"
        else:
            win_script = "update.bat"
        lin_script = "./update.sh"

        if operacni_system == "Windows":
            subprocess.Popen([win_script], creationflags=subprocess.CREATE_NEW_CONSOLE, shell=True)
            
        elif operacni_system == "Linux":
            if os.path.exists(lin_script):
                current_permissions = os.stat(lin_script).st_mode
                os.chmod(lin_script, current_permissions | 0o111)
            
            subprocess.Popen([lin_script])
            
        else:
            print(f"❌ Neznámý OS: {operacni_system}, nemohu aktualizovat.")
            return

        print("ℹ️ Ukončuji aplikaci pro provedení aktualizace.")
        sys.exit(0)
        
    elif server_tuple < lokalni_tuple:
        print("ℹ️ Máš novější verzi než server (vývojová verze?).")
    else:
        print("ℹ️ Software je aktuální. Pokračuji.")

# --- Konfigurace pro testování ---
DOSTUPNA_VERZE_URL = "https://los.krystofklika.cz/manifest.txt" 
AKTUALNI_VERZE = "02.01"

#zkontroluj_a_aktualizuj(AKTUALNI_VERZE, DOSTUPNA_VERZE_URL)