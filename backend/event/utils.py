import re
import requests
from datetime import datetime
from typing import Optional
from icalendar import Calendar as ICalendar
from django.db.models import Q
from django.utils import timezone
from event.models import Calendar, Event
from users.models import User


def set_users_for_event(
    event: Event,
) -> None:
    cal = event.calendar
    event.check_for_star_slash()
    event.save(update_fields=["star", "slash", "all_event"])
    if bool(re.search(r"/\*$", event.title)):
        users = User.objects.filter(
            Q(show_star_events=True) | Q(show_slash_events=True),
            calendar=cal,
        )
    elif "*" in event.title:
        users = User.objects.filter(calendar=cal, show_star_events=True)
    elif bool(re.search(r"/$", event.title)):
        users = User.objects.filter(calendar=cal, show_slash_events=True)
    else:
        users = User.objects.filter(
            calendar=cal,
        )
    event.users.set(users)


def update_or_create_event(
    uid: str,
    title: str,
    description: str,
    url_calendar: str,
    date_from: datetime,
    date_till: Optional[datetime],
    cal: Calendar,
) -> Event | None:
    message = "Empty"
    subject = ""
    event, created = Event.objects.get_or_create(
        uid=uid,
        title=title,
        description=description,
        url_calendar=url_calendar,
        date_from=date_from,
        date_till=date_till,
        calendar=cal,
    )
    if not created:
        changed_fields = {}
        if event.title != title:
            event.title = title
            changed_fields["title"] = f"изменилась тема на '{title}'."
        if event.description != description:
            event.description = description
            changed_fields["description"] = f"изменилось описание {description}."
        if event.url_calendar != url_calendar:
            event.url_calendar = url_calendar
            changed_fields["url"] = f"изменилась ссылка в календаре {url_calendar}"
        if event.date_from != date_from:
            event.date_from = date_from
            changed_fields["date_from"] = f"изменилось время начала на {date_from}."
        if event.date_till != date_till:
            event.date_till = date_till
            changed_fields["date_till"] = f"изменилось время завершения на {date_till}."
        if changed_fields:
            fields_list = [field for field in changed_fields.keys()]
            event.save(update_fields=fields_list)
            if (
                event.date_from.date() == timezone.localdate()
                or date_from.date() == timezone.localdate()
            ):
                subject = "Изменения в мероприятии"
                message = f"{subject}: \n{". ".join(changed_fields.values())}"
    if created and date_from.date() == timezone.localdate():
        message = (
            f"Новое мероприятие: \n '{title}' ,"
            f" дата начала - {date_from.strftime("%Y-%m-%d %H:%M")}"
        )
        subject = "Новое мероприятие"
    set_users_for_event(event)
    if message != "Empty":
        from event.tasks import send_telegram_message

        send_telegram_message(message, subject, event)
    return event


def delete_events_not_in_calendar(current_events: list, new_events: list) -> None:
    for current_event in current_events:
        if current_event not in new_events:
            if current_event.date_from.date() == timezone.localdate():
                message = f"Мероприятие '{current_event.title}' удалено из графика"
                subject = "Удалено мероприятие"
                from event.tasks import send_telegram_message

                send_telegram_message(message, subject, event=current_event)
            current_event.delete()


def parse_ics(cal: Calendar) -> None:
    url = f"https://calendar.yandex.ru/export/ics.xml?private_token={cal.key}"
    events = requests.get(url)
    # events.raise_for_status() TODO: Добавить логгер для исключения
    calendar = ICalendar.from_ical(events.content)
    current_events = Event.objects.filter(
        date_from__gt=timezone.now(),
        calendar=cal,
    )
    new_events = []
    for event in calendar.walk("VEVENT"):
        uid = str(event.get("uid"))
        title = str(event.get("summary", ""))
        description = str(event.get("description", ""))
        url_calendar = str(event.get("url", ""))
        date_from = event.get("dtstart").dt
        date_till = event.get("dtend").dt if event.get("dtend") else None
        rrule = event.get("RRULE") if event.get("RRULE") else None
        if rrule:
            rules = parse_rule(rrule)
            if rules["UNTIL"] and rules["UNTIL"].date() < timezone.localdate():
                continue
            regular_event = create_this_day_regular_event(
                uid,
                title,
                description,
                url_calendar,
                date_from,
                date_till,
                cal,
                rules,
            )
            new_events.append(regular_event)
        if date_from.date() < timezone.localdate():
            continue
        new_event = update_or_create_event(
            uid,
            title,
            description,
            url_calendar,
            date_from,
            date_till,
            cal,
        )
        new_events.append(new_event)
    delete_events_not_in_calendar(current_events, new_events)


def create_this_day_regular_event(
    uid,
    title,
    description,
    url_calendar,
    date_from,
    date_till,
    cal,
    rules,
):
    today = timezone.localdate()
    week_number = (today.day - 1) // 7 + 1
    byday_map = {
        0: "MO",
        1: "TU",
        2: "WE",
        3: "TH",
        4: "FR",
        5: "SA",
        6: "SU",
    }
    new_date_from = date_from.replace(year=today.year, month=today.month, day=today.day)
    new_date_till = date_till.replace(year=today.year, month=today.month, day=today.day)
    if rules["FREQ"] == "WEEKLY":
        for day in rules["BYDAY"]:
            if byday_map[today.weekday()] == day:
                event, created = Event.objects.get_or_create(
                    uid=uid,
                    title=title,
                    description=description,
                    url_calendar=url_calendar,
                    date_from=new_date_from,
                    date_till=new_date_till,
                    calendar=cal,
                )
                set_users_for_event(event)
                return event
    elif rules["FREQ"] == "MONTHLY":
        event_week_number = int(rules["BYDAY"][0][:-2])
        event_week_day = rules["BYDAY"][0][-2:]
        if (
            week_number == event_week_number
            and byday_map[today.weekday()] == event_week_day
        ):
            event, created = Event.objects.get_or_create(
                uid=uid,
                title=title,
                description=description,
                url_calendar=url_calendar,
                date_from=new_date_from,
                date_till=new_date_till,
                calendar=cal,
            )
            set_users_for_event(event)
            return event


def parse_rule(rrule):
    return {
        "FREQ": rrule.get("FREQ", [None])[0],
        "BYDAY": rrule.get("BYDAY", []),
        "INTERVAL": int(rrule.get("INTERVAL", [1])[0]),
        "UNTIL": rrule.get("UNTIL", [None])[0],
    }
