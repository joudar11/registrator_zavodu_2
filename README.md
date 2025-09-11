# Automatická registrace na LOS závod

Vylepšený [skript](https://github.com/joudar11/registrator_zavodu), který automaticky provádí registraci na závod LOS Lex pomocí knihovny Playwright. Nevyžaduje žádné zadávání údajů v konzoli – vše si načítá z konfiguračního souboru `data.py`.

Součástí je:
- Časovaná registrace s přesností na sekundy.
- Automatické přihlášení do systému.
- Odeslání potvrzovacího e-mailu s .ics událostí.
- Notifikace přítelkyni ❤️.
- Logování do souboru.
- Automatické opakování registrace při selhání (max. 25 pokusů - lze změnit v proměnné "LIMIT" v main.py).
- Pokud zvolená divize nebyla v závodě otevřena, skript automaticky zvolí první možnou. Závodník tak nepřijde o místo a následně registraci může upravit.
- Pokud je zvolený squad plný, skript automaticky zkusí zvolit první volný squad v rozsahu 1 - 100.
- Ošetření většiny možných chyb od neodpovídajícího serveru po selhání emailového serveru.
- Pokud závodník prosral začátek registrace a závod je plný, lze spustit soubor plny_zavod.py, který každých 30 minut kontroluje obsazenost a v případě volného místa spouští registrační skript. 

## 📦 Požadavky

- Python 3.12.6
- `playwright`
- Běžící Proton Bridge (Lze upravit pro Gmail - viz historii úprav [zde](https://github.com/joudar11/registrator_zavodu_2/commit/97be62a061d772fd1411141ded62da301ff4a896))
- Konfigurační soubor `data.py` s následujícím obsahem:

```python
JMENO = "Jan Novák"
# Celé jméno závodníka
CISLO_DOKLADU = "AL123456"
# Číslo ZP
CLENSKE_ID = "ABcdEfGh"
# LEX ID (volitelné - pokud nemáš, napiš None)
DIVIZE = "Pistole"
# Název divize přesně dle výběru na webu
URL = "https://www.loslex.cz/contest/292"
# URL konkrétního závodu
LOGIN = "jan.novak"
# Email pro přihlášení i notifikace
HESLO = "tajneheslo123"
# Heslo do systému LOS Lex
DATUM_CAS_REGISTRACE = "2025-06-15 20:00:00"
# Datum otevření registrace. Formát musí být RRRR-MM-DD HH:MM:SS
SQUAD = 1
# Číslo squadu, nebo r (v uvozovkách pro squad ROZHODČÍ)
EMAIL_P = "tajneheslo123"
# Proton Bridge heslo pro SMTP
EMAIL_U = "jan.novak@pm.me"
# Proton Bridge username odesílatele
MZ = False
# Mimo závod
ZACATECNIK = False
# Začátečník
STAVITEL = False
# Stavitel
ROZHODCI = False
# Rozhodčí
POZNAMKA = "..."
# Poznámka (volitelné) - Může být None
PRITELKYNE = "jana.novakova@pm.me"
# Email přítelkyně (None, pokud jsi single)
JMENO_PRITELKYNE = "Jana"
# Křestní jméno přítelkyně v prvním pádu
RANDOM_WAIT = False
# Zda má skript před odesláním registrace čekat náhodný počet sekund mezi 2 a 3, aby registrace vypadala věrohodněji
INTERVAL = 1800
# V jakém intervalu v sekundách se má kontrolovat volné místo na plném závodě (s tímto údajem se pracuje pouze v plny_zavod.py)
```

## ▶️ Spuštění

- Pokud registrace ještě nezačala:

```bash
python main.py
```

- Pokud registrace běží, ale závod je plný:
```bash
python plny_zavod.py
```

### Funkce skriptu

- Načte stránku závodu
- Přihlásí se do systému v určený čas
- Automaticky vyplní registrační formulář
- Pokud zvolená divize neexistuje, zvolí první možnou dostupnou
- Pokud zvolený squad neexistuje, zvolí první dostupný
- Zaznamená každý pokus do textového logu (adresář logs/)
- Opakuje registraci až 25× v případě selhání
- Ověří přesměrování na stránku úspěšné registrace
- Odešle potvrzení na email
- Informuje přítelkyni, že jedeš střílet 😎❤️ (Pošle jí na email datum závodu a název.)

## 📧 Notifikace

Skript používá `smtplib` pro odesílání přes SMTP (Proton Bridge).
