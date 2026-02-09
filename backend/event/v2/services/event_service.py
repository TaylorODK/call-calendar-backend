from dataclasses import dataclass, fields
from datetime import date, datetime
from django.db.models import QuerySet
from django.utils import timezone
from event.models import Calendar, Event
from event.v2.dto import (
    ParsedEvent,
    ParsedRule,
    ServicedEvent,
    RegularEventDates,
)
from core.constants import BYDAY_MAP, CALENDAR_KEY
from users.models import User


@dataclass
class EventService:
    event: ParsedEvent
    calendar: Calendar

    def __call__(self, *args, **kwds) -> ServicedEvent | None:
        dates = None
        parsed_rules = self.calculate_parsed_rule()
        if parsed_rules:
            dates = self.calculate_dates_for_regular_event()
        if not self.check_if_event_today(
            rule=parsed_rules if parsed_rules else None,
            dates=dates if dates else None,
        ):
            return None
        serviced_event = self.create_event(dates=dates if dates else None)
        if serviced_event:
            if serviced_event.message:
                from event.tasks import send_telegram_message

                send_telegram_message(serviced_event=serviced_event)
            self.add_calendar_to_event(serviced_event=serviced_event)
            self.add_users_to_event(serviced_event=serviced_event)
            self.remove_users_if_not_in_calendar(
                serviced_event=serviced_event,
            )
            if self.calendar.key == CALENDAR_KEY:
                self.hardcode_calendar(serviced_event=serviced_event)
            return serviced_event
        return None

    def create_event(
        self,
        dates: RegularEventDates | None,
    ) -> ServicedEvent | None:
        users = User.objects.filter(calendar=self.calendar)
        new_event, created = Event.objects.get_or_create(
            uid=self.event.uid,
            defaults={
                "title": self.event.title,
                "description": self.event.description,
                "url_calendar": self.event.url_calendar,
                "date_from": (dates.new_date_from) if dates else self.event.date_from,
                "date_till": (dates.new_date_till) if dates else self.event.date_till,
            },
        )
        message = self.generate_message(
            event=new_event,
            created=created,
            changed_fields=None,
        )
        if not created and not dates:
            serviced_event = self.update_event(
                event_to_update=new_event,
                users=users,
            )
            return serviced_event
        return ServicedEvent(
            event=new_event,
            message=message,
            users=users,
        )

    def update_event(
        self,
        event_to_update: Event,
        users: QuerySet[User],
    ) -> ServicedEvent | None:
        changed_fields = {}
        for field in fields(self.event):
            if field.name == "rrule":
                continue
            new_value = getattr(self.event, field.name)
            if not hasattr(self.event, field.name):
                continue
            old_value = getattr(event_to_update, field.name)
            if old_value != new_value:
                changed_fields[field.name] = (
                    f"- изменение поля {field.name} на {new_value}.\n"
                )
                setattr(event_to_update, field.name, new_value)
        if changed_fields:
            fields_list = [field for field in changed_fields.keys()]
            event_to_update.save(update_fields=fields_list)
        message = self.generate_message(
            event=event_to_update,
            created=False,
            changed_fields=changed_fields,
        )
        return ServicedEvent(
            message=message,
            event=event_to_update,
            users=users,
        )

    def generate_message(
        self,
        event: Event,
        created: bool,
        changed_fields: dict | None,
    ) -> str:
        message = ""
        if created and event.date_from.date() == timezone.localdate():
            message = "📅 Новое мероприятие в календаре:"
            message += f"<b>{event.title.strip()}</b>\n"
            message += f"   🕐 {event.time_for_event()}\n"
            if event.url_for_event():
                event_url = event.url_for_event().strip().rstrip('\\"')
                message += f"   🔗 <a href='{event_url}'>Ссылка</a>\n\n"
            else:
                message += "   🔗 Ссылка не предоставлена.\n\n"
        elif changed_fields and event.date_from.date() == timezone.localdate():
            message = f"📅 Изменения в мероприятии '{event.title}':\n"
            message += "".join(changed_fields.values())
        return message

    def hardcode_calendar(self, serviced_event: ServicedEvent) -> None:
        """
        ХАРДКОД для группового календаря.
        """
        serviced_event.event.check_for_star_slash()
        serviced_event.event.save(
            update_fields=["star", "slash", "aiterus", "all_event"],
        )

    def add_calendar_to_event(
        self,
        serviced_event: ServicedEvent,
    ) -> None:
        if self.calendar not in serviced_event.event.calendar.all():
            serviced_event.event.calendar.add(self.calendar)

    def add_users_to_event(
        self,
        serviced_event: ServicedEvent,
    ) -> None:
        for user in serviced_event.users:
            if user not in serviced_event.event.users.all():
                serviced_event.event.users.add(*serviced_event.users)

    def remove_users_if_not_in_calendar(
        self,
        serviced_event: ServicedEvent,
    ) -> None:
        for user in serviced_event.event.users.all():
            if user.calendar not in serviced_event.event.calendar.all():
                serviced_event.event.users.remove(user)

    def calculate_parsed_rule(
        self,
    ) -> ParsedRule | None:
        if not self.event.rrule:
            return None
        return ParsedRule(
            FREQ=self.event.rrule.get("FREQ", [None])[0],
            BYDAY=self.event.rrule.get("BYDAY", []),
            INTERVAL=int(self.event.rrule.get("INTERVAL", [1])[0]),
            UNTIL=self.event.rrule.get("UNTIL", [None])[0],
        )

    def check_if_event_today(
        self,
        rule: ParsedRule | None,
        dates: RegularEventDates | None,
    ) -> bool:
        if not rule or not dates:
            if self.event.date_from.date() >= timezone.localdate():
                return True
            return False
        if rule.UNTIL and rule.UNTIL.date() < timezone.localdate():
            return False
        if rule.FREQ == "DAILY":
            if rule.BYDAY:
                for day in rule.BYDAY:
                    if BYDAY_MAP[dates.today.weekday()] == day:
                        return True
                return False
            elif dates.days_from_start_event % int(rule.INTERVAL) == 0:
                return True
            return False
        elif rule.FREQ == "WEEKLY":
            for day in rule.BYDAY:
                if BYDAY_MAP[dates.today.weekday()] == day and (
                    dates.weeks_from_event_start % int(rule.INTERVAL) == 0
                ):
                    return True
            return False
        elif rule.FREQ == "MONTHLY":
            event_week_number = int(rule.BYDAY[0][:-2])
            event_week_day = rule.BYDAY[0][-2:]
            if (
                dates.week_number == event_week_number
                and BYDAY_MAP[dates.today.weekday()] == event_week_day
            ):
                return True
            return False
        return False

    def calculate_dates_for_regular_event(
        self,
    ) -> RegularEventDates:
        today = timezone.localdate()
        return RegularEventDates(
            today=today,
            week_number=(today.day - 1) // 7 + 1,
            new_date_from=self.calculate_new_date(self.event.date_from, today),
            new_date_till=self.calculate_new_date(
                self.event.date_till,
                today,
            )
            if self.event.date_till
            else None,
            weeks_from_event_start=(today - self.event.date_from.date()).days // 7,
            days_from_start_event=(today - self.event.date_from.date()).days,
        )

    def calculate_new_date(
        self,
        date: datetime,
        today: date,
    ) -> datetime:
        return date.replace(
            year=today.year,
            month=today.month,
            day=today.day,
        )
