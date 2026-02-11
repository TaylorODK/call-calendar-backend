from dataclasses import dataclass


@dataclass(kw_only=True, slots=True, frozen=True)
class RegistrationError:
    error_message: str
    error_code: int
