import logging


from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet
from event.permissions import TelegramUserPermission
from users.models import User
from users.v2.serializers import (
    LoginCodeCreateSerializer,
    CodeConfirmSerializer,
    SetShowTimeSerializer,
    CheckRegistrationDataSerializer,
)
from users.v2.dto import RegistrationData
from users.v2.services import RegistrationService

logger = logging.getLogger("app")


class EmailCheckViewSet(GenericViewSet):
    permission_classes = (AllowAny,)

    @action(url_path="email", detail=False, methods=["POST"])
    def register(self, request: Request, *args, **kwargs) -> Response:
        if not request.headers.get("telegram-id"):
            return Response(
                {
                    "detail": "Не был получен telegram-id",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        telegram_id = request.headers.get("telegram-id")
        serializer = CheckRegistrationDataSerializer(
            data={
                "telegram_id": telegram_id,
                "email": request.data.get("email"),
            },
        )
        serializer.is_valid(raise_exception=True)
        regictration_start = RegistrationService()
        registration_check = regictration_start(
            registration_data=RegistrationData(
                telegram_id=telegram_id,
                email=request.data.get("email"),
            ),
        )
        if registration_check.can_send_code:
            serializer = LoginCodeCreateSerializer(
                data=request.data,
                context={"telegram_id": telegram_id},
            )
            serializer.is_valid(raise_exception=True)
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
        logger.error(
            f"""Ошибка регистрации пользователя: \n
            код - {registration_check.error.error_code}. \n
            сообщение - {registration_check.error.error_message}
            telegram_id - {
                (
                    telegram_id
                ) if telegram_id else None
            }.
            """,
            extra={
                "method": self.action,
                "status": status.HTTP_400_BAD_REQUEST,
            },
        )
        return Response(
            {
                "detail": registration_check.error.error_message,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    @action(url_path="code", detail=False, methods=["POST"])
    def code(self, request: Request, *args, **kwargs) -> Response:
        if not request.headers.get("telegram-id"):
            return Response(
                {
                    "detail": "Не был получен telegram-id",
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
                    "confirm": "Пользователь активирован,"
                    " для получения данных календаря вам надо нажать кнопку "
                    "'Мои созвоны'",
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
        methods=["POST"],
        permission_classes=(TelegramUserPermission,),
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
                "confirm": "Время установлено",
            },
            status=status.HTTP_200_OK,
        )
