from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from users.serializers import LoginCodeCreateSerializer, CodeConfirmSerializer


class EmailCheckViewSet(GenericViewSet):
    permission_classes = (AllowAny,)

    def get_serializer_class(self):
        return {
            "register": LoginCodeCreateSerializer,
        }.get(self.action, LoginCodeCreateSerializer)

    @action(url_path="register", detail=False, methods=["POST"])
    def register(self, request):
        serializer = LoginCodeCreateSerializer(
            data=request.data,
            context={"telegram_id": request.headers.get("Telegram-ID")},
        )
        if serializer.is_valid():
            serializer.save()
            return Response(
                {
                    "send-code": "Код подтверждения отправлен",
                },
                status=status.HTTP_201_CREATED,
            )
        return Response(
            {
                "message": str(serializer.errors),
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    @action(url_path="code", detail=False, methods=["POST"])
    def code(self, request):
        serializer = CodeConfirmSerializer(
            data=request.data,
            context={"telegram_id": request.headers.get("Telegram-ID")},
        )
        if serializer.is_valid():
            serializer.save()
            return Response(
                {
                    "code-confirm": "Пользователь активирован",
                },
                status=status.HTTP_201_CREATED,
            )
        return Response(
            {
                "message": str(serializer.errors),
            },
            status=status.HTTP_400_BAD_REQUEST,
        )
