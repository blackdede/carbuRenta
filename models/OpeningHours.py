from models.HoursRange import HoursRange


class OpeningHours:
    days: list[dict[HoursRange]]

    def __init__(self, days: list[dict[HoursRange]]):
        self.days = days

    def __str__(self):
        if not self.days:
            return "OpeningHours: No opening hours available."

        formatted_days = "\n".join(
            f"Day {day_id}: {hours_range}" if hours_range else f"Day {day_id}: Closed"
            for day_id, hours_range in self.days.items()
        )
        return f"OpeningHours:\n{formatted_days}"