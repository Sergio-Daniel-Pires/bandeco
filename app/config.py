import os

import dotenv

dotenv.load_dotenv()

# Redis config
REDIS_CONN = os.environ["REDIS_CONN"]
REDIS_PASSWORD = os.environ["REDIS_PASSWORD"]

# Gunicorn config
GUNICORN_BIND = os.environ.get("GUNICORN_BIND", "0.0.0.0:3579")
GUNICORN_WORKERS = os.environ.get("GUNICORN_WORKERS", "4")
GUNICORN_TIMEOUT = os.environ.get("GUNICORN_TIMEOUT", "180")

# Whatsapp config
WHATSAPP_BOT_NUMBER = os.environ["WHATSAPP_BOT_NUMBER"]
WHATSAPP_API_TOKEN = os.environ["WHATSAPP_API_TOKEN"]
WHATSAPP_VERIFY_TOKEN = os.environ["WHATSAPP_VERIFY_TOKEN"]
WHATSAPP_GATEWAY_TOKEN = os.environ["WHATSAPP_GATEWAY_TOKEN"]
