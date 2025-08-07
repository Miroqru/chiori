"""Ядро бота ChioriCord.

Главный файл ядра.
настраивает все компоненты для бота.
Динамически подгружает плагины.
"""

import asyncio
import sys

import hikari
import miru
from loguru import logger

from chioricord.api import BotConfig, RoleLevel, RoleTable
from chioricord.client import ChioClient
from chioricord.errors import client_error_handler
from chioricord.hooks import has_role

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

__all__ = ("start_bot",)


async def _connect_db(client: ChioClient) -> None:
    """Производим подключение к базе данных."""
    logger.info("Connect to chio database")
    await client.db.connect(str(client.bot_config.DB_DSN))
    await client.db.create_tables()


def _setup_logger(config: BotConfig) -> None:
    if config.DEBUG:
        # hikari_logger = logging.getLogger()
        # hikari_logger.setLevel(logging.DEBUG)
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


def _setup_db(client: ChioClient) -> None:
    client.db.register(RoleTable)
    client.add_hook(has_role(RoleLevel.USER))
    client.add_startup_hook(_connect_db)


def start_bot() -> None:
    """Функция для запуска бота.

    Устанавливает запись логов.
    Проверяет наличие необходимых директорий.
    Подгружает все плагины.
    Запускает самого бота.
    """
    logger.info("[1] Init client")
    config = BotConfig()  # type: ignore
    bot = hikari.GatewayBot(token=config.BOT_TOKEN, intents=hikari.Intents.ALL)
    client = ChioClient(bot, config)
    miru.Client.from_arc(client)

    client.set_type_dependency(BotConfig, config)
    client.set_error_handler(client_error_handler)

    logger.info("[2] Setup Chio")
    _setup_logger(config)
    _check_folders(config)
    _setup_db(client)

    logger.info("[3] Load plugins from {}", config.EXTENSIONS_PATH)
    client.load_extensions_from(config.EXTENSIONS_PATH)

    logger.info("[4] Load plugin configs")
    try:
        client.config.load(config.CONFIG_PATH)
    except ValueError as e:
        logger.error(e)
        sys.exit(1)

    logger.info("[5] Start bot")
    activity = hikari.Activity(name="/help", type=hikari.ActivityType.PLAYING)
    bot.run(activity=activity)
