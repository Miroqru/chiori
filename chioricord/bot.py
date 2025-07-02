"""Ядро бота ChioriCord.

Главный файл ядра.
настраивает все компоненты для бота.
Динамически подгружает плагины.
"""

import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import arc
import hikari
import miru
from loguru import logger

from chioricord.config import PluginConfigManager, config
from chioricord.db import ChioDatabase

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
    try:
        raise exc
    except Exception as e:
        embed = hikari.Embed(
            title="Что-то пошло не так!",
            description="Во время выполнения команды возникло исключение",
            color=hikari.Color(0xFF00BB),
            timestamp=datetime.now(tz=ZoneInfo("Europe/Samara")),
        )
        embed.add_field("Тип", str(type(e)))
        embed.add_field("Исключение", str(e))
        await ctx.respond(embed=embed)
        logger.exception(e)


@dp.add_hook
async def on_command(ctx: arc.GatewayContext) -> None:
    """Простой журнал вызовы команд."""
    logger.debug(
        "Use {} in {} by {}", ctx.command.name, ctx.guild_id, ctx.user.id
    )


@dp.add_startup_hook
@dp.inject_dependencies
async def on_startup(
    client: arc.GatewayClient, db: ChioDatabase = arc.inject()
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


# if isinstance(error, commands.errors.MissingPermissions):
#     await ctx.send(embed=discord.Embed(
#         title="❌ **Ошибка**",
#         description=(
#             f"**{ctx.author}**, у вас недостаточно прав для использования"
#             "данной команды."
#          ),
#         color=0xff2b20
#     ))

# Запуск бота
# ===========


def start_bot() -> None:
    """Функция для запуска бота.

    Устанавливает запись логов.
    Подгружает все плагины.
    Запускает самого бота.
    """
    logger.remove()
    logger.add(sys.stdout, format=LOG_FORMAT)

    logger.info("Check data folder {}", BOT_DATA_PATH)
    BOT_DATA_PATH.mkdir(exist_ok=True)

    logger.info("Setup config and database")
    cm = PluginConfigManager(config.PLUGINS_CONFIG, dp)
    db = ChioDatabase(str(config.DB_DSN), dp)

    dp.set_type_dependency(PluginConfigManager, cm)
    dp.set_type_dependency(ChioDatabase, db)

    # Простой загрузчик расширений
    logger.info("Load plugins from {} ...", EXT_PATH)
    dp.load_extensions_from(EXT_PATH)

    activity = hikari.Activity(
        name="для справки /help", type=hikari.ActivityType.STREAMING
    )
    bot.run(activity=activity)
