from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from users.serializers import LoginCodeCreateSerializer


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
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {
                "send-code": "Код подтверждения отправлен",
            },
            status=status.HTTP_201_CREATED,
        )
