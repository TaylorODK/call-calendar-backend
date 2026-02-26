from dataclasses import dataclass
from django.db.models import QuerySet
from event.models import Event, GroupChat
from users.models import User


@dataclass(slots=True, kw_only=True)
class ServicedEvent:
    message: str | None
    event: Event
    users: QuerySet[User]
    groups: QuerySet[GroupChat]
    status: str | None
    olf_fields: dict | None = None
