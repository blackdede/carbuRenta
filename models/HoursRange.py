import datetime


class HoursRange:
    """
    Represents a range of hours, indicating the start and end times.

    Attributes:
    - hour_start (datetime.time): The starting time of the hours range.
    - hour_end (datetime.time): The ending time of the hours range.

    Methods:
    - __init__(self, hour_start: datetime.time, hour_end: datetime.time): Initializes the HoursRange object with
      the provided start and end times.
    - __str__(self): Returns a formatted string representation of the hours range.
    """
    hour_start: datetime.time
    hour_end: datetime.time

    def __init__(self, hour_start: datetime.time, hour_end: datetime.time):
        self.hour_start = hour_start
        self.hour_end = hour_end

    def __str__(self):
        """
        Returns a formatted string representation of the hours range.

        Returns:
        - str: A formatted string showing the hours range in the format 'HH:MM - HH:MM'.
        """
        return f"{self.hour_start.strftime('%H:%M')} - {self.hour_end.strftime('%H:%M')}"
    
    def serialize(self):
        """
        Serialize the HoursRange object to a format suitable for JSON.

        Returns:
        - dict: A dictionary representation of the serialized HoursRange object.
        """
        return {
            "hour_start": self.hour_start.strftime('%H:%M'),
            "hour_end": self.hour_end.strftime('%H:%M')
        }