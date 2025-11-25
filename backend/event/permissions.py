from django.contrib.auth.models import AnonymousUser
from rest_framework.permissions import BasePermission


class TelegramUserPermission(BasePermission):
    def has_permission(self, request, view):
        return request.telegram_user != AnonymousUser()
