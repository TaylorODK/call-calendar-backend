from django.utils import timezone
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from event.models import Event, GroupChat
from event.tasks import create_task_for_alert, delete_task_for_alert
from users.tasks import create_event_schedule


@receiver(post_save, sender=Event)
def create_event_alert(sender, instance, created, update_fields=None, **kwargs):
    """
    Создание разовой задачи по отправке уведомления
    за 15 минут до мероприятия.
    """

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
