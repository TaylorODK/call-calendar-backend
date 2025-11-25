import re
from rest_framework import serializers
from event.models import Event


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
        time_start = instance.date_from.strftime("%d.%m.%Y %H:%M")
        time_end = instance.date_till.strftime("%H:%M")
        if time_end:
            return f"{time_start} - {time_end}"
        return f"{time_start}"
