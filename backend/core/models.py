from django.db import models

# Create your models here.


class BaseModel(models.Model):
    created_at = models.DateTimeField(
        verbose_name="Дата и время создания",
        auto_now_add=True,
    )
    updated_at = models.DateTimeField(
        verbose_name="Дата и время обновления",
        auto_now=True,
    )
    is_active = models.BooleanField(verbose_name="Активность", default=True)

    class Meta:
        abstract = True
