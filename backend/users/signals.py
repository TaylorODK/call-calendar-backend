from django.db.models.signals import post_save
from django.dispatch import receiver

from users.models import LoginCode, User
from users.tasks import send_code_email, create_event_schedule


@receiver(post_save, sender=LoginCode)
def send_verification_code_email(sender, instance, created, **kwargs):
    """
    Отправка почты при сохранении модели.
    """
    send_code_email.delay(code_id=instance.id)


@receiver(post_save, sender=User)
def update_shchedule_for_user(
    sender, instance, created, update_fields, **kwargs
) -> None:
    """
    Обновление графика про сохранении модели пользователя.
    """
    if not update_fields:
        return
    if instance.is_active and "calendar_show_time" in update_fields:
        create_event_schedule.delay(user_id=instance.id)
