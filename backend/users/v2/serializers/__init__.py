# Сериализаторы регистрации пользователя
from users.v2.serializers.registration_serializers import (
    CodeConfirmSerializer,  # noqa
    LoginCodeCreateSerializer,  # noqa
)

# Сериализатор для установки и изменения времени отображения календаря
from users.v2.serializers.set_time_serializer import SetShowTimeSerializer  # noqa
