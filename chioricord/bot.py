"""Ядро бота ChioriCord.

Главный файл ядра.
настраивает все компоненты для бота.
Динамически подгружает плагины.
"""

import asyncio
import logging
import sys

import arc
import hikari
import miru
from loguru import logger

from chioricord.config import BotConfig, PluginConfigManager
from chioricord.db import ChioDB
from chioricord.errors import client_error_handler
from chioricord.hooks import has_role
from chioricord.roles import RoleLevel, RoleTable

try:
    import uvloop

    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
except ModuleNotFoundError:
    asyncio.set_event_loop_policy(asyncio.DefaultEventLoopPolicy())


# Настраиваем формат отображения логов loguru
# Обратите внимание что в проекте помимо loguru используется logging
_LOG_FORMAT = (
    "<lvl>{level.icon}</> "
    "<light-black>{time:YYYY-MM-DD HH:mm:ss.SSS}</> "
    "{file}:{function} "
    "<lvl>{message}</>"
)


async def _connect_db(client: arc.GatewayClient) -> None:
    """Производим подключение к базе данных."""
    logger.info("Connect to chio database")
    db = client.get_type_dependency(ChioDB)
    await db.connect()
    await db.create_tables()


def _setup_logger(config: BotConfig) -> None:
    if config.DEBUG:
        hikari_logger = logging.getLogger()
        hikari_logger.setLevel(logging.DEBUG)
        level = "DEBUG"
    else:
        level = "INFO"

    logger.remove()
    logger.add(sys.stdout, format=_LOG_FORMAT, enqueue=True, level=level)


def _check_folders(config: BotConfig) -> None:
    logger.info("Check needed bot folders")
    config.EXTENSIONS_PATH.mkdir(exist_ok=True)
    config.DATA_PATH.mkdir(exist_ok=True)
    config.CONFIG_PATH.mkdir(exist_ok=True)


def _setup_db(client: arc.GatewayClient, config: BotConfig) -> None:
    logger.info("Setup config and database")
    cm = PluginConfigManager(config.CONFIG_PATH, client)
    cm.load()

    db = ChioDB(str(config.DB_DSN), client)
    db.register(RoleTable)

    # Установка DI
    client.set_type_dependency(PluginConfigManager, cm)
    client.set_type_dependency(ChioDB, db)

    # Настройка хуков
    client.add_hook(has_role(RoleLevel.USER))
    client.add_startup_hook(_connect_db)


def start_bot() -> None:
    """Функция для запуска бота.

    Устанавливает запись логов.
    Проверяет наличие необходимых директорий.
    Подгружает все плагины.
    Запускает самого бота.
    """
    logger.info("Load bot config")
    config = BotConfig()  # type: ignore

    bot = hikari.GatewayBot(token=config.BOT_TOKEN, intents=hikari.Intents.ALL)
    client = arc.GatewayClient(bot)
    miru.Client.from_arc(client)

    client.set_type_dependency(BotConfig, config)
    client.set_error_handler(client_error_handler)

    _setup_logger(config)
    _check_folders(config)
    _setup_db(client, config)

    # Простой загрузчик расширений
    logger.info("Load plugins from {} ...", config.EXTENSIONS_PATH)
    client.load_extensions_from(config.EXTENSIONS_PATH)

    # Запуск бота
    activity = hikari.Activity(name="/help", type=hikari.ActivityType.PLAYING)
    bot.run(activity=activity)
