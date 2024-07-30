"""Ядро бота ChioriCord.

Главный файл ядра.
настраивает все компоненты для бота.
Динамически подгружает плагины.
"""

import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
import traceback

import arc
import hikari
import miru
from loguru import logger

from chioricord import config

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

# Директория откудла будут грузиться все расширения
EXT_PATH = Path("exstensions/")
BOT_DATA_PATH = Path("bot_data/")
bot = hikari.GatewayBot(token=config.BOT_TOKEN)
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
    embed = hikari.Embed(
        title="Что-то пошло не так!",
        description="Во время выполнения команды возникло исключение",
        color=hikari.colors.Color(0xff00bb),
        timestamp=datetime.now(tz=ZoneInfo("Europe/Samara"))
    )
    await ctx.respond(embed=embed)

    # Ну и отправляем в логи, чтобы было с чем работать
    logger.error(str(ctx))
    logger.exception(exc)
    traceback.print_exception(exc)


# if isinstance(error, commands.errors.MissingPermissions):
#     await ctx.send(embed=discord.Embed(
#         title="❌ **Ошибка**",
#         description=(
#             f"**{ctx.author}**, у вас недостаточно прав для использования"
#             "данной команды."
#          ),
#         color=0xff2b20
#     ))


# Обработка команд
# ================

# @bot.command()
# async def unraid(ctx: commands.Context):
#     logger.info("Start unraid")
#     for channel in ctx.guild.channels:
#         if channel.name == "переезд":
#             await channel.delete()
#     logger.info("End unraid")
#     await ctx.send("Unraid complete")


# @bot.hybrid_group()
# async def system(ctx: commands.Context):
#     ext = bot.extensions()
#     await ctx.send("Это системные команды")

# @system.command()
# async def load(ctx: commands.Context, extension: str):
#     bot.load_extension(extension)
#     await ctx.send(f"Модуль **{extension}** подключен...", delete_after=30)

# @system.command()
# async def unload(ctx: commands.Context, extension: str):
#     bot.unload_extension(extension)
#     await ctx.send(f"Модуль **{extension}** выключен...", delete_after=30)

# @system.command()
# async def reload(ctx: commands.Context, extension: str):
#     bot.reload_extension(extension)
#     await ctx.send(f"Модуль **{extension}** перезагружен..", delete_after=30)


# Запуск бота
# ===========

def start_bot():
    """Функция для запуска бота.

    Устанавливает логгирование.
    Подгружает все плагины.
    Запускаеет самого бота.
    """
    # Настройка логгеров
    logger.remove()
    logger.add(
        sys.stdout,
        format=LOG_FORMAT
    )

    logger.info("Check data folder {}", BOT_DATA_PATH)
    BOT_DATA_PATH.mkdir(exist_ok=True)


    # Простой загрузчик расширений
    logger.info("Load plugins from {}", EXT_PATH)
    dp.load_extensions_from(EXT_PATH)

    # Устанавливаем активность бота
    # "prefix для получение справки"
    activity = hikari.presences.Activity(
        name=f"для справки /help",
        type=hikari.presences.ActivityType.PLAYING
    )

    # Запускаем бота
    bot.run(activity=activity)
