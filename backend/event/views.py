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
        prepared_data = ShowCalendarService(data).__call__()
        if prepared_data.data:
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
