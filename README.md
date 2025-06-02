# Automatická registrace na LOS závod

Vylepšený [skript](https://github.com/joudar11/registrator_zavodu), který automaticky provádí registraci na závod LOS Lex pomocí knihovny Playwright. Nevyžaduje žádné zadávání údajů v konzoli – vše si načítá z konfiguračního souboru `data.py`.

Součástí je:
- časovaná registrace s přesností na sekundy
- automatické přihlášení do systému
- odeslání potvrzovacího e-mailu
- notifikace přítelkyni ❤️

## 📦 Požadavky

- Python 3.13
- `playwright`
- Gmail s aktivním přihlášením pomocí App Passwords (SMTP)
- Konfigurační soubor `data.py` s následujícím obsahem:

```python
JMENO = "..."                # Jméno závodníka
CISLO_DOKLADU = "..."        # Číslo ZP
CLENSKE_ID = "..."           # LEX ID (volitelné)
DIVIZE = "..."               # Název divize přesně dle výběru na webu
URL = "..."                  # URL konkrétního závodu
LOGIN = "..."                # Email pro přihlášení i notifikace
HESLO = "..."                # Heslo do systému LOS Lex
DATUM_CAS_REGISTRACE = "2025-06-15 20:00:00"  # nebo None pro okamžitou registraci. Formát musí být RRRR-MM-DD HH:MM:SS
SQUAD = 2                    # Číslo squadu
GOOGLE_P = "..."             # Gmail App Password pro SMTP
GOOGLE_U = "..."             # Gmail odesílatele
MZ = True                    # Mimo závod
ZACATECNIK = False           # Začátečník
STAVITEL = False             # Stavitel
ROZHODCI = False             # Rozhodčí
POZNAMKA = "..."             # Poznámka (volitelné) - Může být None
PRITELKYNE = "..."           # Email přítelkyně
JMENO_PRITELKYNE = "..."     # Křestní jméno přítelkyně v prvním pádu
```

## ▶️ Spuštění

```bash
python main.py
```

### Funkce skriptu

✅ Načte stránku závodu  
✅ Přihlásí se do systému v určený čas  
✅ Automaticky vyplní registrační formulář  
✅ Ověří přesměrování na stránku úspěšné registrace  
✅ Odešle potvrzení na email  
✅ Informuje přítelkyni, že jedeš střílet 😎❤️ (Pošle jí na email datum závodu a název.)

## 📧 Notifikace

Skript používá `smtplib` pro odesílání přes SMTP (Gmail).  
Je potřeba mít zapnuté [dvoufázové ověření](https://myaccount.google.com/security) a vytvořený [App Password](https://support.google.com/accounts/answer/185833).
