from dotenv import load_dotenv

load_dotenv()

NAME_MAX_LENGTH = 255
CODE_MAX_LENGTH = 4
CODE_EXPIRATION_TIME = 5
ALLOWED_EMAIL = ("@ylab.team", "@ylab.io")
CALENDAR_KEY = "b2e59b301592d6a16043453b8257fd6e5a1cff89&tz_id=Europe/Moscow"
# CALENDAR_KEY = os.getenv("CALENDAR_KEY")
CHAT_ID = "-1003577506308"
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
