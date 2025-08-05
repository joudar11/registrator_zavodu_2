# Automatická registrace na LOS závod

Vylepšený [skript](https://github.com/joudar11/registrator_zavodu), který automaticky provádí registraci na závod LOS Lex pomocí knihovny Playwright. Nevyžaduje žádné zadávání údajů v konzoli – vše si načítá z konfiguračního souboru `data.py`.

Součástí je:
- Časovaná registrace s přesností na sekundy
- Automatické přihlášení do systému
- Odeslání potvrzovacího e-mailu
- Notifikace přítelkyni ❤️
- Logování do souboru
- Automatické opakování registrace při selhání (max. 25 pokusů)
- Pokud zvolená divize nebyla v závodě otevřena, skript automaticky zvolí první možnou. Závodník tak nepřijde o místo a následně registraci může upravit. Stejný postup je uplatněn na squady.
- Ošetření většiny možných chyb od neodpovídajícího serveru po selhání emailového serveru. 

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
# Zda má skript předs odesláním refistrace čekat náhodný počet sekund mezi 2 a 3, aby registrace vypadala věrohodněji
```

## ▶️ Spuštění

```bash
python main.py
```

### Funkce skriptu

- ✅ Načte stránku závodu
- ✅ Přihlásí se do systému v určený čas
- ✅ Automaticky vyplní registrační formulář
- ✅ Pokud zvolená divize neexistuje, zvolí první možnou dostupnou
- ✅ Pokud zvolený squad neexistuje, zvolí squad č. 1
- ✅ Zaznamená každý pokus do textového logu (adresář logs/)
- ✅ Opakuje registraci až 50× v případě selhání
- ✅ Ověří přesměrování na stránku úspěšné registrace
- ✅ Odešle potvrzení na email
- ✅ Informuje přítelkyni, že jedeš střílet 😎❤️ (Pošle jí na email datum závodu a název.)

## 📧 Notifikace

Skript používá `smtplib` pro odesílání přes SMTP (Proton Bridge).
