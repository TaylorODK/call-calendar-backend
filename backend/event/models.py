from django.db import models

from backend.core.constants import NAME_MAX_LENGTH
from backend.core.models import BaseModel


class Event(BaseModel):
    uid = models.IntegerField(
        verbose_name="ID мероприятия",
        unique=True,
        blank=False,
    )
    title = models.CharField(
        verbose_name="Наименование мероприятия",
        max_length=NAME_MAX_LENGTH,
        blank=False,
    )
    date_start = models.DateTimeField(
        verbose_name="Дата и время начала мероприятия",
        blank=False,
    )
    date_end = models.DateTimeField(
        verbose_name="Дата и время завершения мероприятия",
        blank=False,
    )
    description = models.TextField(
        verbose_name="Описание мероприятия",
        blank=True,
        null=True,
        default=None,
    )
    url = models.CharField(
        verbose_name="Ссылка на встречу",
        max_length=NAME_MAX_LENGTH,
        blank=False,
    )
    with_star = models.BooleanField(
        verbose_name="Со звездочкой",
        default=False,
    )
    with_stick = models.BooleanField(
        verbose_name="С палочкой",
        default=False,
    )
    created_at = models.DateTimeField(
        verbose_name="Дата создания",
        auto_now_add=True,
    )
    updated_at = models.DateTimeField(
        verbose_name="Дата обновления",
        auto_now=True,
    )
    user = models.ForeignKey(
        "users.User",
        related_name="events",
        on_delete=models.CASCADE,
    )

    class Meta:
        verbose_name = "Событие"
        verbose_name_plural = "События"

    def __str__(self) -> str:
        return f"Мероприятие {self.title}."
