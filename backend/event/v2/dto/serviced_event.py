from dataclasses import dataclass
from django.db.models import QuerySet
from event.models import Event
from users.models import User


@dataclass(slots=True, frozen=True, kw_only=True)
class ServicedEvent:
    message: str | None
    event: Event
    users: QuerySet[User]
