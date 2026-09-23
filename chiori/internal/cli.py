"""Главный файл бота.

Отвечает за запуск клиента и подключение подсистем.
Подгружает настройки из файла.
настраивает все компоненты для запуска.
Динамически подгружает расширений, настройки, базу данных.
"""

import logging

import hikari

from chiori import meta
from chiori.api.custom import Custom
from chiori.client import ChioClient
from chiori.internal.config import load_config
from chiori.internal.errors import client_error_handler, forbid_message

# Настраиваем формат отображения логов loguru
# Обратите внимание что в проекте помимо loguru используется logging
_LOG_FORMAT = (
    "<lvl>{level.icon}</> "
    "<light-black>{time:YYYY-MM-DD HH:mm:ss.SSS}</> "
    "{file}:{function} "
    "<lvl>{message}</>"
)


# TODO: Выглядит как костыль
async def _on_start(client: ChioClient) -> None:
    await client.start()


async def _on_shutdown(client: ChioClient) -> None:
    await client.stop()


def run_bot() -> None:
    """Запуска бота.

    Создаёт новый клиент и запускает его подсистемы.
    Динамически загружает настройки и расширения.
    Производит подключение к базе данных.
    Запускает обработку событий.
    """
    config = load_config()
    bot = hikari.GatewayBot(
        banner=None,
        token=config.BOT_TOKEN,
        intents=hikari.Intents.ALL,
        logs="DEBUG" if config.HIKARI_DEBUG else "INFO",
    )
    bot.print_banner(
        "chiori",
        allow_color=True,
        force_color=False,
        extra_args={
            "chio_version": meta.__version__,
            "chio_copyright": meta.__copyright__,
            "chio_license": meta.__license__,
            "chio_discord": meta.__discord_invite__,
            "chio_docementation": meta.__docs__,
        },
    )

    config.EXTENSIONS_PATH.mkdir(exist_ok=True)
    config.DATA_PATH.mkdir(exist_ok=True)
    config.CONFIG_PATH.mkdir(exist_ok=True)

    # Это от части костыль
    logger = logging.getLogger("chiori")
    logger.setLevel(logging.DEBUG if config.DEBUG else logging.INFO)

    if config.DEBUG:
        logger.warning("Enabled debug mode")
        logger.warning("- Auto sync disabled, use /ext sync instead")
        logger.warning("- Default enabled guilds set to MAIN + ADMIN")
        logger.warning("Please disable debug mode in production")
        enabled_guilds = [config.MAIN_GUILD, config.ADMIN_GUILD]
    else:
        enabled_guilds = hikari.UNDEFINED

    client = ChioClient(
        bot, config, autosync=not config.DEBUG, default_enabled_guilds=enabled_guilds
    )
    client.set_error_handler(client_error_handler)
    client.register_error(hikari.ForbiddenError, forbid_message)

    client.config.register(Custom)
    logger.info("Load plugins from %s/", config.EXTENSIONS_PATH)
    client.load_extensions_from(config.EXTENSIONS_PATH)

    logger.info("Start Chiori client")
    client.config.load(client.bot_config.CONFIG_PATH)
    client.emoji.load()
    client.add_startup_hook(_on_start)
    client.add_shutdown_hook(_on_shutdown)

    custom = client.get_type_dependency(Custom)
    bot.run(activity=custom.activity.activity, asyncio_debug=config.HIKARI_DEBUG)
