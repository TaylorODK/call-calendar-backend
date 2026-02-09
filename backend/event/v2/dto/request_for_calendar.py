from dataclasses import dataclass


@dataclass(frozen=True)
class RequestForCalendar:
    telegram_id: str
    chat_id: str
