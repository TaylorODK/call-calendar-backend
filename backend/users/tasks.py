from celery import shared_task
from django.core.mail import EmailMessage

from users.models import LoginCode


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
        from_email="no-reply@example.com",
        to=[request.email],
    )
    email.send()
