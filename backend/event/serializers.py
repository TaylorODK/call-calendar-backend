import re
from rest_framework import serializers
from event.models import Event
from django.utils import timezone


class EventShowSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()
    meeting_time = serializers.SerializerMethodField()

    class Meta:
        model = Event
        fields = ("meeting_time", "title", "url")

    def get_url(self, instance):
        text = instance.description
        url_pattern = r"https?://[^\s]+"
        match = re.search(url_pattern, text)
        return match.group() if match else None

    def get_meeting_time(self, instance):
        date_from = timezone.localtime(instance.date_from)
        if instance.date_till:
            date_till = timezone.localtime(instance.date_till)
            return f"{date_from:%H:%M} - {date_till:%H:%M}"
        return f"{date_from:%H:%M}"
