from django.db.models import Q
from rest_framework.decorators import action
from rest_framework.viewsets import GenericViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from event.models import Event
from event.utils import parse_ics
from event.serializers import EventShowSerializer


class EventShowView(GenericViewSet):
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        user = self.request.user
        base_q = Q(all_event=True)
        if user.show_star_events:
            base_q |= Q(star=True)
        if user.show_slash_events:
            base_q |= Q(slash=True)
        return Event.objects.filter(base_q).order_by("date_from")

    @action(
        methods=["GET"],
        url_path="events",
        detail=False,
    )
    def show_events(self, request):
        parse_ics()
        queryset = self.get_queryset()
        serializer = EventShowSerializer(queryset, many=True)
        return Response(
            {
                "meetings": serializer.data,
            },
            status=status.HTTP_200_OK,
        )
