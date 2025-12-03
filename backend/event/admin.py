from django.contrib import admin

from event.models import Calendar, Event


@admin.register(Calendar)
class CalendarAdmin(admin.ModelAdmin):
    list_display = ("id", "key")
    list_display_links = ("key",)
    search_fields = ("id",)


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
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
