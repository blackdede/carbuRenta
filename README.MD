# Installation

```sh
pip install -r requirements.txt

python get_datas.py
python main.py
```

# Informations

Data is retrieved and stored locally via the get_datas script. This may take a few minutes

To get the display afterwards, run main.py and go to ```http://127.0.0.1:8050/```

Data are downloaded statically for the year 2023 (https://donnees.roulez-eco.fr/opendata/annee/2023).
However, station company names are retrieved dynamically via prix-carburants.gouv.fr, methode get_name_station in get_datas.py

# Sources

Data from: https://www.prix-carburants.gouv.fr/rubrique/opendata/
