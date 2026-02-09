from dataclasses import dataclass


@dataclass(frozen=True)
class ParsedRule:
    FREQ: str | None
    BYDAY: str | None
    INTERVAL: int
    UNTIL: str | None
