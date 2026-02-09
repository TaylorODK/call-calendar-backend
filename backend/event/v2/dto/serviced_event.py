from dataclasses import dataclass
from django.db.models import QuerySet
from event.models import Event
from users.models import User


@dataclass(frozen=True)
class ServicedEvent:
    message: str | None
    event: Event
    users: QuerySet[User]
