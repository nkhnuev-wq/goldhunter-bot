import os

BOT_TOKEN = os.getenv("BOT_TOKEN")

ADMIN_ID = os.getenv("ADMIN_ID")

if ADMIN_ID is None:
    raise ValueError("ADMIN_ID is not set in environment variables")

ADMIN_ID = int(ADMIN_ID)