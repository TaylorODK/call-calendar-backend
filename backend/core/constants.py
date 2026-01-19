import os
from dotenv import load_dotenv

load_dotenv()

NAME_MAX_LENGTH = 255
CODE_MAX_LENGTH = 4
CODE_EXPIRATION_TIME = 5
ALLOWED_EMAIL = ("@ylab.team", "@ylab.io")
KEY = os.getenv("KEY")
CHAT_ID = os.getenv("CHAT_ID")
