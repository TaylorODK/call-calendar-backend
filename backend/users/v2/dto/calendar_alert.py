from dataclasses import dataclass
from users.v2.dto import BaseData


@dataclass(slots=True, frozen=True, kw_only=True)
class CalendarAlert(BaseData):
    message: str
