from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin

from core.constants import NAME_MAX_LENGTH
from core.models import BaseModel
from users.managers import UserManager


class User(AbstractBaseUser, PermissionsMixin, BaseModel):
    """
    Кастомная модель пользователя.
    """

    email = models.EmailField(
        verbose_name="Email пользователя",
        max_length=NAME_MAX_LENGTH,
        unique=True,
        blank=False,
    )
    telegram_id = models.CharField(
        verbose_name="Telegram ID пользователя",
        max_length=NAME_MAX_LENGTH,
        unique=True,
        blank=False,
    )
    first_name = models.CharField(
        verbose_name="Имя",
        max_length=NAME_MAX_LENGTH,
        blank=True,
        null=True,
    )
    last_name = models.CharField(
        verbose_name="Фамилия",
        max_length=NAME_MAX_LENGTH,
        blank=True,
        null=True,
    )
    yandex_calendar_key = models.CharField(
        verbose_name="Приватный ключ яндекс календаря пользователя",
        max_length=NAME_MAX_LENGTH,
        unique=True,
        blank=True,
        null=True,
    )
    is_staff = models.BooleanField(verbose_name="Staff", default=True)
    is_superuser = models.BooleanField(verbose_name="Superuser", default=False)
    REQUIRED_FIELDS = ["telegram_id"]
    USERNAME_FIELD = "email"
    objects = UserManager()

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"

    def __str__(self) -> str:
        return f"{self.email}"
