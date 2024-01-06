from models.HoursRange import HoursRange


class OpeningHours:
    """
    Represents the opening hours of a gas station for each day.

    Attributes:
    - days (list[dict[HoursRange]]): A list containing dictionaries where keys are day IDs (int) and values are
      instances of the `HoursRange` class representing the opening hours for that day.

    Methods:
    - __init__(self, days: list[dict[HoursRange]]): Initializes the OpeningHours object with the provided list of days.
    - __str__(self): Returns a formatted string representation of the opening hours.
    """
    days: list[dict[HoursRange]]

    def __init__(self, days: list[dict[HoursRange]]):
        self.days = days

    def __str__(self):
        """
        Returns a formatted string representation of the opening hours.

        Returns:
        - str: A formatted string showing the opening hours for each day.
        """
        if not self.days:
            return "OpeningHours: No opening hours available."

        formatted_days = "\n".join(
            f"Day {day_id}: {hours_range}" if hours_range else f"Day {day_id}: Closed"
            for day_id, hours_range in self.days.items()
        )
        return f"OpeningHours:\n{formatted_days}"
    
    def serialize(self):
        serialized_days = {
            str(day_id): hours_range.serialize() if hasattr(hours_range, 'serialize') and callable(getattr(hours_range, 'serialize')) else None
            for day_id, hours_range in self.days.items()
        }
        return serialized_days