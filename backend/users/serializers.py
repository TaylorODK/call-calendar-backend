from datetime import timedelta

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

    def validate(self, data):
        email = data["email"].strip().lower()
        used_email = User.objects.filter(email=email).first()
        if used_email and used_email.is_active:
            raise serializers.ValidationError(
                "Активированный пользователь с таким Email уже существует",
            )
        if email.split("@")[-1] != "ylab.team":
            raise serializers.ValidationError(
                "Email должен быть в домене @ylab.team",
            )
        verification = LoginCode.objects.filter(email=email).first()
        if verification:
            expiration_time = verification.updated_at + timedelta(
                minutes=CODE_EXPIRATION_TIME,
            )
            if timezone.now() < expiration_time:
                raise serializers.ValidationError(
                    f"Новый запрос можно сделать через {CODE_EXPIRATION_TIME} минут",
                )
        return data

    @transaction.atomic
    def create(self, validated_data):
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

    def validate(self, attrs):
        telegram_id = self.context.get("telegram_id")
        try:
            user = User.objects.get(telegram_id=telegram_id)
        except User.DoesNotExist:
            raise serializers.ValidationError(
                "Пользователя с данным telegram_id не существует",
            )
        try:
            code_obj = LoginCode.objects.get(code=attrs["code"], email=user.email)
        except LoginCode.DoesNotExist:
            raise serializers.ValidationError("Неверный код")
        expiration_time = code_obj.updated_at + timedelta(
            minutes=CODE_EXPIRATION_TIME,
        )
        if timezone.now() > expiration_time:
            raise serializers.ValidationError(
                f"Время действия кода {CODE_EXPIRATION_TIME} минут",
            )
        return attrs

    def create(self, validated_data):
        telegram_id = self.context.get("telegram_id")
        user = User.objects.get(telegram_id=telegram_id)
        user.is_active = True
        user.save(update_fields=["is_active"])
        return user
