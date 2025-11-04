cd %appdata%
git clone https://github.com/joudar11/registrator_zavodu_2
cd ./registrator_zavodu_2
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m playwright install
IF NOT EXIST data.py copy data_sample.py data.py
