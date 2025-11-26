from django.db.models import Q
from django.utils import timezone
from rest_framework.decorators import action
from rest_framework.viewsets import GenericViewSet
from rest_framework.response import Response
from rest_framework import status
from event.models import Event
from event.utils import parse_ics
from event.serializers import EventShowSerializer
from event.permissions import TelegramUserPermission


class EventShowView(GenericViewSet):
    permission_classes = (TelegramUserPermission,)

    def get_queryset(self):
        user = self.request.telegram_user
        base_q = Q(
            all_event=True,
            date_from__date=timezone.localdate(),
            calendar=user.calendar,
        )
        if user.show_star_events:
            base_q |= Q(star=True)
        if user.show_slash_events:
            base_q |= Q(slash=True)
        return (
            Event.objects.filter(
                base_q,
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
        parse_ics(cal=self.request.telegram_user.calendar)
        queryset = self.get_queryset()
        serializer = EventShowSerializer(queryset, many=True)
        return Response(
            {
                "meetings": serializer.data,
            },
            status=status.HTTP_200_OK,
        )
