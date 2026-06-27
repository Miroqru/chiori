"""Главный файл бота.

Отвечает за запуск клиента и подключение подсистем.
Подгружает настройки из файла.
настраивает все компоненты для запуска.
Динамически подгружает расширений, настройки, базу данных.
"""

import logging
import sys

import hikari
import miru
from loguru import logger

from chiori.api.custom import Custom
from chiori.api.tags import TagsTable, not_tags
from chiori.client import ChioClient
from chiori.internal.config import ChioConfig
from chiori.internal.errors import client_error_handler

# Настраиваем формат отображения логов loguru
# Обратите внимание что в проекте помимо loguru используется logging
_LOG_FORMAT = (
    "<lvl>{level.icon}</> "
    "<light-black>{time:YYYY-MM-DD HH:mm:ss.SSS}</> "
    "{file}:{function} "
    "<lvl>{message}</>"
)


def _setup_logger(config: ChioConfig) -> None:
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


def _check_folders(config: ChioConfig) -> None:
    logger.info("Check needed chiori directories")
    config.EXTENSIONS_PATH.mkdir(exist_ok=True)
    config.DATA_PATH.mkdir(exist_ok=True)
    config.CONFIG_PATH.mkdir(exist_ok=True)


# TODO: Выделить в Core расширение
async def on_start(client: ChioClient) -> None:
    """Запускает работа клиента.

    Это финальные метод, запускайте его после предварительной подготовки.
    """
    logger.info("Connect to database")
    await client.db.connect(str(client.bot_config.DB_DSN))
    await client.db.create_tables()


def run_bot() -> None:
    """Запуска бота.

    Создаёт новый клиент и запускает его подсистемы.
    Динамически загружает настройки и расширения.
    Производит подключение к базе данных.
    Запускает обработку событий.
    """
    logger.info("[1] Init client")
    # TODO: Move to config loader func
    config = ChioConfig()  # pyright: ignore[reportCallIssue]
    # TODO: Customize settings
    # TODO: Set logger level directly
    bot = hikari.GatewayBot(token=config.BOT_TOKEN, intents=hikari.Intents.ALL)

    client = ChioClient(bot, config)
    miru.Client.from_arc(client)
    client.set_error_handler(client_error_handler)

    logger.info("[2] Setup Chio")
    _setup_logger(config)
    _check_folders(config)

    client.db.register(TagsTable)
    client.config.register(Custom)
    client.add_hook(not_tags("chio/banned"))

    logger.info("[3] Load plugins from {}", config.EXTENSIONS_PATH)
    client.load_extensions_from(config.EXTENSIONS_PATH)

    logger.info("[4] Start chiori client")

    client.config.load(client.bot_config.CONFIG_PATH)
    client.emoji.load()
    client.add_startup_hook(on_start)

    custom = client.get_type_dependency(Custom)
    bot.run(activity=custom.activity.activity, asyncio_debug=config.HIKARI_DEBUG)
