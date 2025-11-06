set VIRTUAL_ENV_DISABLE_PROMPT=
call .venv\Scripts\activate.bat
python vysledky_zverejneny.py
call .venv\Scripts\deactivate.bat
@PAUSE