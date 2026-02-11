from datetime import timedelta
from typing import Any
from django.db import transaction
from django.utils import timezone
from rest_framework import serializers
from core.enums import ErrorCodes
from core.constants import CODE_EXPIRATION_TIME
from users.models import User, LoginCode


class LoginCodeCreateSerializer(serializers.ModelSerializer):
    """
    Сериализатор получения email пользователя
    для регистрации и отправки пользователю
    на почту кода подтверждения.
    Ожидает в context:
        - telegram_id: str
    Ожидаемое тело запроса:
        {
            "email": "example@ylab.io",
        }
    """

    telegram_id = serializers.CharField(required=False)

    class Meta:
        model = LoginCode
        fields = ("id", "code", "email", "telegram_id", "updated_at")
        read_only_fields = ("id", "code", "telegram_id", "updated_at")

    @transaction.atomic
    def create(self, validated_data: dict[str, Any]) -> LoginCode:
        """
        Атоматорное создание объектов модели LoginCode и User.
        """

        code = LoginCode.get_random_code()
        email = validated_data["email"]
        telegram_id = self.context.get("telegram_id")
        verification, created = LoginCode.objects.get_or_create(
            email=email,
            defaults={"code": code},
        )
        if not created:
            verification.code = code
            verification.save(update_fields=["code", "updated_at"])
        user = User.objects.filter(
            telegram_id=telegram_id,
        ).first()
        if user:
            user.email = email
            user.is_active = False
            user.save(update_fields=["email", "is_active"])
        else:
            User.objects.create(
                email=email,
                is_active=False,
                telegram_id=telegram_id,
            )
        return verification


class CodeConfirmSerializer(serializers.Serializer):
    """
    Сериализатор подтверждения кода и активации пользователя.
    Ожидает в context:
        - telegram_id: str
    Ожидаемое тело запроса:
        {
            "code": 1234
        }
    """

    code = serializers.CharField(required=True)
    telegram_id = serializers.CharField(required=False)

    def validate(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Валидация кода, пользователя и email:
            - проверка на существование User с telegram_id из запроса;
            - проверка на совпадение кода пользователя;
            - проверка на истечения срока действия кода.
        """

        telegram_id = self.context.get("telegram_id")
        try:
            user = User.objects.get(telegram_id=telegram_id)
        except User.DoesNotExist:
            raise serializers.ValidationError(
                "❌ Пользователя вашим telegram_id не существует, "
                "пожалуйста, воспользуйтесь заного командрой /email",
                code=ErrorCodes.ID_DONT_EXIST,
            )
        try:
            code_obj = LoginCode.objects.get(
                code=data["code"],
                email=user.email,
            )
        except LoginCode.DoesNotExist:
            raise serializers.ValidationError(
                "❌ Неверный код",
                code=ErrorCodes.WRONG_CODE,
            )
        expiration_time = code_obj.updated_at + timedelta(
            minutes=CODE_EXPIRATION_TIME,
        )
        if timezone.now() > expiration_time:
            raise serializers.ValidationError(
                "❌ Время действия кода истекло, чтобы "
                "запросить новый, пожалуйста, "
                "воспользуйтесь командой /email",
                code=ErrorCodes.CODE_EXPIRED,
            )
        return data

    def create(self, validated_data: dict[str, Any]) -> User:
        """
        После валидации данных пользователь становится активированным.
        Активированному пользователю необходимо добавить через
        админку календарь, после чего он сможет получать мероприятия
        из календаря, уведолмения об изменениях в мероприятиях и
        настроить себе время ежедневного получения календаря.
        """

        telegram_id = self.context.get("telegram_id")
        user = User.objects.get(telegram_id=telegram_id)
        user.is_active = True
        user.save(update_fields=["is_active"])
        return user


class CheckRegistrationDataSerializer(serializers.Serializer):
    telegram_id = serializers.IntegerField(required=True)
    email = serializers.EmailField(required=True)
