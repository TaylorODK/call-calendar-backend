from dataclasses import dataclass


@dataclass(slots=True, frozen=True, kw_only=True)
class ParsedRule:
    FREQ: str | None
    BYDAY: str | None
    INTERVAL: int
    UNTIL: str | None
