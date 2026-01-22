import json
import logging
import requests
from celery import shared_task
from django_celery_beat.models import CrontabSchedule, PeriodicTask
from django.core.mail import EmailMessage
from django.db.models import Q
from django.utils import timezone
from calendar_backend import settings
from event.models import Event
from users.models import LoginCode, User


logger = logging.getLogger("email")


@shared_task(
    retry_kwargs={"max_retries": 5, "countdown": 5},
    retry_backoff=False,
    retry_jitter=True,
)
def send_code_email(code_id):
    """Отправка пользователю кода на почту."""

    request = LoginCode.objects.get(id=code_id)
    subject = "Ваш код подтверждения"
    message = f"Ваш код: {request.code}"
    email = EmailMessage(
        subject=subject,
        body=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[request.email],
    )
    email.send()
    logger.info(
        f"Отправка кода на почту {request.email}",
    )


@shared_task
def create_event_schedule(user_id: int) -> None:
    user = User.objects.get(id=user_id)
    update_time = user.calendar_show_time
    user_schedule, _ = CrontabSchedule.objects.get_or_create(
        minute=str(update_time.minute),
        hour=str(update_time.hour),
        day_of_week="*",
        day_of_month="*",
        month_of_year="*",
    )
    PeriodicTask.objects.update_or_create(
        name=f"send_events_schedule_for_user_{user.id}",
        defaults={
            "crontab": user_schedule,
            "task": "users.tasks.send_events_for_active_users",
            "args": json.dumps([user.id]),
            "kwargs": "{}",
            "enabled": True,
        },
    )


@shared_task(
    retry_kwargs={"max_retries": 5, "countdown": 5},
    retry_backoff=False,
    retry_jitter=True,
)
def send_events_for_active_users(user_id: int) -> None:
    user = User.objects.select_related("calendar").get(id=user_id)
    url = f"https://api.telegram.org/bot{settings.BOT_TOKEN}/sendMessage"
    base_q = Q(
        date_from__date=timezone.localdate(),
        date_till__gt=timezone.now(),
        calendar=user.calendar,
        users=user,
    )
    events = (
        Event.objects.filter(
            base_q,
        )
        .prefetch_related(
            "users",
        )
        .select_related(
            "calendar",
        )
        .order_by(
            "date_from",
        )
    )

    if events.exists():
        letters = "<b>📅 Ваши созвоны на сегодня:</b>\n\n"
        for i, event in enumerate(events, 1):
            event_url = event.url_for_event()
            event_time = event.time_for_event()
            letters += f"<b>{i}. {event.title.strip()}</b>\n"
            letters += f"   🕐 {event_time}\n"
            if event_url:
                event_url = event_url.strip().rstrip('\\"')
                letters += f"   🔗 <a href='{event_url}'>Ссылка</a>\n\n"
            else:
                letters += "   🔗 Ссылка не предоставлена.\n\n"
    else:
        letters = "Нет мероприятий в календаре на сегодня."
    data = {
        "chat_id": user.telegram_id,
        "text": letters,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }
    requests.post(url, json=data)
