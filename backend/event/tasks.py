from celery import shared_task
import requests
from django.utils import timezone
from event.utils import parse_ics
from event.models import Calendar, Event
from calendar_backend.settings import BOT_TOKEN


@shared_task
def run_base_update(calendar_id: int) -> None:
    """Таска по обновлению календаря."""

    cal = Calendar.objects.get(id=calendar_id)
    parse_ics(cal)


@shared_task
def start_update_calendar() -> None:
    """Таска по обновлению всех календарей."""

    for calendar_id in Calendar.objects.values_list("id", flat=True):
        run_base_update.delay(calendar_id)


@shared_task
def send_telegram_message(
    message: str,
    subject: str,
    event: Event,
) -> list[dict] | None:
    """
    Таска отправке сообщения в телеграм пользователей,
    связанных с мероприятием.
    """

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    responses = []
    for user in event.users.all():
        data = {
            "chat_id": user.telegram_id,
            "text": message,
            "parse_mode": "HTML",
        }
        response = requests.post(url, json=data)
        responses.append(response.json)
    return responses if responses else None


@shared_task
def clear_old_events() -> None:
    """Удаление старых мероприятий (вчерашних)."""

    for event in Event.objects.all():
        if event.date_from.date() < timezone.localdate():
            event.delete()
