from django.db.models import Q
from django.utils import timezone
from rest_framework.decorators import action
from rest_framework.viewsets import GenericViewSet
from rest_framework.response import Response
from rest_framework import status
from event.models import Event
from event.serializers import EventShowSerializer
from event.permissions import TelegramUserPermission


class EventShowView(GenericViewSet):
    permission_classes = (TelegramUserPermission,)

    def get_queryset(self):
        user = self.request.telegram_user
        base_q = Q(
            date_from__date=timezone.localdate(),
            date_from__gt=timezone.now(),
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
        queryset = self.get_queryset()
        serializer = EventShowSerializer(queryset, many=True)
        return Response(
            {
                "meetings": serializer.data,
            },
            status=status.HTTP_200_OK,
        )
