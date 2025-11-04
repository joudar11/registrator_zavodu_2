cd %appdata%
git clone https://github.com/joudar11/registrator_zavodu_2
cd ./registrator_zavodu_2
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m playwright install
if exist data_sample.py ren data_sample.py data.py
