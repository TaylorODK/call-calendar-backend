from datetime import datetime
from dataclasses import dataclass
from django.utils import timezone
from event.models import Event
from event.v2.dto import RegularEventDates
from core.constants import DATE_FORMAT_FOR_ALERTS
from core.enums import MessageEnums, StatusEnums


@dataclass(slots=True, frozen=True, kw_only=True)
class CreateMessageService:
    """
    Сервис по генерации сообщений.
    Сообщения делятся на 3 типа:
    - создание мероприятия;
    - изменение мероприятия;
    - удаление мероприятия.
    Мероприятие проверяется на следующие критерии
    - если создается регулярное мероприятие
    (а они создаются каждый день в 00:00) то возвращается
    False;
    - если дата созданного или измененнного
    мероприятия не в текущий день;
    """

    def __call__(
        self,
        event: Event,
        dates: RegularEventDates | None = None,
        changed_fields: dict | None = None,
        created: bool = False,
        deleted: bool = False,
    ) -> tuple[str, str]:
        message = ""
        status = StatusEnums.NO_STATUS
        if not self._check_event(
            event=event,
            dates=dates,
            changed_fields=changed_fields,
            created=created,
            deleted=deleted,
        ):
            return message, status
        message += self._message_title(event=event, created=created)
        if created:
            message += self._message_for_created_event(event=event)
            status = StatusEnums.CREATED
        elif changed_fields:
            message += self._message_for_updated_event(
                event=event,
                changed_fields=changed_fields,
            )
            status = StatusEnums.UPDATED
        elif deleted:
            message += self._message_for_deleted_event()
            status = StatusEnums.DELETED
            return message, status
        message += self._add_shortcut(event=event)
        return message, status

    def _check_event(
        self,
        event: Event,
        dates: RegularEventDates | None,
        changed_fields: dict | None,
        created: bool = False,
        deleted: bool = False,
    ) -> bool:
        """
        Проверка мероприятия.
        """

        if dates and created:
            return False
        elif (
            created or changed_fields
        ) and event.date_from.date() == timezone.localdate():
            return True
        elif deleted:
            return True
        return False

    def _message_title(
        self,
        event: Event,
        created: bool = False,
    ) -> str:
        """
        Подготовка заголовка для мероприятия.
        """

        if created:
            result = "📅 Новое мероприятие в календаре"
        else:
            result = "📅 Изменения в мероприятии"
        result += f" '{event.title}':\n\n"
        return result

    def _message_for_created_event(
        self,
        event: Event,
    ) -> str:
        """
        Подготовка тела сообщения для
        созданного мероприятия.
        """

        return f"   🕐 {event.time_for_event()}\n"

    def _message_for_updated_event(
        self,
        event: Event,
        changed_fields: dict,
    ) -> str:
        """
        Подготовка тела сообщения для
        измененного мероприятия.
        """

        result = ""
        for field, value in changed_fields.items():
            if field == "date_from":
                value = self._clean_date_for_message(event.date_from)
            if field == "date_till":
                continue
            result += f"{MessageEnums[field].value} {value} \n"
        return result

    def _message_for_deleted_event(
        self,
    ) -> str:
        """
        Подготовка тела сообщения для
        удаленного мероприятия.
        """

        return MessageEnums.deleted.value

    def _add_shortcut(self, event: Event) -> str:
        """
        Добавление в сообщение ссылки на созвон.
        """

        result = ""
        if event.url_for_event():
            event_url = event.url_for_event().strip().rstrip('\\"')
            result += f"   🔗 <a href='{event_url}'>Ссылка</a>\n\n"
        else:
            result += "   🔗 Ссылка не предоставлена.\n\n"
        return result

    def _clean_date_for_message(
        self,
        date: datetime,
    ) -> str:
        """
        Приведение даты мероприятия в
        читаемый формат
        """

        return date.strftime(DATE_FORMAT_FOR_ALERTS)
