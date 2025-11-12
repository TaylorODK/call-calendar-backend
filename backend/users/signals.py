from django.core.mail import send_mail
from django.db.models.signals import post_save
from django.dispatch import receiver

from users.models import LoginCode


@receiver(post_save, sender=LoginCode)
def send_verification_code_email(sender, instance, created, **kwargs):
    """
    Отправка почты при сохранении или обновлении модели.
    """
    if not instance.is_used:
        send_mail(
            subject="Ваш код подтверждения",
            message=f"Ваш код: {instance.code}",
            from_email="no-reply@example.com",
            recipient_list=[instance.email],
            fail_silently=False,
        )
