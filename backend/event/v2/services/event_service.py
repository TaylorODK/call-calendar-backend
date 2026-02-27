from dataclasses import dataclass, fields
from datetime import date, datetime
from django.db.models import QuerySet
from django.utils import timezone
from event.models import Calendar, Event, GroupChat
from event.v2.dto import (
    MessageToPrepare,
    ParsedEvent,
    ParsedRule,
    ServicedEvent,
    RegularEventDates,
)
from event.v2.services.create_message_service import CreateMessageService
from event.v2.services.sending_message_service import SendingMessageService
from core.constants import (
    BYDAY_MAP,
    CALENDAR_KEY,
)
from core.enums import StatusEnums
from users.models import User


@dataclass(slots=True, frozen=True, kw_only=True)
class EventService:
    """
    Сервис по созданию/изменению мероприятия
    по итогам парсинга календаря.
    Входные данные:
    1) Событие - event: ParsedEvent;
    2) Календарь calendar: Calendar.
    События делятся на 2 типа:
    - разовые события;
    - регулярные события.
    Регулярные делятся на 4 типа:
    - ежедневные;
    - еженедельные;
    - ежемесячные;
    - ежегодные; (TODO: предусмотреть парсинг ежегодных событий)
    Регулярные события отличаются наличие полей:
    - rrule;
    - exdate.
    Если в exdate есть текущая дата, то событие добавляться в БД
    не будет.
    """

    def __call__(
        self,
        event: ParsedEvent,
        calendar: Calendar,
    ) -> ServicedEvent | None:
        if event.exdate and timezone.localdate() in event.exdate:
            return None
        dates = None
        parsed_rules = self._calculate_parsed_rule(event=event)
        if parsed_rules:
            dates = self._calculate_dates_for_regular_event(event=event)
        if not self._check_if_event_today(
            event=event,
            rule=parsed_rules if parsed_rules else None,
            dates=dates if dates else None,
        ):
            return None
        create_message = CreateMessageService()
        serviced_event = self._create_event(
            event=event,
            calendar=calendar,
            dates=dates if dates else None,
            create_message=create_message,
        )
        if serviced_event:
            self._add_users_to_event(serviced_event=serviced_event)
            self._add_groups_to_event(serviced_event=serviced_event)
            self._remove_users_if_not_in_calendar(
                serviced_event=serviced_event,
            )
            self._remove_groups_if_not_in_calendar(
                serviced_event=serviced_event,
            )
            if serviced_event.message:
                if serviced_event.status == StatusEnums.UPDATED:
                    print(serviced_event.event.title)
                    print(serviced_event.event.users.all())
                    print(serviced_event.event.groups.all())
                    serviced_event.users = serviced_event.event.users.all()
                    serviced_event.groups = serviced_event.event.groups.all()
                message_service = SendingMessageService()
                message_to_prepare = MessageToPrepare(
                    message=serviced_event.message,
                    event_id=serviced_event.event.id,
                    status=serviced_event.status,
                    users=serviced_event.users,
                    groups=serviced_event.groups,
                    old_fields=serviced_event.olf_fields,
                )
                message_service(message_to_prepare=message_to_prepare)
            self._add_calendar_to_event(
                serviced_event=serviced_event,
                calendar=calendar,
            )
            if calendar.key == CALENDAR_KEY:
                self._hardcode_calendar(serviced_event=serviced_event)
            return serviced_event
        return None

    def _create_event(
        self,
        event: ParsedEvent,
        calendar: Calendar,
        dates: RegularEventDates | None,
        create_message: CreateMessageService,
    ) -> ServicedEvent | None:
        """
        Создание события.
        Если событие не создается, то оно
        проверяется на наличие измененных полей.
        К созданному разовому событию создается текст
        сообщения.
        ВНИМАНИЕ!
        if not created and not dates - очень важные условия
        для обновления мероприятий, иначе регулярное событие будет
        обновлять себя в каждый парсинг по кругу.
        """

        users = User.objects.filter(calendar=calendar)
        groups = GroupChat.objects.filter(calendar=calendar)
        new_event, created = Event.objects.get_or_create(
            uid=event.uid,
            defaults={
                "title": event.title,
                "description": event.description,
                "url_calendar": event.url_calendar,
                "date_from": (dates.new_date_from) if dates else event.date_from,
                "date_till": (dates.new_date_till) if dates else event.date_till,
            },
        )
        message, status = create_message(
            event=new_event,
            created=created,
            dates=dates,
            changed_fields=None,
        )
        if not created and not dates:
            serviced_event = self._update_event(
                event_to_update=new_event,
                event=event,
                users=users,
                groups=groups,
                create_message=create_message,
            )
            return serviced_event
        return ServicedEvent(
            event=new_event,
            message=message,
            users=users,
            status=status,
            groups=groups,
        )

    def _update_event(
        self,
        event_to_update: Event,
        event: ParsedEvent,
        users: QuerySet[User],
        groups: QuerySet[GroupChat],
        create_message: CreateMessageService,
    ) -> ServicedEvent | None:
        """
        Изменение событие.
        Проверяется список полей на наличие
        изменений и создается словарь, где
        - ключ - наименование поля;
        - значение - значение поля.
        Ключи нужны для списка полей на сохранение
        в БД.
        Также словарь используется для формирования текста
        сообщения об изменении мероприятия.
        ВНИМАНИЕ: измененное в текущие день регулярное событие
        считается одноразовым событием в ICS данных. uid события
        совпадает с UID регулярного созвона и будет именно изменяться,
        а не создаваться и дублироваться два раза в календаре на текущий
        день.
        """
        old_fields = {}
        changed_fields = {}
        for field in fields(event):
            if field.name == "rrule" or field.name == "exdate":
                continue
            new_value = getattr(event, field.name)
            if not hasattr(event, field.name):
                continue
            old_value = getattr(event_to_update, field.name)
            if old_value != new_value:
                old_fields[field.name] = old_value
                changed_fields[field.name] = new_value
                setattr(event_to_update, field.name, new_value)
        if changed_fields:
            fields_list = [field for field in changed_fields.keys()]
            event_to_update.save(update_fields=fields_list)
        message, status = create_message(
            event=event_to_update,
            changed_fields=changed_fields,
            old_fields=old_fields,
        )
        return ServicedEvent(
            message=message,
            event=event_to_update,
            users=users,
            groups=groups,
            status=status,
            olf_fields=old_fields,
        )

    def _hardcode_calendar(self, serviced_event: ServicedEvent) -> None:
        """
        ХАРДКОД для группового календаря.
        """
        serviced_event.event.check_for_star_slash()
        serviced_event.event.save(
            update_fields=["star", "slash", "aiterus", "all_event"],
        )

    def _add_calendar_to_event(
        self,
        calendar: Calendar,
        serviced_event: ServicedEvent,
    ) -> None:
        """
        Добавление календаря в событие.
        Пояснение:
        Личные календари команды техчасти Y-lab берут часть мероприятий
        из общего календаря, в связи с чем их UID совпадает. Так как поле
        UID уникальное в модели Event, то событие на все календари создается
        в 1 экземпляре. К этому событию присоедияются календари и пользователи,
        связанные с ними.
        """

        if calendar not in serviced_event.event.calendar.all():
            serviced_event.event.calendar.add(calendar)

    def _add_users_to_event(
        self,
        serviced_event: ServicedEvent,
    ) -> None:
        """
        Добавление пользователей в событие.
        """
        serviced_event.event.users.add(*serviced_event.users)

    def _add_groups_to_event(
        self,
        serviced_event: ServicedEvent,
    ) -> None:
        """
        Добавление групп в событие.
        """
        serviced_event.event.groups.add(*serviced_event.groups)

    def _remove_users_if_not_in_calendar(
        self,
        serviced_event: ServicedEvent,
    ) -> None:
        """
        Удаление пользователей из события.
        Пояснение:
        Создано на случай, если пользователю был случайно выбран не
        тот календарь. Иначе добавленным в календарь пользователям
        будут приходить уведомления об создании/изменение/удаленни
        мероприятия в которые они были добавлен в парсинге,
        а также напоминалки о ближайшем созвоне.
        """

        for user in serviced_event.event.users.all():
            if user.calendar not in serviced_event.event.calendar.all():
                serviced_event.event.users.remove(user)

    def _remove_groups_if_not_in_calendar(
        self,
        serviced_event: ServicedEvent,
    ) -> None:
        """
        Удаление лишних групп из события.
        """

        for group in serviced_event.event.groups.all():
            if group.calendar not in serviced_event.event.calendar.all():
                serviced_event.event.groups.remove(group)

    def _calculate_parsed_rule(
        self,
        event: ParsedEvent,
    ) -> ParsedRule | None:
        """
        Подготовка правил регулярных мероприятий:
        - FREQ - ежедневно/еженедельно/ежемесячно/ежегодно
        - BYDAY - по каким дня недели
        - INTERVAL - периодичность проведения
        - UNTIL - до какой даты.
        """

        if not event.rrule:
            return None
        return ParsedRule(
            FREQ=event.rrule.get("FREQ", [None])[0],
            BYDAY=event.rrule.get("BYDAY", []),
            INTERVAL=int(event.rrule.get("INTERVAL", [1])[0]),
            UNTIL=event.rrule.get("UNTIL", [None])[0],
        )

    def _check_if_event_today(
        self,
        event: ParsedEvent,
        rule: ParsedRule | None,
        dates: RegularEventDates | None,
    ) -> bool:
        """
        Проверка на то, что регулярное событие происходит
        именно в текущий день.
        Пояснение:
        Регулярное событие создается 1 раз и поле date_from
        в нем по умолчанию будет совпадать с датой и временем
        первого раза его работы.
        """

        if not rule or not dates:
            if event.date_from.date() >= timezone.localdate():
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

    def _calculate_dates_for_regular_event(
        self,
        event: ParsedEvent,
    ) -> RegularEventDates:
        """
        Расчет дат для регулярных событий,
        нужен для вычеслений в _check_if_event_today
        и изменения даты проведения события.
        """
        today = timezone.localdate()
        return RegularEventDates(
            today=today,
            week_number=(today.day - 1) // 7 + 1,
            new_date_from=self._calculate_new_date(event.date_from, today),
            new_date_till=self._calculate_new_date(
                event.date_till,
                today,
            )
            if event.date_till
            else None,
            weeks_from_event_start=(today - event.date_from.date()).days // 7,
            days_from_start_event=(today - event.date_from.date()).days,
        )

    def _calculate_new_date(
        self,
        date: datetime,
        today: date,
    ) -> datetime:
        """
        Замена даты регулярного события
        на текущие день/месяц/год.
        """

        return date.replace(
            year=today.year,
            month=today.month,
            day=today.day,
        )
