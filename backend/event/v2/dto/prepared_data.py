from dataclasses import dataclass


@dataclass
class PreparedData:
    data: list
    message: str | None
    telegram_id: str
