import os
from dotenv import load_dotenv

load_dotenv()

NAME_MAX_LENGTH = 255
CODE_MAX_LENGTH = 4
CODE_EXPIRATION_TIME = 1
DATE_FORMAT_FOR_ALERTS = "%H:%M %d.%m.%Y"
ALLOWED_EMAIL = os.getenv("ALLOWED_EMAIL", "mail.ru").split(",")
CALENDAR_KEY = os.getenv("CALENDAR_KEY")
ALERT_TIME_BEFORE_EVENT = 10
PARSIN_AHEAD_DAYS = 5
CHAT_ID = os.getenv("CHAT_ID")
PARSE_URL = "https://calendar.yandex.ru/export/ics.xml?private_token="
BYDAY_MAP = {
    0: "MO",
    1: "TU",
    2: "WE",
    3: "TH",
    4: "FR",
    5: "SA",
    6: "SU",
}
