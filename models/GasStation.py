from models.OpeningHours import OpeningHours
from typing import Dict

class GasStation:
    """
    Represents a gas station with its details, including location, opening hours, and gas price history.

    Attributes:
    - id (int): The unique identifier of the gas station.
    - name (str): The name of the gas station.
    - address (str): The address of the gas station.
    - latitude (float): The latitude of the gas station location.
    - longitude (float): The longitude of the gas station location.
    - postal_code (str): The postal code of the gas station.
    - city (str): The city where the gas station is located.
    - opening_hours (OpeningHours): An instance of the OpeningHours class representing the gas station's opening hours.
    - is_always_open (bool): A boolean indicating if the gas station is always open.
    - gas_price_history (Dict[str, Dict[str, float]]): A dictionary representing the gas price history with fuel types
      as keys and nested dictionaries with dates and prices.

    Methods:
    - __init__(self, id: int, name: str, address: str, latitude: float, longitude: float, postal_code: str, city: str,
                is_always_open: bool = False, opening_hours: OpeningHours = None,
                gas_price_history: Dict[str, Dict[str, float]] = {}): Initializes the GasStation object with the
                provided attributes.
    - __str__(self): Returns a formatted string representation of the gas station.
    """
    id: int
    name: str
    address: str
    latitude: float
    longitude: float
    postal_code: str
    city: str
    opening_hours: OpeningHours
    is_always_open: bool
    gas_price_history: Dict[str, Dict[str, float]] # Dict[<fuel_type>, Dict[<date>, <price>]]
    
    
    def __init__(self, id: int, name: str, address: str, latitude: float, longitude: float, postal_code: str, city: str, is_always_open: bool = False, opening_hours: OpeningHours = None, gas_price_history: Dict[str, Dict[str, float]] = {}):
        self.id = id
        self.name = name
        self.address = address
        self.latitude = latitude
        self.longitude = longitude
        self.postal_code = postal_code
        self.city = city
        self.opening_hours = opening_hours
        self.is_always_open = is_always_open
        self.gas_price_history = gas_price_history
    
    def __str__(self):
        """
        Returns a formatted string representation of the gas station.

        Returns:
        - str: A formatted string showing the details of the gas station.
        """
        return f"GasStation(id={self.id}, name={self.name}, address={self.address}, latitude={self.latitude}, longitude={self.longitude}, postal_code={self.postal_code}, city={self.city}, is_always_open={self.is_always_open}, opening_hours={self.opening_hours}, gas_price_history={self.gas_price_history})"