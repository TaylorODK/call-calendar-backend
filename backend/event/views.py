from django.db.models import Q, Prefetch
from django.http import HttpResponse
from django.utils import timezone
from rest_framework.decorators import action
from rest_framework.viewsets import GenericViewSet
from rest_framework.response import Response
from rest_framework import status
from core.constants import CHAT_ID, CALENDAR_KEY
from event.models import Event, Calendar
from event.serializers import EventShowSerializer, UserEventsSerializer
from event.permissions import TelegramUserPermission
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
        print(request.data.get("chat_id"))
        serializer.is_valid(raise_exception=True)
        print(serializer.validated_data.get("chat_id"))
        print(CHAT_ID)
        if serializer.validated_data.get("chat_id") == CHAT_ID:
            print("True")
            events_qs = Event.objects.filter(
                Q(
                    date_from__date=timezone.localdate(),
                    date_till__gt=timezone.now(),
                ),
            ).order_by(
                "date_from",
            )
            calendar = Calendar.objects.get(
                key=CALENDAR_KEY,
            )
            queryset = User.objects.filter(
                calendar=calendar,
            ).prefetch_related(
                Prefetch(
                    "events",
                    queryset=events_qs,
                    to_attr="filtered_events",
                ),
            )
            serializer = UserEventsSerializer(queryset, many=True)
        else:
            queryset = self.get_queryset()
            serializer = EventShowSerializer(queryset, many=True)
        return Response(
            {
                "meetings": serializer.data,
            },
            status=status.HTTP_200_OK,
        )


def always_ok(request):
    return HttpResponse("Ok")
