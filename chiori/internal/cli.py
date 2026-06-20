"""Главный файл бота.

Отвечает за запуск клиента и подключение подсистем.
Подгружает настройки из файла.
настраивает все компоненты для работы.
Динамически подгружает плагины из директории.
"""

import asyncio
import logging
import sys

import hikari
import miru
from loguru import logger

from chiori.api.tags import TagsTable, not_tags
from chiori.client import ChioClient
from chiori.internal.errors import client_error_handler
from chiori.internal.settings import BotConfig

# Настраиваем формат отображения логов loguru
# Обратите внимание что в проекте помимо loguru используется logging
_LOG_FORMAT = (
    "<lvl>{level.icon}</> "
    "<light-black>{time:YYYY-MM-DD HH:mm:ss.SSS}</> "
    "{file}:{function} "
    "<lvl>{message}</>"
)


def _setup_logger(config: BotConfig) -> None:
    if config.HIKARI_DEBUG:
        root = logging.getLogger()
        root.setLevel(logging.DEBUG)

    logger.remove()
    logger.add(
        sys.stdout,
        format=_LOG_FORMAT,
        enqueue=True,
        level="DEBUG" if config.DEBUG else "INFO",
    )


def _check_folders(config: BotConfig) -> None:
    logger.info("Check needed chiori directories")
    config.EXTENSIONS_PATH.mkdir(exist_ok=True)
    config.DATA_PATH.mkdir(exist_ok=True)
    config.CONFIG_PATH.mkdir(exist_ok=True)


def run_bot() -> None:
    """Запуска бота.

    Создаёт новый клиент и запускает его подсистемы.
    Динамически загружает настройки и расширения.
    Производит подключение к базе данных.
    Запускает обработку событий.
    """
    logger.info("[1] Init client")
    config = BotConfig()  # pyright: ignore[reportCallIssue]
    bot = hikari.GatewayBot(token=config.BOT_TOKEN, intents=hikari.Intents.ALL)

    client = ChioClient(bot, config)
    miru.Client.from_arc(client)
    client.set_error_handler(client_error_handler)

    logger.info("[2] Setup Chio")
    _setup_logger(config)
    _check_folders(config)

    client.db.register(TagsTable)
    client.add_hook(not_tags("chio/banned"))

    logger.info("[3] Load plugins from {}", config.EXTENSIONS_PATH)
    client.load_extensions_from(config.EXTENSIONS_PATH)

    logger.info("[4] Start chiori client")

    try:
        asyncio.run(client.start())
    except Exception as e:
        logger.error("Error start client")
        logger.exception(e)
        sys.exit(1)

    activity = hikari.Activity(name="/chio v0.11", type=hikari.ActivityType.PLAYING)
    bot.run(activity=activity, asyncio_debug=config.HIKARI_DEBUG)
