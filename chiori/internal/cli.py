"""Главный файл бота.

Отвечает за запуск клиента и подключение подсистем.
Подгружает настройки из файла.
настраивает все компоненты для запуска.
Динамически подгружает расширений, настройки, базу данных.
"""

import argparse
import logging
from pathlib import Path

import hikari

from chiori import meta
from chiori.client import ChioClient
from chiori.internal.config import ChioConfig, load_config
from chiori.internal.errors import setup_errors

# Настраиваем формат отображения логов loguru
# Обратите внимание что в проекте помимо loguru используется logging
_LOG_FORMAT = (
    "<lvl>{level.icon}</> "
    "<light-black>{time:YYYY-MM-DD HH:mm:ss.SSS}</> "
    "{file}:{function} "
    "<lvl>{message}</>"
)

_CONFIG_PATH = Path("chio.toml")
"""Путь к основным настройкам Chiori."""


# TODO: Выглядит как костыль
async def _on_start(client: ChioClient) -> None:
    await client.start()


async def _on_shutdown(client: ChioClient) -> None:
    await client.stop()


def run_bot(args: argparse.Namespace, config: ChioConfig) -> None:
    """Запуска бота.

    Создаёт новый клиент и запускает его подсистемы.
    Динамически загружает настройки и расширения.
    Производит подключение к базе данных.
    Запускает обработку событий.
    """
    bot = hikari.GatewayBot(
        banner=None,
        token=config.BOT_TOKEN,
        intents=hikari.Intents.ALL,
        logs="DEBUG" if config.HIKARI_DEBUG else "INFO",
    )

    if not args.no_banner:
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

    config.path.EXTENSIONS_PATH.mkdir(exist_ok=True)
    config.path.DATA_PATH.mkdir(exist_ok=True)
    config.path.CONFIG_PATH.mkdir(exist_ok=True)

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
        bot,
        config,
        autosync=config.SYNC_COMMANDS,
        default_enabled_guilds=enabled_guilds,
    )
    setup_errors(client)

    logger.info("Load plugins from %s/", config.path.EXTENSIONS_PATH)
    client.load_extensions_from(config.path.EXTENSIONS_PATH)

    logger.info("Start Chiori client")
    client.config.load(config.path.CONFIG_PATH)
    client.emoji.load()
    client.add_startup_hook(_on_start)
    client.add_shutdown_hook(_on_shutdown)

    bot.run(
        activity=config.custom.activity.activity,
        asyncio_debug=config.HIKARI_DEBUG,
        check_for_updates=False,
        status=config.custom.status,
    )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="chiori", description="Chiori is modular discord bot core."
    )

    parser.add_argument(
        "--config",
        "-c",
        help="Path to chiori config file (chio.toml)",
        type=Path,
        default=_CONFIG_PATH,
        metavar="path",
    )
    parser.add_argument(
        "--no-banner",
        action="store_true",
        help="Don`t print banner on start",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable Chiori debug mode",
    )
    parser.add_argument(
        "--hikari-debug",
        action="store_true",
        help="Enable hikari and asyncio debug mode",
    )
    parser.add_argument(
        "--sync-commands",
        action="store_true",
        help="Sync slash commands on start client",
    )
    parser.add_argument(
        "--create-models",
        action="store_true",
        help="Create models after connect to Chiori DB",
    )
    parser.add_argument(
        "--ext-path",
        "-e",
        help="Path to load extensions",
        type=Path,
        default=None,
        metavar="path",
    )
    return parser


def _config_overrides(config: ChioConfig, args: argparse.Namespace) -> None:
    if args.debug:
        config.DEBUG = True

    if args.hikari_debug:
        config.HIKARI_DEBUG = True

    if args.create_models:
        config.CREATE_MODELS = True

    if args.sync_commands:
        config.SYNC_COMMANDS = True

    if e := args.ext_path:
        config.path.EXTENSIONS_PATH = e


def cli() -> None:
    """Интерфейс командной строки для управления Шиори.

    Предоставляет гибкие параметры для запуска.
    """
    parser = _parser()
    args = parser.parse_args()

    config = load_config(args.config)
    _config_overrides(config, args)

    run_bot(args, config)
