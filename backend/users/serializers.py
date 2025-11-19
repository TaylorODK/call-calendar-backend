from datetime import timedelta
from typing import Any

from django.db import transaction
from django.utils import timezone
from rest_framework import serializers

from core.constants import CODE_EXPIRATION_TIME
from users.models import User, LoginCode


class LoginCodeCreateSerializer(serializers.ModelSerializer):
    telegram_id = serializers.CharField(required=False)

    class Meta:
        model = LoginCode
        fields = ("id", "code", "email", "telegram_id", "updated_at")
        read_only_fields = ("id", "code", "telegram_id", "updated_at")

    def validate(self, data: dict[str, Any]) -> dict[str, Any]:
        email = data["email"].strip().lower()
        user = User.objects.filter(email=email).first()
        if user and user.is_active:
            raise serializers.ValidationError(
                "❌ Активированный пользователь с таким Email уже существует, "
                "пожалуйста, укажите другой email "
                "и воспользуйтесь командой /register",
                code=400,
            )
        if email.split("@")[-1] != "ylab.team":
            raise serializers.ValidationError(
                "❌ Ваш Email должен быть в домене @ylab.team",
                code=400,
            )
        verification = LoginCode.objects.filter(email=email).first()
        if verification:
            expiration_time = verification.updated_at + timedelta(
                minutes=CODE_EXPIRATION_TIME,
            )
            if timezone.now() < expiration_time:
                raise serializers.ValidationError(
                    "❌ время действия отправленного кода "
                    f"{CODE_EXPIRATION_TIME} минут. "
                    "Новый запрос команды /register можно сделать после "
                    "истечения срока действия кода",
                    code=400,
                )
        return data

    @transaction.atomic
    def create(self, validated_data: dict[str, Any]) -> LoginCode:
        code = LoginCode.get_random_code()
        email = validated_data["email"]
        telegram_id = self.context.get("telegram_id")
        verification = LoginCode.objects.filter(email=email).first()
        if verification:
            verification.code = code
            verification.is_used = False
            verification.save(update_fields=["code", "updated_at"])
            return verification
        User.objects.create(email=email, is_active=False, telegram_id=telegram_id)
        verification = LoginCode.objects.create(
            code=code,
            email=email,
        )
        return verification


class CodeConfirmSerializer(serializers.Serializer):
    code = serializers.CharField(required=True)
    telegram_id = serializers.CharField(required=False)

    def validate(self, data: dict[str, Any]) -> dict[str, Any]:
        telegram_id = self.context.get("telegram_id")
        try:
            user = User.objects.get(telegram_id=telegram_id)
        except User.DoesNotExist:
            raise serializers.ValidationError(
                "❌ Пользователя вашим telegram_id не существует, "
                "пожалуйста, воспользуйтесь заного командрой /register",
                code=400,
            )
        try:
            code_obj = LoginCode.objects.get(code=data["code"], email=user.email)
        except LoginCode.DoesNotExist:
            raise serializers.ValidationError(
                "❌ Неверный код",
                code=400,
            )
        expiration_time = code_obj.updated_at + timedelta(
            minutes=CODE_EXPIRATION_TIME,
        )
        if timezone.now() > expiration_time:
            raise serializers.ValidationError(
                "❌ Время действия кода истекло, чтобы "
                "запросить новый, пожалуйста, "
                "воспользуйтесь командой /register",
                code=400,
            )
        return data

    def create(self, validated_data: dict[str, Any]) -> User:
        telegram_id = self.context.get("telegram_id")
        user = User.objects.get(telegram_id=telegram_id)
        user.is_active = True
        user.save(update_fields=["is_active"])
        return user
