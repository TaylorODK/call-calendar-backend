import requests
from dataclasses import dataclass
from requests import Response
from icalendar import Calendar as ICalendar
from django.db.models import QuerySet
from django.utils import timezone
from event.models import Calendar, Event
from event.v2.dto import ServicedEvent
from core.constants import PARSE_URL
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
        current_events = self._get_current_events_for_calendar(cal=cal)
        new_events = []
        for event in calendar.walk("VEVENT"):
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
            )
            event_service = EventService()
            serviced_event = event_service(
                event=event_to_service,
                calendar=cal,
            )
            if serviced_event:
                new_events.append(serviced_event.event)
            else:
                continue
        self._delete_events_not_in_calendar(current_events, new_events)

    def _delete_events_not_in_calendar(
        self,
        current_events: list,
        new_events: list,
    ) -> None:
        for current_event in current_events:
            if current_event not in new_events:
                if current_event.date_from.date() == timezone.localdate():
                    message = f"Мероприятие '{current_event.title}' удалено из графика"
                    users = current_event.users.all()
                    from event.tasks import send_telegram_message

                    send_telegram_message(
                        ServicedEvent(
                            message=message,
                            event=current_event,
                            users=users,
                        ),
                    )
                current_event.delete()

    def _send_request_to_url(
        self,
        parsing_url: str,
    ) -> Response:
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
        return Event.objects.filter(
            calendar=cal,
            date_from__gt=timezone.now(),
        )

    def _get_icalendar_data(
        self,
        content: bytes,
    ):
        return ICalendar.from_ical(content)
