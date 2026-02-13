from django.contrib import admin

from event.models import Calendar, Event, GroupChat


@admin.register(Calendar)
class CalendarAdmin(admin.ModelAdmin):
    """
    Админка для календарей.
    """

    list_display = ("id", "key", "title")
    list_display_links = ("key",)
    search_fields = ("id",)


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
    search_fields = ("title", "star", "slash", "all_event")


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
