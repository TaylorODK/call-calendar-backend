from rest_framework import serializers
from users.models import User


class SetShowTimeSerializer(serializers.ModelSerializer):
    """
    Сериализатор для установки времени ежедневной
    отправки календаря пользователю.
    Время в запросе указывается в 24-часовом формате.
    Ожидает в context:
        - telegram_id: str
    Ожидаемое тело запроса:
        {
            "time": 12:30
        }
    """

    time = serializers.TimeField()

    class Meta:
        model = User
        fields = ("time",)

    def update(self, instance, validated_data):
        """
        После обноаления поля calendar_show_time в периодических
        мероприятиях по сигналу добавляется событие по отрпавке
        календаря пользователю ежеденвно к указанное в запросе время.
        """
        instance.calendar_show_time = validated_data["time"]
        instance.save(update_fields=["calendar_show_time"])
        return instance
