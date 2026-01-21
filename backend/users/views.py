import logging

from typing import Type

from rest_framework import status, serializers
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from users.models import User
from users.serializers import (
    LoginCodeCreateSerializer,
    CodeConfirmSerializer,
    SetShowTimeSerializer,
)


logger = logging.getLogger("app")


class EmailCheckViewSet(GenericViewSet):
    permission_classes = (AllowAny,)

    def get_serializer_class(self) -> Type[serializers.Serializer]:
        return {
            "register": LoginCodeCreateSerializer,
            "code": CodeConfirmSerializer,
        }.get(self.action, LoginCodeCreateSerializer)

    @action(url_path="email", detail=False, methods=["POST"])
    def register(self, request: Request, *args, **kwargs) -> Response:
        if not request.headers.get("telegram-id"):
            return Response(
                {
                    "detaid": "Не был получен telegram-id",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer = LoginCodeCreateSerializer(
            data=request.data,
            context={"telegram_id": request.headers.get("telegram-id")},
        )
        if serializer.is_valid():
            instance = serializer.save()
            logger.info(
                f"Регистрация пользователя {instance.email}",
                extra={
                    "method": self.action,
                    "status": status.HTTP_201_CREATED,
                },
            )
            return Response(
                {
                    "code": "Код подтверждения отправлен",
                },
                status=status.HTTP_201_CREATED,
            )
        logger.info(
            f"Ошибка регистрации пользователя {request.data["email"]}",
            extra={
                "method": self.action,
                "status": status.HTTP_400_BAD_REQUEST,
            },
        )
        return Response(
            {
                "detail": list(serializer.errors.values())[0][0],
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    @action(url_path="code", detail=False, methods=["POST"])
    def code(self, request: Request, *args, **kwargs) -> Response:
        if not request.headers.get("telegram-id"):
            return Response(
                {
                    "detaid": "Не был получен telegram-id",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer = CodeConfirmSerializer(
            data=request.data,
            context={"telegram_id": request.headers.get("telegram-id")},
        )
        if serializer.is_valid():
            instance = serializer.save()
            logger.info(
                f"Активация пользователя {instance.email}",
                extra={
                    "method": self.action,
                    "status": status.HTTP_201_CREATED,
                },
            )
            return Response(
                {
                    "confirm": "Пользователь активирован",
                },
                status=status.HTTP_201_CREATED,
            )
        logger.info(
            "Ошибка активации пользователя",
            extra={
                "method": self.action,
                "status": status.HTTP_400_BAD_REQUEST,
            },
        )
        return Response(
            {
                "detail": list(serializer.errors.values())[0][0],
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    @action(
        url_path="set_time",
        detail=False,
        methods=["PATCH"],
        permission_classes=(IsAuthenticated,),
    )
    def set_show_time(self, request):
        user = User.objects.get(telegram_id=request.headers.get("telegram-id"))
        if not user.is_active:
            return Response(
                {
                    "error": "Пользователь не был активирован,"
                    " повторите регистрацию.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer = SetShowTimeSerializer(
            user,
            data=request.data,
            partial=True,
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {
                "message": "Установлено время отображения календаря",
                "время": serializer.data["show_time"],
            },
            status=status.HTTP_200_OK,
        )
