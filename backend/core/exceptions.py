class BaseServiceError(Exception):
    """Base service error."""

    def __init__(self, *, message: str = None, **context) -> None:
        self.message = self.__doc__ or message
        self.context = context


class NotWorkingParseEvent(BaseServiceError):
    """Не удалось начать парсинг календаря."""


class NotFoundEvent(BaseServiceError):
    """Не удалось найти событие для отправки сообщения."""


class NoReceiver(BaseServiceError):
    """Не удалось найти получателя сообщения в БД"""
