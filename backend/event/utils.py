import requests
from icalendar import Calendar as ICalendar
from django.utils import timezone
from event.models import Calendar, Event


def update_or_create_event(
    uid: str,
    title: str,
    description: str,
    url_calendar: str,
    date_from: str,
    date_till: str | None,
    cal: Calendar,
) -> Event:
    try:
        event = Event.objects.get(uid=uid)
        changed_fields = []
        if event.title != title:
            event.title = title
            changed_fields.append("title")
        if event.description != description:
            event.description = description
            changed_fields.append("description")
        if event.url_calendar != url_calendar:
            event.url_calendar = url_calendar
            changed_fields.append("url")
        if event.date_from != date_from:
            event.date_from = date_from
            changed_fields.append("date_from")
        if event.date_till != date_till:
            event.date_till = date_till
            changed_fields.append("date_till")
        if changed_fields:
            event.save(update_fields=changed_fields)
    except Event.DoesNotExist:
        event = Event.objects.create(
            uid=uid,
            title=title,
            description=description,
            url_calendar=url_calendar,
            date_from=date_from,
            date_till=date_till,
            calendar=cal,
        )
    event.check_for_star_slash()
    event.save(update_fields=["star", "slash", "all_event"])
    return event


def parse_ics(cal: Calendar):
    url = f"https://calendar.yandex.ru/export/ics.xml?private_token={cal.key}"
    events = requests.get(url)
    # events.raise_for_status() TODO: Добавить логгер для исключения
    calendar = ICalendar.from_ical(events.content)
    for event in calendar.walk("VEVENT"):
        uid = str(event.get("uid"))
        title = str(event.get("summary", ""))
        description = str(event.get("description", ""))
        url_calendar = str(event.get("url", ""))
        date_from = event.get("dtstart").dt
        date_till = event.get("dtend").dt if event.get("dtend") else None
        if date_from <= timezone.now():
            continue
        event = update_or_create_event(
            uid,
            title,
            description,
            url_calendar,
            date_from,
            date_till,
            cal,
        )
