from django.db import models
from django.contrib.auth import get_user_model

from calendar_backend.constants import NAME_MAX_LENGTH


USER = get_user_model()


class Event(models.Model):
    uid = models.IntegerField(unique=True, blank=False, verbose_name="ID мероприятия")
    title = models.CharField(
        max_length=NAME_MAX_LENGTH,
        blank=False,
        verbose_name="Наименование мероприятия",
    )
    dt_start = models.DateTimeField(
        blank=False, verbose_name="Дата и время начала мероприятия"
    )
    dt_end = models.DateTimeField(
        blank=False, verbose_name="Дата и время завершения мероприятия"
    )
    description = models.TextField(
        blank=True,
        null=True,
        default=None,
        verbose_name="Описание мероприятия",
    )
    url = models.CharField(
        max_length=NAME_MAX_LENGTH,
        blank=False,
        verbose_name="Ссылка на встречу",
    )
    with_star = models.BooleanField(default=False, verbose_name="Со звездочкой")
    with_stick = models.BooleanField(default=False, verbose_name="С палочкой")
    created = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")
    user = models.ForeignKey(USER, related_name="events", on_delete=models.CASCADE)

    class Meta:
        verbose_name = "Событие"
        verbose_name_plural = "События"

    def __str__(self):
        return f"Мероприятие {self.title}."
