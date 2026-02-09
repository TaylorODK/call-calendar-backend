from django.utils import timezone
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from event.models import Event
from event.tasks import create_task_for_alert, delete_task_for_alert


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
    delete_task_for_alert.delay(event_id=instance.id)
