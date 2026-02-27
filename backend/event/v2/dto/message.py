from dataclasses import dataclass
from django.db.models import QuerySet
from event.models import GroupChat
from users.models import User


@dataclass(slots=True, frozen=True, kw_only=True)
class BaseMessage:
    message: str
    event_id: int


@dataclass(slots=True, frozen=True, kw_only=True)
class MessageToPrepare(BaseMessage):
    status: str | None
    users: QuerySet[User] | tuple[User]
    groups: QuerySet[GroupChat] | tuple[User]
    old_fields: dict | None = None


@dataclass(slots=True, frozen=True, kw_only=True)
class MessageForSending(BaseMessage):
    users_tg_ids: list
    groups_tg_ids: list
