from django.contrib import admin

from event.models import Calendar, Event, GroupChat
from users.tasks import create_event_schedule
from typing import Any


@admin.register(Calendar)
class CalendarAdmin(admin.ModelAdmin):
    """
    Админка для календарей.
    """

    list_display = ("id", "title", "key")
    list_display_links = ("title",)
    search_fields = ("title",)


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    """
    Админка для мероприятий.
    """

    list_display = (
        "id",
        "title",
        "date_from",
        "date_till",
        "star",
        "slash",
        "all_event",
        "created_at",
    )
    list_display_links = ("title",)
    search_fields = ("title",)
    list_filter = ("star", "slash", "all_event")

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.prefetch_related(
            "calendar",
            "users",
            "groups",
        )


@admin.register(GroupChat)
class GroupAdmin(admin.ModelAdmin):
    """
    Админка для групп .
    """

    list_display = (
        "id",
        "title",
        "chat_id",
        "calendar",
    )
    list_display_links = ("title",)
    search_fields = ("title",)

    def save_model(
        self,
        request: Any,
        obj: Any,
        form: Any,
        change: bool,
    ) -> None:
        if change and "calendar_show_time" in form.changed_data:
            super().save_model(request, obj, form, change)
            create_event_schedule(group_id=obj.id)
            return
        super().save_model(request, obj, form, change)
