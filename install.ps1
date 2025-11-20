# Nastavení kódování pro české znaky
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host "🚀 Spouštím instalaci Registrátoru Závodů..." -ForegroundColor Cyan

# --- 1. Kontrola a instalace prerekvizit (Python a Git) ---
function Check-And-Install ($command, $wingetId, $name) {
    if (-not (Get-Command $command -ErrorAction SilentlyContinue)) {
        Write-Host "⚠️ $name není nainstalován. Pokouším se nainstalovat přes Winget..." -ForegroundColor Yellow
        winget install -e --id $wingetId --accept-source-agreements --accept-package-agreements
        
        # Refresh prostředí po instalaci, aby byl příkaz vidět
        $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
        
        if (-not (Get-Command $command -ErrorAction SilentlyContinue)) {
            Write-Host "❌ Nepodařilo se automaticky nainstalovat $name. Prosím nainstaluj ho ručně a spusť skript znovu." -ForegroundColor Red
            Read-Host "Stiskni Enter pro ukončení..."
            exit
        }
    } else {
        Write-Host "✅ $name je nainstalován." -ForegroundColor Green
    }
}

Check-And-Install "git" "Git.Git" "Git"
Check-And-Install "python" "Python.Python.3.12" "Python 3.12"

# --- 2. Příprava složky ---
$appData = $env:APPDATA
$repoDir = Join-Path $appData "registrator_zavodu_2"
$repoUrl = "https://github.com/joudar11/registrator_zavodu_2.git"

if (Test-Path $repoDir) {
    Write-Host "🔄 Složka existuje, provádím aktualizaci..." -ForegroundColor Cyan
    Set-Location $repoDir
    git fetch --all
    git reset --hard HEAD
    git pull
} else {
    Write-Host "📥 Klonuji repozitář..." -ForegroundColor Cyan
    Set-Location $appData
    git clone $repoUrl
    if (-not (Test-Path $repoDir)) {
        Write-Host "❌ Chyba při klonování." -ForegroundColor Red
        exit
    }
    Set-Location $repoDir
}

# --- 3. Virtuální prostředí a instalace balíčků ---
Write-Host "🐍 Nastavuji virtuální prostředí (.venv)..." -ForegroundColor Cyan
if (-not (Test-Path ".venv")) {
    python -m venv .venv
}

# Cesta k pythonu ve venv
$venvPython = ".\.venv\Scripts\python.exe"

Write-Host "📦 Instaluji/Aktualizuji balíčky..." -ForegroundColor Cyan
& $venvPython -m pip install --upgrade pip
& $venvPython -m pip install -r requirements.txt
& $venvPython -m playwright install

# --- 4. Konfigurace ---
if (-not (Test-Path "data.py")) {
    Write-Host "📄 Vytvářím data.py ze vzoru..." -ForegroundColor Yellow
    Copy-Item "data_sample.py" -Destination "data.py"
}

Write-Host ""
Write-Host "✅ Hotovo! Instalace byla úspěšná." -ForegroundColor Green
Write-Host "📂 Program je nainstalován v: $repoDir"
Write-Host ""
Read-Host "Stiskni Enter pro ukončení..."