from datetime import datetime
from dataclasses import dataclass


@dataclass(slots=True, frozen=True, kw_only=True)
class ParsedEvent:
    """
    Формат данных, ожидаемый для получения в результате
    парсинга календаря. для date_till и rrule допускается
    null.
    """

    uid: str
    title: str
    description: str
    url_calendar: str
    date_from: datetime
    date_till: datetime | None
    rrule: dict | None
    exdate: list[datetime | None]
