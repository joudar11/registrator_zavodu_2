@echo off
setlocal EnableExtensions EnableDelayedExpansion

rem === 1) Předpoklady ===
where git >nul 2>&1 || (echo [ERROR] Git neni v PATH. Nainstaluj Git. & exit /b 1)
where python >nul 2>&1 || (echo [WARN] 'python' neni v PATH, zkusim 'py'.)

cd /d "%APPDATA%" || (echo [ERROR] Nelze prepnout do %%APPDATA%% & exit /b 1)
set "REPO=registrator_zavodu_2"

rem === 2) Klon nebo update ===
if not exist "%REPO%\.git" (
  git clone https://github.com/joudar11/registrator_zavodu_2 "%REPO%" || (echo [ERROR] Git clone selhal & exit /b 1)
) else (
  pushd "%REPO%"
  git fetch --all && git reset --hard HEAD && git pull || (echo [WARN] Git update selhal)
  popd
)

cd /d "%APPDATA%\%REPO%" || (echo [ERROR] Repo slozka nenalezena & exit /b 1)

rem === 3) Venv (funguje s python i py) ===
if not exist ".venv\Scripts\activate.bat" (
  python -m venv .venv 2>nul || py -3 -m venv .venv || (echo [ERROR] Vytvoreni venv selhalo. & exit /b 1)
)

call ".venv\Scripts\activate.bat" || (echo [ERROR] Aktivace venv selhala. & exit /b 1)
set VIRTUAL_ENV_DISABLE_PROMPT=

rem === 4) Instalace balicku ===
python -m pip install --upgrade pip || (echo [ERROR] Upgrade pip selhal. & exit /b 1)
python -m pip install -r requirements.txt || (echo [ERROR] Instalace requirements selhala. & exit /b 1)

rem Pokud by v requirements nebyl playwright, doinstaluj:
python -c "import pkgutil,sys; sys.exit(0 if pkgutil.find_loader('playwright') else 1)" || pip install playwright || (echo [ERROR] Instalace playwright selhala. & exit /b 1)

rem Prohlizece pro Playwright:
playwright install || (echo [ERROR] 'playwright install' selhalo. & exit /b 1)

rem === 5) data.py jen pokud chybi ===
if not exist data.py if exist data_sample.py copy /Y data_sample.py data.py >nul

call ".venv\Scripts\deactivate.bat"
echo [OK] Instalace dokoncena.
exit /b 0