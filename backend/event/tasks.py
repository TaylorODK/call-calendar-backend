import logging
import json
from datetime import timedelta
from celery import shared_task
import requests
from django_celery_beat.models import ClockedSchedule, PeriodicTask
from django.utils import timezone
from event.models import Calendar, Event
from event.v2.dto import ServicedEvent, PreparedData
from event.v2.services.calendar_service import CalendarService
from calendar_backend.settings import BOT_TOKEN
from core.constants import ALERT_TIME_BEFORE_EVENT


bot_logger = logging.getLogger("bot")
calendar_logger = logging.getLogger("calendar")


@shared_task
def run_base_update(calendar_id: int) -> None:
    """Таска по обновлению календаря."""

    cal = Calendar.objects.get(id=calendar_id)
    calendar_logger.info(f"Обновление календаря '{cal.title}'")
    parsing = CalendarService()
    parsing(cal=cal)


@shared_task
def start_update_calendar() -> None:
    """Таска по обновлению всех календарей."""
    calendar_logger.info("Начало задачи по обновлению календарей")
    for calendar_id in Calendar.objects.values_list("id", flat=True):
        run_base_update.delay(calendar_id)


@shared_task
def send_telegram_message(
    serviced_event: ServicedEvent | None = None,
    prepared_data: PreparedData | None = None,
) -> list[dict] | None:
    """
    Таска по отправке сообщения в телеграм пользователей:
    Возможны 2 сценария для отправки сообщений:
    1) по результатам парсинга календаря serviced_event
    (создание, изменеие, удаление мероприятия);
    2) по результатам обработки запроса пользователя
    на предоставление данных календаря prepared_data
    """

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    responses = []
    if serviced_event:
        for user in serviced_event.users.all():
            data = {
                "chat_id": user.telegram_id,
                "text": serviced_event.message,
                "parse_mode": "HTML",
                "disable_web_page_preview": True,
            }
            response = requests.post(url, json=data)
            responses.append(response.json)
            bot_logger.info(f"Сообщение в адрес пользователя {user.email}")
    elif prepared_data:
        data = {
            "chat_id": prepared_data.telegram_id,
            "text": prepared_data.message,
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
        }
        response = requests.post(url, json=data)
        responses.append(response.json)
    return responses if responses else None


@shared_task
def clear_old_events() -> None:
    """Удаление старых мероприятий (вчерашних)."""
    calendar_logger.info("Начало задачи по удалению старых мероприятий")
    for event in Event.objects.all():
        if event.date_from.date() < timezone.localdate():
            event.delete()


@shared_task
def create_task_for_alert(event_id: int) -> None:
    event = Event.objects.get(id=event_id)
    if event:
        alert_time = event.date_from - timedelta(
            minutes=ALERT_TIME_BEFORE_EVENT,
        )
        if alert_time <= timezone.now():
            send_alert(event_id)
            return
        clocked, _ = ClockedSchedule.objects.get_or_create(
            clocked_time=alert_time,
        )
        PeriodicTask.objects.update_or_create(
            name=f"alert_for_event_{event_id}",
            defaults={
                "task": "event.tasks.send_alert",
                "clocked": clocked,
                "one_off": True,
                "args": json.dumps([event_id]),
                "enabled": True,
            },
        )


@shared_task(
    retry_kwargs={"max_retries": 5, "countdown": 5},
    retry_backoff=False,
    retry_jitter=True,
)
def send_alert(event_id: int) -> None:
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    event = Event.objects.get(id=event_id)
    if event and event.date_from > timezone.now():
        users = event.users.all()
        letter = f"<b>🕐 Через {ALERT_TIME_BEFORE_EVENT}"
        letter += f" минут начнется созвон {event.title}</b>\n\n"
        event_url = event.url_for_event()
        if event_url:
            event_url = event_url.strip().rstrip('\\"')
            letter += f"   🔗 <a href='{event_url}'>Ссылка</a>\n\n"
        else:
            letter += "   🔗 Ссылка не предоставлена.\n\n"
        for user in users:
            data = {
                "chat_id": user.telegram_id,
                "text": letter,
                "parse_mode": "HTML",
                "disable_web_page_preview": True,
            }
            requests.post(url, json=data)


@shared_task
def delete_task_for_alert(event_id):
    task = PeriodicTask.objects.filter(
        name=f"alert_for_event_{event_id}",
    ).first()
    if task:
        task.delete()
