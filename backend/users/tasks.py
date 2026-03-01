import json
import logging
from celery import shared_task
from django_celery_beat.models import CrontabSchedule, ClockedSchedule, PeriodicTask
from django.core.mail import EmailMessage
from django.utils import timezone
from calendar_backend import settings
from event.models import GroupChat
from users.models import LoginCode, User
from users.v2.dto import AlerReceiver
from users.v2.services import SendEventsService


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
def create_event_schedule(
    user_id: int | None = None,
    group_id: int | None = None,
) -> None:
    if user_id:
        receiver = User.objects.get(id=user_id)
        receiver_name = "user"
    elif group_id:
        receiver = GroupChat.objects.get(id=group_id)
        receiver_name = "group"
    update_time = receiver.calendar_show_time
    recieve_schedule, _ = CrontabSchedule.objects.get_or_create(
        minute=str(update_time.minute),
        hour=str(update_time.hour),
        day_of_week="*",
        day_of_month="*",
        month_of_year="*",
    )
    PeriodicTask.objects.update_or_create(
        name=f"send_events_schedule_for_{receiver_name}_{receiver.id}",
        defaults={
            "crontab": recieve_schedule,
            "task": "users.tasks.send_events_for_active_users",
            "kwargs": json.dumps(
                {
                    "user_id": user_id,
                    "group_id": group_id,
                },
            ),
            "enabled": True,
        },
    )


@shared_task(
    retry_kwargs={"max_retries": 5, "countdown": 5},
    retry_backoff=False,
    retry_jitter=True,
)
def send_events_for_active_users(
    user_id: str | None,
    group_id: str | None,
) -> None:
    show_calendar = SendEventsService()
    show_calendar(
        AlerReceiver(
            user_id=user_id,
            group_id=group_id,
        ),
    )


@shared_task
def clear_crontab() -> None:
    CrontabSchedule.objects.filter(
        periodictask__isnull=True,
    ).delete()
    ClockedSchedule.objects.filter(
        periodictask__isnull=True,
        clocked_time__lt=timezone.now(),
    ).delete()
    PeriodicTask.objects.filter(
        clocked__clocked_time__lt=timezone.now(),
    ).delete()
