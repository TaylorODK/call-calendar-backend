from dataclasses import dataclass


@dataclass(slots=True, frozen=True, kw_only=True)
class RequestForCalendar:
    telegram_id: str | None
    chat_id: str | None
