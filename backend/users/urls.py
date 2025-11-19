from django.urls import path, include
from rest_framework.routers import DefaultRouter

from users.views import EmailCheckViewSet

router_v1 = DefaultRouter()
router_v1.register("", EmailCheckViewSet, basename="register")


urlpatterns = [
    path("", include(router_v1.urls)),
]
