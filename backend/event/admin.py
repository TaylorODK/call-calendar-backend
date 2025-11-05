from django.contrib import admin

from event.models import Event
# Register your models here.


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ("uid", "title", "date_start", "user")
    list_display_links = ("uid", "title")
    search_fields = ("user",)
    list_select_related = ("user",)
