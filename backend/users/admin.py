from django.contrib import admin
from users.models import User
from users.tasks import create_event_schedule
from typing import Any


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "email",
        "telegram_id",
        "calendar",
        "calendar_show_time",
    )
    list_display_links = (
        "id",
        "email",
    )
    search_fields = ("email",)

    def save_model(
        self,
        request: Any,
        obj: Any,
        form: Any,
        change: bool,
    ) -> None:
        if change and obj.is_active and "calendar_show_time" in form.changed_data:
            super().save_model(request, obj, form, change)
            create_event_schedule(user_id=obj.id)
            return
        super().save_model(request, obj, form, change)
