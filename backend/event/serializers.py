from rest_framework import serializers
from event.models import Event


class EventShowSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = ("date_from", "date_till", "title", "description")
