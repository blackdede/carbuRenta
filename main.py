from datetime import datetime, timedelta
import re
import xml.etree.cElementTree as ET
from tqdm import tqdm
import concurrent.futures
import requests
from models.GasStation import GasStation
from models.HoursRange import HoursRange
from models.OpeningHours import OpeningHours

GRAPH_DIR = "graph_data/"

def get_name_station(id):
    response = requests.get(f"https://www.prix-carburants.gouv.fr/map/recuperer_infos_pdv/{id}", headers={"x-requested-with": "XMLHttpRequest"})

    if response.status_code == 200:
        html_content = response.text

        pattern = re.compile(r'<strong>(.*?)</strong>', re.DOTALL)
        match = pattern.search(html_content)

        if match:
            strong_text = match.group(1)
            return strong_text
    return None

def get_station_name(station_id):
    return station_id, get_name_station(station_id)

def parse_data() -> None:
    file_name = "PrixCarburants_annuel_2023.xml"
    print("Loading the file")
    tree = ET.parse(file_name)
    root = tree.getroot()
    print("Send API request for each station name")
    gas_stations = []
    count = 0
    maxx = 1000
    station_ids = [int(pdv.get("id")) for pdv in root]
    station_ids = station_ids[:maxx]
    
    with concurrent.futures.ThreadPoolExecutor(150) as executor:
        station_names = list(tqdm(executor.map(get_station_name, station_ids), total=len(station_ids)))
    
    for pdv, (station_id, name) in zip(root, station_names):
        address = pdv.find("adresse").text
        latitude = (pdv.get("latitude"))
        longitude = (pdv.get("longitude"))
        postal_code = pdv.get("cp")
        city = pdv.find("ville").text
        opening_hours = None
        is_always_open = False
        gas_price_history = {}

        horaires_element = pdv.find("horaires")
        if horaires_element is not None:
            always_open = "automate-24-24" in horaires_element.attrib
            days = {}
            for day in horaires_element:
                day_id = int(day.get("id"))
                if day.get("ferme") == "1" or day.find("ouverture") is None:
                    hours_range = None  # Closed on this day
                else:
                    # Assuming that the format is HH:MM-HH:MM
                    opening_time = day.find("horaire").get("ouverture")
                    closing_time = day.find("horaire").get("fermeture")

                    start_time = datetime.strptime(opening_time, "%H.%M").time()
                    end_time = datetime.strptime(closing_time, "%H.%M").time()
                    hours_range = HoursRange(hour_start=start_time, hour_end=end_time)

                days[day_id] = hours_range

            opening_hours = OpeningHours(days)

        is_always_open = always_open

        # Parse fuel prices
        for prix_element in pdv.findall("prix"):
            if prix_element.attrib:
                fuel_type = prix_element.get("nom")
                price = float(prix_element.get("valeur"))
                update_date = prix_element.get("maj")

                if fuel_type not in gas_price_history:
                    gas_price_history[fuel_type] = {}

                gas_price_history[fuel_type][update_date] = price

        gas_station = GasStation(
            id=station_id,
            name=name,
            address=address,
            latitude=latitude,
            longitude=longitude,
            postal_code=postal_code,
            city=city,
            is_always_open=is_always_open,
            opening_hours=opening_hours,
            gas_price_history=gas_price_history,
        )

        gas_stations.append(gas_station)

        count += 1
        if count > maxx:
            break

    numbers_of_stations = len([child.attrib["id"] for child in root])
    print(numbers_of_stations)
    return gas_stations

def create_json_heatmap(gas_stations):
    result_json = {"stations": []}
    print("Saving result to JSON")
    with tqdm(total=len(gas_stations), desc="Processing gas stations") as pbar:
        for gas_station in gas_stations:
            station_json = {
                "id": gas_station.id,
                "name": gas_station.name,
                "address": gas_station.address,
                "latitude": gas_station.latitude,
                "longitude": gas_station.longitude,
                "postal_code": gas_station.postal_code,
                "city": gas_station.city,
                "is_always_open": gas_station.is_always_open,
                "carburants": {},
            }

            current_datetime = datetime.now()
            for fuel_type, price_history in gas_station.gas_price_history.items():
                station_json["carburants"][fuel_type] = []
                prices = [
                    price_history.get(
                        (current_datetime - timedelta(days=day_number)).strftime("%Y-%m-%d"),
                        station_json["carburants"][fuel_type][-1] if station_json["carburants"][fuel_type] else 0,
                    )
                    for day_number in range(365)
                ]
                station_json["carburants"][fuel_type] = prices

            result_json["stations"].append(station_json)
            pbar.update(1)

    import json
    # Save to file
    with open(GRAPH_DIR + 'data.json', 'w') as outfile:
        json.dump(result_json, outfile)


if __name__ == "__main__":
    from time import perf_counter
    debut = perf_counter()

    gas_stations = parse_data()

    create_json_heatmap(gas_stations)

    fin = perf_counter()
    print(f"Temps d'exécution : {fin - debut}s")
