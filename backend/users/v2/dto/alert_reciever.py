from dataclasses import dataclass
from core.enums import TypeReceiverEnums
from event.v2.dto import PreparedData
from event.models import GroupChat
from users.models import User


@dataclass(frozen=True, kw_only=True, slots=True)
class AlerReceiver:
    user_id: str | None
    group_id: str | None


@dataclass(frozen=True, kw_only=True, slots=True)
class PreparedAlertData:
    prepared_data: PreparedData
    type_receiver: TypeReceiverEnums
    receiver: User | GroupChat
