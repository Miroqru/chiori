"""Класс хранит корневые настройки бота.

Author: Milinuri Nirvalen
"""

from os import getenv

from dotenv import load_dotenv
from loguru import logger

load_dotenv()
BOT_TOKEN = getenv("BOT_TOKEN")

if BOT_TOKEN is None:
    raise TypeError("You need to set discord bot token")

BOT_PREFIX = getenv("BOT_PREFIX", "c!")
BOT_OWNER = getenv("BOT_OWNER")

if BOT_OWNER is None:
    logger.warning("Bot owner id is empty.")
    logger.warning("No one will be able to control the bot system")

