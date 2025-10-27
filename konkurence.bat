chcp 65001 >nul
setlocal
set VIRTUAL_ENV_DISABLE_PROMPT=
call .venv\Scripts\activate.bat
python konkurence.py
call .venv\Scripts\deactivate.bat
@PAUSE
