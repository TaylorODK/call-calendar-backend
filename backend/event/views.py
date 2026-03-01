from django.http import HttpResponse
from rest_framework.decorators import action
from rest_framework.viewsets import GenericViewSet
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from event.serializers import (
    TelegramDataSerializer,
)
from event.v2.dto import RequestForCalendar
from event.v2.services import ShowCalendarService


class EventShowView(GenericViewSet):
    """
    Вьюсет для отображения мероприятий в календарях.
    Предусмотрены 2 варианта:
    1) отображение личного календаря;
    2) отображение группового календря (хардкод).
    Допускается возможность сделать запрос любым пользователям,
    в случае, если пользователь не прошел регистрацию или активацию,
    либо пользователю не назначен календарь, в его адрес будет направлено
    сообщение от бота с информацией о причинах
    ошибки предоставления календаря.
    """

    permission_classes = (AllowAny,)

    @action(
        methods=["GET"],
        url_path="meetings",
        detail=False,
    )
    def show_events(self, request):
        serializer = TelegramDataSerializer(
            data={
                "telegram_id": request.headers.get("telegram-id"),
                "chat_id": request.data.get("chat_id"),
            },
        )
        serializer.is_valid(raise_exception=True)
        data = RequestForCalendar(
            telegram_id=request.headers.get("telegram-id"),
            chat_id=str(request.data.get("chat_id")),
        )
        show_service = ShowCalendarService()
        prepared_data = show_service(data)
        if not prepared_data.message:
            return Response(
                {
                    "meetings": prepared_data.data,
                },
                status=status.HTTP_200_OK,
            )
        return Response(
            {
                "errors": prepared_data.message,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )


def always_ok(request):
    return HttpResponse("Ok")
