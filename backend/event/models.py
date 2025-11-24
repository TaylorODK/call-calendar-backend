import re

from django.db import models

from core.constants import NAME_MAX_LENGTH
from core.models import BaseModel


class Calendar(models.Model):
    key = models.CharField(
        verbose_name="Ключ от календаря",
        max_length=NAME_MAX_LENGTH,
    )

    class Meta:
        verbose_name = "Календарь"
        verbose_name_plural = "Календари"


class Event(BaseModel):
    uid = models.CharField(
        verbose_name="UID мероприятия",
        max_length=NAME_MAX_LENGTH,
        unique=True,
    )
    date_from = models.DateTimeField(
        verbose_name="Дата и время начала мероприятия",
    )
    date_till = models.DateTimeField(
        verbose_name="Дата и время завершения мероприятия",
    )
    title = models.TextField(
        verbose_name="Наименование мероприятия",
    )
    description = models.TextField(verbose_name="Описание мероприятия")
    url_calendar = models.CharField(
        "Ссылка на мероприятие",
        max_length=NAME_MAX_LENGTH,
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

    class Meta:
        verbose_name = "Мероприятие"
        verbose_name_plural = "Мероприятия"

    def check_for_star_slash(self):
        self.star = "*" in self.title
        self.slash = bool(re.search(r"/$", self.title))
        self.all_event = not self.star and not self.slash
