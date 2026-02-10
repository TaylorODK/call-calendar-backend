from dataclasses import dataclass


@dataclass(slots=True, frozen=True, kw_only=True)
class BaseData:
    telegram_id: str
