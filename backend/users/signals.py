from django.db.models.signals import post_save
from django.dispatch import receiver

from users.models import LoginCode
from users.tasks import send_code_email


@receiver(post_save, sender=LoginCode)
def send_verification_code_email(sender, instance, created, **kwargs):
    """
    Отправка почты при сохранении или обновлении модели.
    """
    if created:
        send_code_email.delay(code_id=instance.id)
