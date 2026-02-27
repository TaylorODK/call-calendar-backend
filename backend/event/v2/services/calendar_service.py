import re
import requests
from datetime import datetime, timedelta
from dataclasses import dataclass
from requests import Response
from icalendar import Calendar as ICalendar
from typing import Any
from django.db.models import QuerySet
from django.utils import timezone
from event.models import Calendar, Event
from core.constants import PARSE_URL, PARSIN_AHEAD_DAYS
from core.exceptions import NotWorkingParseEvent
from event.v2.dto.event import ParsedEvent
from event.v2.services.event_service import EventService


@dataclass(frozen=True, kw_only=True, slots=True)
class CalendarService:
    """
    Парсинг календаря.
    """

    def __call__(self, cal: Calendar) -> None:
        parsing_url = f"{PARSE_URL}{cal.key}"
        events = self._send_request_to_url(parsing_url)
        calendar = self._get_icalendar_data(events.content)
        new_events = []
        for event in calendar.walk("VEVENT"):
            exdate = self._exdate_parsing(event=event)
            event_to_service = ParsedEvent(
                uid=str(event.get("uid")),
                title=str(event.get("summary", "")),
                description=str(event.get("description", "")),
                url_calendar=str(event.get("url", "")),
                date_from=event.get("dtstart").dt,
                date_till=event.get(
                    "dtend",
                ).dt
                if event.get("dtend")
                else None,
                rrule=event.get("RRULE") if event.get("RRULE") else None,
                exdate=exdate,
            )
            if event_to_service.date_from.date() > (
                timezone.localdate() + timedelta(days=PARSIN_AHEAD_DAYS)
            ):
                continue
            event_service = EventService()
            serviced_event = event_service(
                event=event_to_service,
                calendar=cal,
            )
            if serviced_event:
                new_events.append(serviced_event.event)
            else:
                continue
        self._delete_events_not_in_calendar(cal, new_events)

    def _delete_events_not_in_calendar(
        self,
        cal: Calendar,
        new_events: list[Event],
    ) -> None:
        """
        Проверка наличия мероприятий из БД
        в списке мероприятий, который вернул парсинг,
        если мероприятия нет в календаре, то оно удаляется
        из БД.
        """
        current_events = self._get_current_events_for_calendar(cal=cal)
        for current_event in current_events:
            if current_event not in new_events:
                current_event.is_active = False
                current_event.save(update_fields=["is_active"])

    def _send_request_to_url(
        self,
        parsing_url: str,
    ) -> Response:
        """
        Отправка запроса на получение данных календаря.
        """

        try:
            events = requests.get(parsing_url)
            events.raise_for_status()
        except requests.exceptions.RequestException:
            raise NotWorkingParseEvent
        return events

    def _get_current_events_for_calendar(
        self,
        cal: Calendar,
    ) -> QuerySet[Event]:
        """
        Запрос в БД на получения списка мероприятий
        на текущую дату.
        """

        return Event.objects.filter(
            calendar=cal,
            date_from__gte=timezone.localdate(),
        )

    def _get_icalendar_data(
        self,
        content: bytes,
    ) -> Any:
        """
        Извлечентн данных из ICalendar
        """

        return ICalendar.from_ical(content)

    def _exdate_parsing(
        self,
        event: ICalendar.events,
    ) -> list[Any]:
        """
        Проверка наличия поля EXDATE в регулярных мероприятиях.
        Если в какой-либо день регулярное мероприятие отменяется, то
        в данных события пояляется поле
        "EXDATE;TZID=Europe/Moscow:20251230T140000"
        На каждую отмену мероприятия по 1 строке. Данные извлекаются списком
        , приводятся к формату str и с помощью регулярного выражения
        извлекаются даты из строк. Список дат от текущего дня включительно
        возвращается в переменную exdate в parsed_event. Если дат не
        обнаружено, возвращается пустой список.
        """

        exdates = []
        exdate_prop = event.get("EXDATE")
        date_search_pattern = r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}[+-]\d{2}:\d{2}"
        if exdate_prop:
            dates_list = re.findall(date_search_pattern, str(exdate_prop))
            for dates in dates_list:
                if datetime.fromisoformat(dates).date() < timezone.localdate():
                    continue
                exdates.append(datetime.fromisoformat(dates).date())
        return exdates
