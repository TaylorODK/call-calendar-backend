from django.db import models
from django.contrib.auth.models import AbstractBaseUser

from calendar_backend.constants import NAME_MAX_LENGTH


class User(AbstractBaseUser):
    """
    Кастомная модель пользователя.
    """

    email = models.EmailField(
        max_length=NAME_MAX_LENGTH,
        unique=True,
        blank=False,
        verbose_name="Email пользователя",
    )
    telegram_id = models.CharField(
        max_length=NAME_MAX_LENGTH,
        unique=True,
        blank=False,
        verbose_name="Telegram ID пользователя",
    )
    first_name = models.CharField(
        max_length=NAME_MAX_LENGTH,
        blank=True,
        null=True,
        verbose_name="Имя",
    )
    last_name = models.CharField(
        max_length=NAME_MAX_LENGTH,
        blank=True,
        null=True,
        verbose_name="Фамилия",
    )
    yandex_calendar_key = models.CharField(
        max_length=NAME_MAX_LENGTH,
        unique=True,
        blank=True,
        null=True,
        verbose_name="Приватный ключ яндекс календаря пользователя",
    )
    REQUIRED_FIELDS = [email, telegram_id]
    USERNAME_FIELD = "email"

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"

    def __str__(self):
        return f"{self.email}"
