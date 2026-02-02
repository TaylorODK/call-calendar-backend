from django.db.models import Q
from django.http import HttpResponse
from django.utils import timezone
from rest_framework.decorators import action
from rest_framework.viewsets import GenericViewSet
from rest_framework.response import Response
from rest_framework import status
from core.constants import CHAT_ID, CALENDAR_KEY
from event.models import Event
from event.serializers import EventShowSerializer, UserEventsSerializer
from event.permissions import TelegramUserPermission
from event.utils import events_for_group
from users.models import User


class EventShowView(GenericViewSet):
    permission_classes = (TelegramUserPermission,)

    def get_queryset(self):
        user = self.request.telegram_user
        base_q = Q(
            date_from__date=timezone.localdate(),
            date_till__gt=timezone.now(),
            calendar=user.calendar,
            users=user,
        )
        return (
            Event.objects.filter(
                base_q,
            )
            .prefetch_related(
                "users",
            )
            .select_related(
                "calendar",
            )
            .order_by(
                "date_from",
            )
        )

    @action(
        methods=["GET"],
        url_path="meetings",
        detail=False,
    )
    def show_events(self, request):
        user = User.objects.get(telegram_id=request.headers.get("telegram-id"))
        if not user.is_active:
            return Response(
                {
                    "error": "Пользователь не был активирован,"
                    " повторите регистрацию.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer = UserEventsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if serializer.validated_data.get("chat_id") == CHAT_ID:
            events_qs = Event.objects.filter(
                Q(
                    date_from__date=timezone.localdate(),
                    date_till__gt=timezone.now(),
                    calendar__key=CALENDAR_KEY,
                ),
            ).order_by(
                "date_from",
            )
            serializer = events_for_group(events_qs)
            return Response(
                {
                    "meetings": serializer,
                },
                status=status.HTTP_200_OK,
            )
        else:
            return Response(
                {
                    "meetings": EventShowSerializer(
                        self.get_queryset(),
                        many=True,
                    ).data,
                },
                status=status.HTTP_200_OK,
            )


def always_ok(request):
    return HttpResponse("Ok")
