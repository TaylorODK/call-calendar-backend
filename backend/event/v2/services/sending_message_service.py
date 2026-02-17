from dataclasses import dataclass
from django.db.models import QuerySet
from django.utils import timezone
from event.models import Event, GroupChat
from event.v2.dto import MessageToPrepare, MessageForSending
from core.exceptions import NotFoundEvent
from core.enums import StatusEnums
from users.models import User


@dataclass(slots=True, frozen=True, kw_only=True)
class SendingMessageService:
    """
    Сервис по отправке сообщений в адрес пользователей
    и групп, связанных с мероприятием.
    """

    def __call__(
        self,
        message_to_prepare: MessageToPrepare,
    ) -> None:
        event = self._check_event(event_id=message_to_prepare.event_id)
        users_list = self._prepare_users_list(
            users=message_to_prepare.users,
        )
        groups_list = self._prepare_groups_list(groups=message_to_prepare.groups)
        if (
            not self._check_if_actual(
                event=event,
            )
            or message_to_prepare.status == StatusEnums.NO_STATUS
        ):
            return None
        from event.tasks import send_telegram_message

        prepared_message = MessageForSending(
            message=message_to_prepare.message,
            event_id=message_to_prepare.event_id,
            users_tg_ids=users_list,
            groups_tg_ids=groups_list,
        )
        send_telegram_message(prepared_message=prepared_message)

    def _check_event(self, event_id: int) -> Event:
        """
        Проверка event_id на существование мероприятия.
        """

        try:
            event = Event.objects.filter(id=event_id).first()
        except Event.DoesNotExist:
            raise NotFoundEvent
        return event

    def _check_if_actual(
        self,
        event: Event,
    ) -> bool:
        """
        Проверка на совпадение даты
        меропрятия с текущим днем.
        """

        if event.date_from.date() == timezone.localdate():
            return True
        return False

    def _prepare_users_list(self, users: QuerySet[User]) -> list:
        """
        Подготовка списка telegram_id пользователей для рассылки.
        """

        return [user.telegram_id for user in users]

    def _prepare_groups_list(self, groups: QuerySet[GroupChat]) -> list:
        """
        Подготовка списка chat_id групп для рассылки.
        """

        return [group.chat_id for group in groups]
