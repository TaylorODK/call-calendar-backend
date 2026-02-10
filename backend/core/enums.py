from enum import IntEnum


class ErrorCodes(IntEnum):
    EMAIL_EXISTS = 1001
    WRONG_DOMAIN = 1002
    CODE_NOT_EXPIRED = 1003
    ID_DONT_EXIST = 1004
    WRONG_CODE = 1005
    CODE_EXPIRED = 1006
    HAVE_ACTIVATED_USER = 1007
