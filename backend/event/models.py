import re

from django.db import models

from core.constants import NAME_MAX_LENGTH
from core.models import BaseModel


class Calendar(models.Model):
    title = models.CharField(
        verbose_name="Наименование календаря",
        max_length=NAME_MAX_LENGTH,
    )
    key = models.CharField(
        verbose_name="Ключ от календаря",
        max_length=NAME_MAX_LENGTH,
        help_text="Ключ необходимо указать с &tz_id=Europe/Moscow",
    )

    class Meta:
        verbose_name = "Календарь"
        verbose_name_plural = "Календари"

    def __str__(self):
        return self.title


class Event(BaseModel):
    uid = models.CharField(
        verbose_name="UID мероприятия",
        max_length=NAME_MAX_LENGTH,
        unique=True,
    )
    date_from = models.DateTimeField(
        verbose_name="Дата и время начала мероприятия",
        blank=True,
    )
    date_till = models.DateTimeField(
        verbose_name="Дата и время завершения мероприятия",
        blank=True,
    )
    title = models.TextField(
        verbose_name="Наименование мероприятия",
        blank=True,
    )
    description = models.TextField(verbose_name="Описание мероприятия", blank=True)
    url_calendar = models.CharField(
        "Ссылка на мероприятие",
        max_length=NAME_MAX_LENGTH,
        blank=True,
    )
    star = models.BooleanField(
        verbose_name="Со звездочкой",
        default=False,
    )
    slash = models.BooleanField(
        verbose_name="Со слэшем",
        default=False,
    )
    all_event = models.BooleanField(
        verbose_name="Общее мероприятие",
        default=False,
    )
    calendar = models.ForeignKey(
        Calendar,
        on_delete=models.CASCADE,
        related_name="events",
    )
    users = models.ManyToManyField(
        "users.User",
        related_name="events",
        blank=True,
    )

    class Meta:
        verbose_name = "Мероприятие"
        verbose_name_plural = "Мероприятия"

    def check_for_star_slash(self):
        if bool(re.search(r"/\*$", self.title)):
            self.star = True
            self.slash = True
        else:
            self.star = "*" in self.title
            self.slash = bool(re.search(r"/+$", self.title))
        self.all_event = not self.star and not self.slash
