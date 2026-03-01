from dataclasses import dataclass
from django.utils import timezone
from core.constants import CHAT_ID
from core.exceptions import NoReceiver
from core.enums import TypeReceiverEnums
from users.v2.dto import AlerReceiver, CalendarAlert, PreparedAlertData
from users.models import User
from event.v2.dto import RequestForCalendar
from event.models import GroupChat
from event.v2.services import ShowCalendarService


@dataclass(frozen=True, kw_only=True, slots=True)
class SendEventsService:
    def __call__(self, alert_receiver: AlerReceiver):
        alert = self._get_prepared_data(alert_receiver=alert_receiver)
        from event.tasks import send_telegram_message

        if alert.prepared_data.message:
            send_telegram_message(prepared_data=alert.prepared_data)
            return
        calendar_alert = self._generate_regular_message(
            alert=alert,
        )
        if (
            calendar_alert.message == "📭 На сегодня созвонов нет"
        ) and self._check_today_is_weekend():
            return
        send_telegram_message(calendar_alert=calendar_alert)

    def _get_prepared_data(
        self,
        alert_receiver: AlerReceiver,
    ) -> PreparedAlertData:
        show_calendar = ShowCalendarService()
        if alert_receiver.user_id:
            try:
                reciever = User.objects.filter(
                    id=alert_receiver.user_id,
                ).first()
            except User.DoesNotExist:
                raise NoReceiver
            prepared_data = show_calendar(
                RequestForCalendar(
                    telegram_id=str(reciever.telegram_id),
                    chat_id=None,
                ),
            )
            type_receiver = TypeReceiverEnums.USER
        elif alert_receiver.group_id:
            try:
                reciever = GroupChat.objects.filter(id=alert_receiver.group_id).first()
            except GroupChat.DoesNotExist:
                raise NoReceiver
            prepared_data = show_calendar(
                RequestForCalendar(
                    telegram_id=None,
                    chat_id=str(reciever.chat_id),
                ),
            )
            type_receiver = TypeReceiverEnums.GROUP_CHAT
        return PreparedAlertData(
            prepared_data=prepared_data,
            type_receiver=type_receiver,
            receiver=reciever,
        )

    def _generate_regular_message(
        self,
        alert: PreparedAlertData,
        message: str = "",
    ) -> CalendarAlert:
        if not alert.prepared_data.data:
            message = "📭 На сегодня созвонов нет"
        elif (
            alert.type_receiver == TypeReceiverEnums.GROUP_CHAT
            and alert.receiver.chat_id == CHAT_ID
        ):
            message = self._generate_hardcode_message(
                alert=alert,
            )
        else:
            if alert.prepared_data.data:
                message = "📅 <b>Ваши созвоны на сегодня:</b>\n\n"
                for i, meeting in enumerate(alert.prepared_data.data, 1):
                    title = meeting["title"]
                    url = meeting["url"]
                    message += f"<b>{i}. {title}</b>\n"
                    message += f"   🕐 {meeting['meeting_time']}\n"
                    if url:
                        url = meeting["url"].strip().rstrip('\\"')
                        message += f"   🔗 <a href='{url}'>Ссылка</a>\n\n"
                    else:
                        message += "   🔗 Ссылка не предоставлена.\n\n"
        if alert.type_receiver == TypeReceiverEnums.GROUP_CHAT:
            telegram_id = alert.receiver.chat_id
        else:
            telegram_id = alert.receiver.telegram_id
        return CalendarAlert(
            message=message,
            telegram_id=telegram_id,
        )

    def _generate_hardcode_message(
        self,
        alert: PreparedAlertData,
        message: str = "",
    ) -> str:
        message = "📅 <b>Cозвоны на сегодня:</b>\n\n"
        users_with_events = []
        for user_data in alert.prepared_data.data:
            if user_data.get("events"):
                users_with_events.append(user_data)

        for n, user_data in enumerate(users_with_events, 1):
            username = user_data["username"]
            events = user_data.get("events", [])
            if not events:
                continue
            message += f"         🎧   <b>{username}</b>\n\n"

            for i, event in enumerate(events, 1):
                title = event["title"]
                url = event["url"]
                message += f"<b>{i}. {title}</b>\n"
                message += f"   🕐 {event['meeting_time']}\n"

                if url:
                    url = event["url"].strip().rstrip('\\"')
                    message += f"   🔗 <a href='{url}'>Ссылка</a>\n"
                else:
                    message += "   🔗 Ссылка не предоставлена.\n"

            if n != len(users_with_events):
                message += "─" * 19 + "\n\n"
        return message

    def _check_today_is_weekend(self) -> bool:
        return timezone.localdate().weekday() >= 5
