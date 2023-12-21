import datetime


class HoursRange:
    hour_start: datetime.time
    hour_end: datetime.time

    def __init__(self, hour_start: datetime.time, hour_end: datetime.time):
        self.hour_start = hour_start
        self.hour_end = hour_end

    def __str__(self):
        return f"{self.hour_start.strftime('%H:%M')} - {self.hour_end.strftime('%H:%M')}"