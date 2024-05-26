from os import getenv

from dotenv import load_dotenv


load_dotenv()
BOT_TOKEN = getenv("BOT_TOKEN")

if BOT_TOKEN is None:
    raise TypeError("You need to set discord bot token")

BOT_PREFIX = getenv("BOT_PREFIX", "c!")
