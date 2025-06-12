import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
DEFAULT_FIELD_SIZE = int(os.getenv("DEFAULT_FIELD_SIZE", 4))