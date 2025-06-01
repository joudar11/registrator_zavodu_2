# Automatická registrace na LOS závod

Vylepšený [skript](https://github.com/joudar11/registrator_zavodu), který nepoužívá inputy v konzoli, ale bere si údaje ze souboru.

Tento skript v Pythonu využívá knihovnu **Playwright** k automatické registraci na LOS závod v přesný čas. Součástí je i automatické odeslání potvrzovacího e-mailu a informování přítelkyně.

## 📦 Požadavky

- Python 3.9+
- `playwright`
- Google účet s možností přihlašování přes aplikace (pro SMTP)
- Vytvořený soubor `data.py` s následujícími proměnnými:

```python
JMENO = "..."                # Jméno závodníka
CISLO_DOKLADU = "..."        # Číslo ZP
CLENSKE_ID = "..."           # LEX ID (volitelné)
DIVIZE = "..."               # Název divize (shodný s výběrem na webu)
URL = "..."                  # URL závodu
LOGIN = "..."                # Email pro přihlášení i notifikace
HESLO = "..."                # Heslo
DATUM_CAS_REGISTRACE = "2025-06-15 20:00:00"  # Čas zahájení registrace nebo None, pokud má registrace proběhnout okamžitě
SQUAD = "2"                  # Číslo squadu (Musí být string)
GOOGLE_P = "..."             # Heslo k Gmailu pro SMTP (pomocí App passwords funkce v Google účtu)
GOOGLE_U = "..."             # Gmail odesílatele
MZ = True                    # Zaškrtnutí mimo závod
ZACATECNIK = False           # Začátečník
STAVITEL = False             # Stavitel
ROZHODCI = False             # Rozhodčí
POZNAMKA = ""                # Volitelná poznámka
PRITELKYNE = "..."           # Email přítelkyně
JMENO_PRITELKYNE = "..."     # Jméno přítelkyně v prvním pádu
```

## ▶️ Spuštění

```bash
python main.py
```

Při správném nastavení skript:
- počká na přesný čas přihlášení
- přihlásí se na závod
- odešle potvrzovací email
- informuje přítelkyni ❤️

## 📧 Notifikace

Skript používá `smtplib` k odeslání emailu přes Gmail. Nezapomeň povolit "přístup méně zabezpečených aplikací" nebo použít App Passwords.