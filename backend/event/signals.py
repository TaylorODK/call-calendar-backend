from django.utils import timezone
from django.db.models.signals import post_save, post_delete, m2m_changed
from django.dispatch import receiver

from event.models import Event, GroupChat, Calendar, SendedMessages
from event.tasks import create_task_for_alert, delete_task_for_alert
from event.v2.dto import MessageToPrepare
from event.v2.services import SendingMessageService
from users.models import User
from users.tasks import create_event_schedule


@receiver(post_save, sender=Event)
def create_event_alert(sender, instance, created, update_fields=None, **kwargs):
    """
    Создание разовой задачи по отправке уведомления
    за 15 минут до мероприятия.
    """
    if instance.date_from.date() != timezone.localdate():
        return
    if (
        not created
        and (not update_fields or "date_from" not in update_fields)
        or instance.date_from < timezone.now()
    ):
        return
    create_task_for_alert.delay(event_id=instance.id)


@receiver(post_delete, sender=Event)
def delete_event_alert(sender, instance, **kwargs):
    """
    Удаление задач уведомления после удаления мероприятий.
    """

    delete_task_for_alert.delay(event_id=instance.id)


@receiver(post_save, sender=GroupChat)
def update_shchedule_for_group_chat(sender, instance, update_fields, **kwargs) -> None:
    """
    Обновление графика про сохранении модели группового чата.
    """

    if not update_fields:
        return
    if "calendar_show_time" in update_fields:
        create_event_schedule.delay(groud_id=instance.id)


@receiver(m2m_changed, sender=Event.calendar.through)
def send_message_to_added_or_deleted_calendar_users(
    sender, instance, action, pk_set, **kwargs
):
    if action == "post_add":
        new_calendar = Calendar.objects.filter(pk__in=pk_set)
        sended_message = SendedMessages.objects.filter(event=instance).first()
        users = User.objects.filter(calendar__in=new_calendar)
        groups = GroupChat.objects.filter(calendar__in=new_calendar)
        if sended_message:
            users_list = []
            groups_list = []
            for user in users:
                if user not in sended_message.users.all():
                    users_list.append(user)
            users = users_list
            for group in groups:
                if group not in sended_message.groups.all():
                    groups_list.append(group)
            groups = groups_list
        if instance.message:
            sending_message = SendingMessageService()
            sending_message(
                message_to_prepare=MessageToPrepare(
                    message=instance.message,
                    event_id=instance.id,
                    users=users,
                    groups=groups,
                    status=None,
                ),
            )
