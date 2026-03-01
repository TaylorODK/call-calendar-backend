from django.contrib.auth.models import AnonymousUser
from rest_framework.permissions import BasePermission


class TelegramUserPermission(BasePermission):
    def has_permission(self, request, view):
        telegram_user = getattr(request._request, "telegram_user", None)
        if telegram_user is None:
            return False
        return telegram_user != AnonymousUser()
