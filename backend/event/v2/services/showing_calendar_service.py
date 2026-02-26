from dataclasses import dataclass
from django.db.models import Q, QuerySet
from django.utils import timezone
from core.constants import CHAT_ID, CALENDAR_KEY
from event.models import Calendar, Event, GroupChat
from event.v2.dto import RequestForCalendar, PreparedData
from event.serializers import EventShowSerializer
from users.models import User


@dataclass(slots=True, frozen=True, kw_only=True)
class ShowCalendarService:
    """
    Сервис по отображению календаря
    по запросу пользователя.
    """

    def __call__(self, request: RequestForCalendar) -> PreparedData:
        if not request.chat_id or not request.telegram_id:
            return self._show_calendar_in_alert(
                request=request,
            )
        if request.chat_id == CHAT_ID:
            return PreparedData(
                data=self._hardcode_request(),
                message=None,
                telegram_id=request.chat_id,
            )
        if request.chat_id != request.telegram_id:
            prepared_data = self._request_for_regular_calendar_to_group(
                request=request,
            )
        else:
            prepared_data = self._request_for_regular_calendar_to_user(
                request=request,
            )
        if prepared_data.message:
            from event.tasks import send_telegram_message

            send_telegram_message(
                prepared_data=prepared_data,
            )
        return prepared_data

    def _show_calendar_in_alert(
        self,
        request: RequestForCalendar,
    ) -> PreparedData:
        """
        Отработка запроса из таски по отправке календаря
        по установленному времени
        """
        if request.telegram_id:
            prepared_data = self._request_for_regular_calendar_to_user(
                request=request,
            )
        elif request.chat_id and request.chat_id == CHAT_ID:
            prepared_data = PreparedData(
                data=self._hardcode_request(),
                message=None,
                telegram_id=request.chat_id,
            )
        else:
            prepared_data = self._request_for_regular_calendar_to_group(
                request=request,
            )
        return prepared_data

    def _hardcode_request(self) -> list:
        """
        ХАРДКОД.
        Обработка запроса в группе техчасти.
        """

        events_qs = Event.objects.filter(
            Q(
                date_from__date=timezone.localdate(),
                date_till__gt=timezone.now(),
                calendar__key=CALENDAR_KEY,
            ),
        ).order_by(
            "date_from",
        )
        data = self._hardcode_events_for_group(events_qs)
        return data

    def _hardcode_events_for_group(
        self,
        events_qs: QuerySet[Event],
        no_events: bool = True,
    ) -> list:
        """
        ХАРДКОД.
        Подготовка данных для запроса в группе техчасти.
        """

        results = []
        star_events = events_qs.filter(star=True)
        slash_events = events_qs.filter(Q(slash=True) | Q(all_event=True))
        aiterus_events = events_qs.filter(aiterus=True)
        results.append(
            self._hardcode_get_result_for_user("Павел", slash_events),
        )
        results.append(
            self._hardcode_get_result_for_user("Анна/Олеся", star_events),
        )
        results.append(
            self._hardcode_get_result_for_user("Аитерус", aiterus_events),
        )
        for result in results:
            if result["events"] is not None:
                no_events = False
        return results if not no_events else []

    def _hardcode_get_result_for_user(
        self,
        username: str,
        type_events: QuerySet[Event],
    ) -> dict:
        """
        ХАРДКОД.
        Подготовка данных по пользователям
        для оторажения в группе техчасти.
        """

        return {
            "username": username,
            "events": (
                EventShowSerializer(
                    type_events,
                    many=True,
                ).data
                if type_events.exists()
                else None
            ),
        }

    def _request_for_regular_calendar_to_user(
        self,
        request: RequestForCalendar,
        message: str = "",
    ) -> PreparedData:
        """
        Обработка запроса от пользователей.
        Проводятся следующие проверки:
        - существование пользователя;
        - пользователь активен;
        - есть ли у пользователя календарь.
        В случае если пользователь не прошел какую-нибудь
        проверку, ему будет отправлено сообщение с пояснениями
        по ошибке запроса.
        Если все проверки пройдены, пользователю отправляются
        актуальные события на текущий день.
        """

        data: list = []
        user, message = self._try_find_user(request=request)
        if not user:
            message = self._prepare_message_to_user(
                not_registered=True,
            )
        elif not user.is_active:
            message = self._prepare_message_to_user(
                not_active=True,
            )
        else:
            calendar, message = self._check_user_has_calendar(
                user=user,
            )
        if message or not calendar:
            return PreparedData(
                data=data,
                message=message,
                telegram_id=request.telegram_id,
            )
        queryset = (
            Event.objects.filter(
                date_from__date=timezone.localdate(),
                date_till__gt=timezone.now(),
                calendar=calendar,
                users=user,
            )
            .prefetch_related(
                "users",
                "calendar",
            )
            .order_by(
                "date_from",
            )
        )
        data = EventShowSerializer(
            queryset,
            many=True,
        ).data
        return PreparedData(
            data=data,
            message=message,
            telegram_id=request.telegram_id,
        )

    def _try_find_user(
        self,
        request: RequestForCalendar,
        message: str = "",
    ) -> tuple[User | None, str]:
        """
        Проверка регистрации прользователя.
        """

        try:
            user = User.objects.get(telegram_id=request.telegram_id)
        except User.DoesNotExist:
            return None, self._prepare_message_to_user(not_registered=True)
        return user, message

    def _check_user_has_calendar(
        self,
        user: User,
        message: str = "",
    ) -> tuple[Calendar | None, str]:
        """
        Проверка наличия календаря у пользователя.
        """

        if not user.calendar:
            return None, self._prepare_message_to_user(no_calendar=True)
        try:
            calendar = Calendar.objects.get(id=user.calendar.id)
        except Calendar.DoesNotExist:
            return None, self._prepare_message_to_user(no_calendar=True)
        return calendar, message

    def _prepare_message_to_user(
        self,
        not_registered: bool = False,
        not_active: bool = False,
        no_calendar: bool = False,
        message: str = "Уважаемый пользователь, для получения "
        "данных календаря, вам необходимо ",
    ) -> str:
        """
        Подготовка сообщения в адрес пользователя в случае, если он
        не прошел проверку.
        """

        if not_registered:
            message += "зарегистрироваться."
            return message
        elif not_active:
            message += (
                "продолжить регистрацию."
                " Для этого просим подтвердить адрес вашей электронной почты."
            )
            return message
        elif no_calendar:
            message += (
                "направить iCal "
                "вашего Яндекс.Календаря в адрес администратора "
                "@AnnnnnaAnna"
            )
        return message

    def _request_for_regular_calendar_to_group(
        self,
        request: RequestForCalendar,
        message: str = "",
    ) -> PreparedData:
        """
        Обработка запроса от групповых чатов.
        Срабатывает в случае если chat_id != telegram_id
        Проводятся следующие проверки:
        - существование группового чата;
        - есть ли у группового чата календарь.
        В случае если групповой чат не прошел какую-нибудь
        проверку, ему будет отправлено сообщение с пояснениями
        по ошибке запроса.
        Если все проверки пройдены, групповому чату отправляются
        актуальные события на текущий день.
        """

        data: list = []
        group, message = self._try_find_group_chat(request=request)
        if not group:
            message = self._prepare_message_to_group(
                not_registered=True,
            )
        else:
            calendar, message = self._check_group_chat_has_calendar(
                group=group,
            )
        if message or not calendar:
            return PreparedData(
                data=data,
                message=message,
                telegram_id=request.chat_id,
            )
        queryset = (
            Event.objects.filter(
                date_from__date=timezone.localdate(),
                date_till__gt=timezone.now(),
                calendar=calendar,
                groups=group,
            )
            .prefetch_related(
                "groups",
                "calendar",
            )
            .order_by(
                "date_from",
            )
        )
        data = EventShowSerializer(
            queryset,
            many=True,
        ).data
        return PreparedData(
            data=data,
            message=message,
            telegram_id=request.telegram_id,
        )

    def _try_find_group_chat(
        self,
        request: RequestForCalendar,
        message: str = "",
    ) -> tuple[GroupChat | None, str]:
        """
        Проверка регистрации группового чата.
        """

        try:
            group = GroupChat.objects.get(chat_id=request.chat_id)
        except GroupChat.DoesNotExist:
            return None, self._prepare_message_to_group(not_registered=True)
        return group, message

    def _check_group_chat_has_calendar(
        self,
        group: GroupChat,
        message: str = "",
    ) -> tuple[Calendar | None, str]:
        """
        Проверка наличия календаря у пользователя.
        """

        if not group.calendar:
            return None, self._prepare_message_to_user(no_calendar=True)
        try:
            calendar = Calendar.objects.get(id=group.calendar.id)
        except Calendar.DoesNotExist:
            return None, self._prepare_message_to_user(no_calendar=True)
        return calendar, message

    def _prepare_message_to_group(
        self,
        not_registered: bool = False,
        no_calendar: bool = False,
        message: str = "Уважаемый пользователь, для получения "
        "данных календаря в данном групповом чате, вам необходимо ",
    ) -> str:
        """
        Подготовка сообщения в адрес группового чата в случае, если он
        не прошел проверку.
        """

        if not_registered:
            message += "направить id группового чата "
        elif no_calendar:
            message += "направить iCal вашего группового Яндекс.Календаря "
        message += "в адрес администратора " "@AnnnnnaAnna"
        return message
