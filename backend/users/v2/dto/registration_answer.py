from dataclasses import dataclass
from users.v2.dto.registration_error import RegistrationError


@dataclass(kw_only=True, slots=True, frozen=True)
class RegistrationAnswer:
    can_send_code: bool
    error: RegistrationError | None
