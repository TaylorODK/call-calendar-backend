import logging
import json
from datetime import timedelta
from celery import shared_task, chord
import requests
from django_celery_beat.models import ClockedSchedule, PeriodicTask
from django.utils import timezone
from event.models import Calendar, Event, GroupChat
from event.v2.dto import PreparedData, MessageForSending, MessageToPrepare
from event.v2.services import (
    CalendarService,
    CreateMessageService,
    SendingMessageService,
)
from calendar_backend.settings import BOT_TOKEN
from core.constants import ALERT_TIME_BEFORE_EVENT
from core.exceptions import NotFoundEvent
from users.models import User
from users.v2.dto import CalendarAlert


bot_logger = logging.getLogger("bot")
calendar_logger = logging.getLogger("calendar")


@shared_task
def run_base_update(calendar_id: int):
    """
    Таска по обновлению календаря.
    """

    cal = Calendar.objects.get(id=calendar_id)
    calendar_logger.info(f"Обновление календаря '{cal.title}'")
    parsing = CalendarService()
    parsing(cal=cal)


@shared_task
def start_update_calendar() -> None:
    """
    Таска по обновлению всех календарей.
    """

    calendar_logger.info("Начало задачи по обновлению календарей")
    ids = list(Calendar.objects.values_list("id", flat=True))

    chord(run_base_update.s(cid) for cid in ids)(delete_non_active_events.s())


@shared_task
def delete_non_active_events(_=None) -> None:
    for event in Event.objects.filter(
        is_active=False,
    ).prefetch_related(
        "users",
        "groups",
        "calendar",
    ):
        if event.date_from.date() == timezone.localdate():
            users = tuple(event.users.all())
            groups = tuple(event.groups.all())
            send_message_about_event(event=event, users=users, groups=groups)
        event.delete()


def send_message_about_event(
    event: Event,
    users: tuple[User],
    groups: tuple[GroupChat],
) -> None:
    logging.info(f"Удаление мероприятия {event.title}")
    create_message = CreateMessageService()
    message, status = create_message(
        event=event,
        deleted=True,
    )
    message_to_prepare = MessageToPrepare(
        message=message,
        event_id=event.id,
        status=status,
        users=users,
        groups=groups,
    )
    sending_message = SendingMessageService()
    sending_message(message_to_prepare=message_to_prepare)


@shared_task(
    retry_kwargs={"max_retries": 5, "countdown": 5},
    retry_backoff=False,
    retry_jitter=True,
)
def send_telegram_message(
    prepared_message: MessageForSending | None = None,
    prepared_data: PreparedData | None = None,
    calendar_alert: CalendarAlert | None = None,
) -> list[dict] | None:
    """
    Таска по отправке сообщения в телеграм пользователей:
    Возможны 3 сценария для отправки сообщений:
    1) по результатам парсинга календаря и sending_message_service
    (создание, изменеие, удаление мероприятия);
    2) по результатам обработки запроса пользователя
    на предоставление данных календаря prepared_data
    3) по результатам обработки таски на отправку пользователю
    календаря CalendarAlert
    """

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    responses = []
    if prepared_message:
        try:
            Event.objects.filter(id=prepared_message.event_id).first()
        except Event.DoesNotExist:
            raise NotFoundEvent
        text = prepared_message.message
        for group_tg in prepared_message.groups_tg_ids:
            chat_id = group_tg
            data = make_data_for_response(chat_id=chat_id, text=text)
            responses.append(call_response(url=url, data=data))
        for user_tg in prepared_message.users_tg_ids:
            chat_id = user_tg
            data = make_data_for_response(chat_id=chat_id, text=text)
            responses.append(call_response(url=url, data=data))
    elif prepared_data:
        chat_id = prepared_data.telegram_id
        text = prepared_data.message
        data = make_data_for_response(chat_id=chat_id, text=text)
        responses.append(call_response(url=url, data=data))
    elif calendar_alert:
        chat_id = calendar_alert.telegram_id
        text = calendar_alert.message
        data = make_data_for_response(chat_id=chat_id, text=text)
        responses.append(call_response(url=url, data=data))
    return responses if responses else None


def make_data_for_response(chat_id: str, text: str) -> dict:
    """
    Подготовка данных для отправки сообщения
    """

    return {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }


def call_response(url: str, data: dict):
    """
    Отправка сообщения
    """

    response = requests.post(url, json=data)
    return response.json


@shared_task
def clear_old_events() -> None:
    """
    Задача по удалению старых мероприятий.
    Запускается в 00:00.
    Удаляются мероприятия прошедшего дня.
    """

    calendar_logger.info("Начало задачи по удалению старых мероприятий")
    for event in Event.objects.all():
        if event.date_from.date() < timezone.localdate():
            event.delete()


@shared_task
def create_task_for_alert(event_id: int) -> None:
    """
    Создание задачи по отравке уведомлений в адрес
    пользователя. Запускается по post_save сигналу из
    signals.create_event_alert.
    По итогам создается объекты 2 моделей:
    - ClockedSchedule для времени уведомления;
    - PeriodicTask для задачи по отправки уведомления.
    Если мероприятие было создано менее чем за 10 минут до
    его начала, то ведомление будет отпавлено немедленно и
    объеты моделей создаваться не будут.
    """

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
    """
    Отправка уведомлений в адрес пользователей
    о приближающемся мероприятии.
    Отправляется за 10 минут до созвона.
    ВНИМАНИЕ!
    Отпавка предусмотрена только в адрес пользователей.
    """

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
            data = make_data_for_response(
                chat_id=user.telegram_id,
                text=letter,
            )
            requests.post(url, json=data)


@shared_task
def delete_task_for_alert(event_id):
    """
    Удаление задачи по отправке уведомления.
    Срабатывается по сигналу post_delete модели
    Event из signals.delete_event_alert.
    Необходима для незасорения админки периодическими
    мероприятиями после удаления мероприятий.
    """

    task = PeriodicTask.objects.filter(
        name=f"alert_for_event_{event_id}",
    ).first()
    if task:
        task.delete()
