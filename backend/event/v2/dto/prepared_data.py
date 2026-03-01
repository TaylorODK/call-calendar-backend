from dataclasses import dataclass


@dataclass(slots=True, frozen=True, kw_only=True)
class PreparedData:
    data: list
    message: str | None
    telegram_id: str
