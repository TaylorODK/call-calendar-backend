from django.contrib import admin
from users.models import User


# Register your models here.
@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("id", "email", "telegram_id", "yandex_calendar_key")
    list_display_links = (
        "id",
        "email",
    )
    search_fields = ("email",)
