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
from chiori.log import logger

_CONFIG_PATH = Path("chio.toml")
"""Путь к основным настройкам Chiori."""


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
                "chio_docs": meta.__docs__,
            },
        )

    config.path.EXTENSIONS_PATH.mkdir(exist_ok=True)
    config.path.DATA_PATH.mkdir(exist_ok=True)
    config.path.CONFIG_PATH.mkdir(exist_ok=True)

    if config.DEBUG:
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

    logger.info("Prepare Chiori client")
    client.config.load(config.path.CONFIG_PATH)
    client.emoji.load()
    client.service.load()

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

    logger.setLevel(logging.DEBUG if config.DEBUG else logging.INFO)

    if config.DEBUG:
        logger.warning("Enabled debug mode")
        logger.warning("- Logger level set to DEBUG")
        logger.warning("- Default enabled guilds set to MAIN + ADMIN")
        logger.info("Please disable debug mode in production")

    if not config.SYNC_COMMANDS:
        logger.warning("Sync commands disabled")
        logger.info("Use /ext sync to manually sync commands with discord")

    if not config.CREATE_MODELS:
        logger.warning("Create models disabled")
        logger.info("Please create models again if you change/update extensions")

    run_bot(args, config)
