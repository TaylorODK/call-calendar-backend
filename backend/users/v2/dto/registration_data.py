from dataclasses import dataclass
from users.v2.dto import BaseData


@dataclass(slots=True, frozen=True, kw_only=True)
class RegistrationData(BaseData):
    email: str
