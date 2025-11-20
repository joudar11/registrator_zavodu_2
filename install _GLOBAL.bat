@echo off
chcp 65001 >nul

cd %appdata%

IF EXIST "registrator_zavodu_2" (
    echo 🔄 Složka již existuje, provádím aktualizaci...
    cd registrator_zavodu_2
    git fetch --all
    git reset --hard HEAD
    git pull
) ELSE (
    echo 📥 Klonuji repozitář...
    git clone https://github.com/joudar11/registrator_zavodu_2
    cd registrator_zavodu_2
)

echo 📦 Instaluji/Aktualizuji balíčky globálně...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m playwright install

IF NOT EXIST data.py (
    echo 📄 Vytvářím data.py ze vzoru...
    copy data_sample.py data.py
)

echo ✅ Hotovo.
@PAUSE