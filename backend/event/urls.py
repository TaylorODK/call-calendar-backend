from django.urls import path, include
from rest_framework.routers import DefaultRouter

from event.views import EventShowView

router_v1 = DefaultRouter()
router_v1.register("", EventShowView, basename="event")


urlpatterns = [
    path("", include(router_v1.urls)),
]
