import re
from django.db import models
from django.utils import timezone
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
    aiterus = models.BooleanField(
        verbose_name="Аитерус",
        default=False,
    )
    calendar = models.ManyToManyField(
        Calendar,
        related_name="events",
        blank=True,
    )
    users = models.ManyToManyField(
        "users.User",
        related_name="events",
        blank=True,
    )
    groups = models.ManyToManyField(
        "event.GroupChat",
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
            self.aiterus = bool(re.search(r"\b[Аа][ий]терус\b", self.title))
        self.all_event = not self.star and not self.slash and not self.aiterus

    def url_for_event(self):
        text = self.description
        url_pattern = r"https?://[^\s]+"
        match = re.search(url_pattern, text)
        return match.group() if match else None

    def time_for_event(self):
        date_from = timezone.localtime(self.date_from)
        if self.date_till:
            date_till = timezone.localtime(self.date_till)
            return f"{date_from:%H:%M} - {date_till:%H:%M}"
        return f"{date_from:%H:%M}"


class GroupChat(models.Model):
    """
    Модель группового чата.
    Объекты модели будут добавляться вручную в админке.
    Модель сделана для отправки в групповые чаты уведомлений
    о создании/изменении/удалении мероприятий.
    Поля:
    - title: str
    - chat_id: str
    - calendar: FK Calendar
    """

    title = models.CharField(
        verbose_name="Наименование чата",
        max_length=NAME_MAX_LENGTH,
        unique=True,
    )
    chat_id = models.CharField(
        verbose_name="Id группового чата",
        max_length=NAME_MAX_LENGTH,
        unique=True,
    )
    calendar = models.ForeignKey(
        Calendar,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="groups",
    )

    class Meta:
        verbose_name = "Групповой чат"
        verbose_name_plural = "Групповые чаты"

    def __str__(self) -> str:
        return f"{self.title}"
