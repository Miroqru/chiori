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
    config = client.get_type_dependency(BotConfig)
    await db.connect(str(config.DB_DSN))
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
    db = ChioDB(client)
    db.register(RoleTable)
    client.set_type_dependency(ChioDB, db)
    client.add_hook(has_role(RoleLevel.USER))
    client.add_startup_hook(_connect_db)


def start_bot() -> None:
    """Функция для запуска бота.

    Устанавливает запись логов.
    Проверяет наличие необходимых директорий.
    Подгружает все плагины.
    Запускает самого бота.
    """
    logger.info("[0] Load bot config")
    config = BotConfig()  # type: ignore

    logger.info("[1] Init client")
    bot = hikari.GatewayBot(token=config.BOT_TOKEN, intents=hikari.Intents.ALL)
    client = arc.GatewayClient(bot)
    miru.Client.from_arc(client)

    client.set_type_dependency(BotConfig, config)
    client.set_error_handler(client_error_handler)

    logger.info("[2] Setup Chio")
    _setup_logger(config)
    _check_folders(config)

    logger.info("[3] Setup ChioDB")
    _setup_db(client, config)

    logger.info("[4] Setup PluginConfig")
    cm = PluginConfigManager(client)
    client.set_type_dependency(PluginConfigManager, cm)

    logger.info("[5] Load plugins from {}", config.EXTENSIONS_PATH)
    client.load_extensions_from(config.EXTENSIONS_PATH)

    logger.info("[6] Load plugin configs")
    cm.load(config.CONFIG_PATH)

    logger.info("[7] Start bot")
    activity = hikari.Activity(name="/help", type=hikari.ActivityType.PLAYING)
    bot.run(activity=activity)
