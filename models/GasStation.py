from models.OpeningHours import OpeningHours
from typing import Dict

class GasStation:
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
        return f"GasStation(id={self.id}, name={self.name}, address={self.address}, latitude={self.latitude}, longitude={self.longitude}, postal_code={self.postal_code}, city={self.city}, is_always_open={self.is_always_open}, opening_hours={self.opening_hours}, gas_price_history={self.gas_price_history})"