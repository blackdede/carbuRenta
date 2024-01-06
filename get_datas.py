from datetime import datetime, timedelta
import os
import re
import xml.etree.cElementTree as ET
import zipfile
from tqdm import tqdm
import concurrent.futures
import requests
from models.GasStation import GasStation
from models.HoursRange import HoursRange
from models.OpeningHours import OpeningHours
import json


GRAPH_DIR = "graph_data/"
# Use a session to keep the connection alive and speed up the requests
session = requests.Session()
pattern = re.compile(r'<strong>(.*?)</strong>', re.DOTALL)

def download_file() -> None:
    """
    Download the XML file from the government website and save it to disk.

    Returns:
    - str: The file name of the downloaded XML file.
    """
    
    file_name_zip = "PrixCarburants_annuel_2023.zip"
    file_name_xml = "PrixCarburants_annuel_2023.xml"
    url = "https://donnees.roulez-eco.fr/opendata/annee/2023"
    print("Downloading the file")
    response = session.get(url)
    if response.status_code == 200:
        with open(file_name_zip, 'wb') as f:
            f.write(response.content)
        
        # Extract the contents of the zip file
        with zipfile.ZipFile(file_name_zip, 'r') as zip_ref:
            zip_ref.extractall()
        
        os.remove(file_name_zip)
    else:
        raise Exception("Error while downloading the file")
    return file_name_xml

def get_name_station(id) -> str or None:
    """
    Retrieve the name of a gas station using its ID.

    Parameters:
    - id (str): The ID of the gas station.

    Returns:
    - str or None: The name of the gas station, or None if not found.
    """
    
    try:
        response = session.get(f"https://www.prix-carburants.gouv.fr/map/recuperer_infos_pdv/{id}", headers={"x-requested-with": "XMLHttpRequest"})
        if response.status_code == 200:
            html_content = response.text
            
            match = pattern.search(html_content)

            if match:
                strong_text = match.group(1)
                return strong_text
    except:
        return None

def get_station_name(station_id):
    """
    Wrapper function for retrieving the name of a gas station.

    Parameters:
    - station_id (str): The ID of the gas station.

    Returns:
    - Tuple: A tuple containing the station ID and its name.
    """
    return station_id, get_name_station(station_id)

def get_coordinate(angle: str, isLongitude: bool) -> float:
    """
    Convert a string representing an angle to a float.

    Parameters:
    - angle (str): The angle in string format.
    - isLongitude (bool): True if the angle represents longitude, False if it represents latitude.

    Returns:
    - float: The converted angle as a float.
    
    >>> get_coordinate("4620100", False)
    46.201
    >>> get_coordinate("519800", True)
    5.198
    >>> get_coordinate("4584829.0858556", True)
    45.84829
    >>> get_coordinate("-105000", True)
    -1.05
    >>> get_coordinate("-64673.000000005", True)
    -0.64673
    
    """
    factor = 100000 if isLongitude else 10000 # beacause it's PTV_GEODECIMAL format
    if not isLongitude and len(angle) == 7: # if latitude with 7 digits it's like latitude in PTV_GEODECIMAL format
        factor = 100000

    return round(float(angle)/factor,5)


def parse_data(file_name) -> None:
    """
    Parse the XML file and extract information about gas stations.

    Parameters:
    - file_name (str): The name of the XML file.

    Returns:
    - list: List of GasStation objects.
    """
    
    print("Loading the file into memory")
    tree = ET.parse(file_name)
    root = tree.getroot()
    print("Send API request for each station name")
    gas_stations = []
    count = 0
    station_ids = [int(pdv.get("id")) for pdv in root]
    maxx = 99999 # For debug if needed
    station_ids = station_ids[:maxx]
    
    with concurrent.futures.ThreadPoolExecutor(150) as executor:
        station_names = list(tqdm(executor.map(get_station_name, station_ids), total=len(station_ids)))
    
    with tqdm(total=len(station_names), desc="Processing gas stations") as pbar:
        for pdv, (station_id, name) in zip(root, station_names):
            try:
                address = pdv.find("adresse").text
                latitude = get_coordinate(pdv.get("latitude"), 2)
                longitude = get_coordinate(pdv.get("longitude"), 1)
                postal_code = pdv.get("cp")
                city = pdv.find("ville").text
                opening_hours = None
                is_always_open = False
                gas_price_history = {}
            except:
                continue

            horaires_element = pdv.find("horaires")
            if horaires_element is not None:
                always_open = "automate-24-24" in horaires_element.attrib
                days = {}
                for day in horaires_element:
                    day_id = int(day.get("id"))
                    if day.get("ferme") == "1" or day.find("horaire") is None:
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
                    update_date = str(datetime.strptime(prix_element.get("maj"), "%Y-%m-%dT%H:%M:%S").strftime("%Y-%m-%d"))

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

            # For debug if needed
            count += 1
            if count > maxx:
                break
            
            pbar.update(1) 

    return gas_stations

def create_json(gas_stations):
    """
    Create a JSON file from the information about gas stations.

    Parameters:
    - gas_stations (list): List of GasStation objects.
    """
    
    current_datetime = datetime.now()
    date_strings = [(current_datetime - timedelta(days=day_number)).strftime("%Y-%m-%d") for day_number in range(365, 0, -1)]
    result_json = {"stations": []}
    with tqdm(total=len(gas_stations), desc="Saving to JSON gas stations") as pbar:
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
                "opening_hours": gas_station.opening_hours.serialize() if gas_station.opening_hours else None,  # Serialize the OpeningHours object
                "carburants": {},
                "opening_dates": date_strings,
            }

            for fuel_type, price_history in gas_station.gas_price_history.items():
                station_json["carburants"][fuel_type] = []

                for date_key in date_strings:

                    # Check if the date is in the price history
                    if date_key in price_history:
                        price = price_history[date_key]
                    else:
                        # If the date is not in the history, use the previous value or 0 if there is no previous value
                        price = station_json["carburants"][fuel_type][-1] if station_json["carburants"][fuel_type] else 0

                    station_json["carburants"][fuel_type].append(price)

            result_json["stations"].append(station_json)
            pbar.update(1)

    # Check if the folder exist
    if not os.path.exists(GRAPH_DIR):
        os.makedirs(GRAPH_DIR)

    # Save to file
    with open(os.path.join(GRAPH_DIR, 'data.json'), 'w') as outfile:
        json.dump(result_json, outfile)


if __name__ == "__main__":
    """
    Main block for executing the download, parsing, and JSON creation process.
    """
    
    import doctest
    doctest.testmod()
    
    from time import perf_counter
    debut = perf_counter()
    
    file_name = download_file()
    gas_stations = parse_data(file_name)
    create_json(gas_stations)

    fin = perf_counter()
    print(f"Temps d'exécution : {fin - debut}s")
    
    