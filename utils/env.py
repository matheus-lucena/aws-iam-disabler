import os

from dotenv import load_dotenv
load_dotenv()

DISABLE_ACCESS_KEY_DAYS = int(os.getenv('DISABLE_ACCESS_KEY_DAYS', 60))
