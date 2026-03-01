from enum import IntEnum, StrEnum


class ErrorCodes(IntEnum):
    EMAIL_EXISTS = 1001
    WRONG_DOMAIN = 1002
    CODE_NOT_EXPIRED = 1003
    ID_DONT_EXIST = 1004
    WRONG_CODE = 1005
    CODE_EXPIRED = 1006
    HAVE_ACTIVATED_USER = 1007


class MessageEnums(StrEnum):
    title = "- изменено название мероприятия"
    description = "- измненено описание мероприятия"
    url_calendar = "- изменена ссылка на календарь"
    date_from = "Перенос встречи "
    date_till = "- изменено время завершения проведения мероприятия на"
    deleted = "Отмена встречи"


class StatusEnums(StrEnum):
    CREATED = "created"
    UPDATED = "updated"
    DELETED = "deleted"
    NO_STATUS = ""


class TypeReceiverEnums(StrEnum):
    USER = "user"
    GROUP_CHAT = "group_chat"
