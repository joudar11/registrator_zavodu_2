cd %appdata%
git clone https://github.com/joudar11/registrator_zavodu_2
cd ./registrator_zavodu_2
python -m venv .venv
. venv\Scripts\Activate.ps1
pip install -r requirements.txt
playwright install
