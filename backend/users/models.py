from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.crypto import get_random_string

from core.constants import NAME_MAX_LENGTH, CODE_MAX_LENGTH
from core.models import BaseModel
from users.manager import UserManager


class User(AbstractUser):
    username = None
    email = models.CharField(
        verbose_name="Электронная почты",
        max_length=NAME_MAX_LENGTH,
        blank=False,
        unique=True,
    )
    telegram_id = models.CharField(
        verbose_name="id телеграм",
        max_length=NAME_MAX_LENGTH,
        unique=True,
    )
    calendar_key = models.CharField(
        verbose_name="Ключ для получения данных из календаря",
        max_length=NAME_MAX_LENGTH,
        blank=True,
    )
    is_active = models.BooleanField(
        verbose_name="is_active",
        default=False,
    )
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["telegram_id"]
    objects = UserManager()

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"

    def __str__(self) -> str:
        return f"{self.email}"


class LoginCode(BaseModel):
    code = models.CharField(
        verbose_name="Ключ для верификации почты",
        max_length=CODE_MAX_LENGTH,
        blank=True,
        null=True,
    )
    email = models.EmailField(
        verbose_name="Почта для верификации",
        max_length=NAME_MAX_LENGTH,
        blank=False,
    )

    class Meta:
        verbose_name = "Верификация почты"
        verbose_name_plural = "Верификации почты"

    def __str__(self) -> str:
        return f"Код для верификации почты {self.email}"

    @staticmethod
    def get_random_code():
        return get_random_string(CODE_MAX_LENGTH, allowed_chars="0123456789")
