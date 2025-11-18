from django.contrib.auth.models import AnonymousUser
from users.models import User

EXEMPT_PATHS = ["/admin"]


class TelegramIDMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        telegram_id = request.headers.get("telegram-id")
        print(request.headers)

        if any(request.path.startswith(p) for p in EXEMPT_PATHS):
            return self.get_response(request)

        if not telegram_id:
            request.user = AnonymousUser()
            return self.get_response(request)
        try:
            user = User.objects.get(telegram_id=telegram_id)
            request.telegram_user = user
        except User.DoesNotExist:
            request.telegram_user = AnonymousUser()
        return self.get_response(request)
