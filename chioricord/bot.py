"""Ядро бота ChioriCord.

Главный файл ядра.
настраивает все компоненты для бота.
Динамически подгружает плагины.
"""

import asyncio
import logging
import sys
from datetime import UTC, datetime
from pathlib import Path

import arc
import hikari
import miru
from loguru import logger

from chioricord.config import PluginConfigManager, config
from chioricord.db import ChioDB
from chioricord.hooks import has_role
from chioricord.roles import RoleLevel, RoleTable

try:
    import uvloop

    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
except ModuleNotFoundError:
    asyncio.set_event_loop_policy(asyncio.DefaultEventLoopPolicy())


# Глобальные переменные
# =====================

# Настраиваем формат отображения логов loguru
# Обратите внимание что в проекте помимо loguru используется logging
LOG_FORMAT = (
    "<lvl>{level.icon}</> "
    "<light-black>{time:YYYY-MM-DD HH:mm:ss.SSS}</> "
    "{file}:{function} "
    "<lvl>{message}</>"
)

# Директория откуда будут грузиться все расширения
EXT_PATH = Path("extensions/")
BOT_DATA_PATH = Path("bot_data/")
bot = hikari.GatewayBot(token=config.BOT_TOKEN, intents=hikari.Intents.ALL)
dp = arc.GatewayClient(bot)
miru_client = miru.Client.from_arc(dp)


# Обработка событий
# =================


@dp.set_error_handler
async def client_error_handler(ctx: arc.GatewayContext, exc: Exception) -> None:
    """Отлавливаем исключение если что-то  пошло не по плану.

    К примеру это могут быть ошибки внутри обработчиков.
    Неправильно переданные команды.
    Если обработчики сами не реализуют обработчики ошибок, то все
    исключения будут попадать сюда.
    """
    if isinstance(exc, hikari.ForbiddenError):
        emb = hikari.Embed(
            title="⚠️ Недостаточно прав",
            description="Для выполнения данной команды.",
            color=hikari.Color(0xFF9966),
        )
        emb.add_field("status", f"[`{exc.status}`] {exc.message}")
        return

    try:
        raise exc
    except Exception as e:
        logger.exception(e)
        emb = hikari.Embed(
            title="⚡ Что-то пошло не так!",
            description=(
                "Во время выполнения команды..\n\n"
                f"`{type(e)}`: {e}\n\n"
                "🌱 Обратитесь в поддержку за помощью."
            ),
            color=hikari.Color(0xFF6699),
            timestamp=datetime.now(UTC),
        )
        await ctx.respond(emb)


@dp.add_startup_hook
@dp.inject_dependencies
async def on_startup(
    client: arc.GatewayClient, db: ChioDB = arc.inject()
) -> None:
    """Производим подключение к базе данных."""
    await db.connect()
    await db.create_tables()


@dp.add_shutdown_hook
@dp.inject_dependencies
async def shutdown_client(
    client: arc.GatewayClient, cm: PluginConfigManager = arc.inject()
) -> None:
    """Действия для корректного завершения работы бота."""
    logger.info("Shutdown chiori")
    # TODO: Пока не совсем ясно как стоит сохранять настройки
    # cm.dump_config()


# Запуск бота
# ===========


def start_bot() -> None:
    """Функция для запуска бота.

    Устанавливает запись логов.
    Подгружает все плагины.
    Запускает самого бота.
    """
    hikari_logger = logging.getLogger()
    hikari_logger.setLevel(logging.DEBUG)

    logger.remove()
    logger.add(
        sys.stdout, format=LOG_FORMAT, enqueue=True, level=config.LOG_LEVEL
    )

    logger.info("Check data folder {}", BOT_DATA_PATH)
    BOT_DATA_PATH.mkdir(exist_ok=True)

    logger.info("Setup config and database")
    cm = PluginConfigManager(config.PLUGINS_CONFIG, dp)
    db = ChioDB(str(config.DB_DSN), dp)
    db.register(RoleTable)
    dp.add_hook(has_role(RoleLevel.USER))

    dp.set_type_dependency(PluginConfigManager, cm)
    dp.set_type_dependency(ChioDB, db)

    # Простой загрузчик расширений
    logger.info("Load plugins from {} ...", EXT_PATH)
    dp.load_extensions_from(EXT_PATH)

    activity = hikari.Activity(
        name="для справки /help", type=hikari.ActivityType.STREAMING
    )
    bot.run(activity=activity)
