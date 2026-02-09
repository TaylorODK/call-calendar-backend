from dataclasses import dataclass
from datetime import date, datetime


@dataclass(frozen=True)
class RegularEventDates:
    today: date
    week_number: int
    new_date_from: datetime
    new_date_till: datetime | None
    weeks_from_event_start: int
    days_from_start_event: int
