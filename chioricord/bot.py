"""Ядро бота ChioriCord.

Используется для загрузки и запуска плагинов.

Author: Mulinuri Nirvalen
Verion: v0.3 (8)
"""

import sys
import logging
import re
from pathlib import Path

import hikari
import arc
from loguru import logger

from chioricord import config

# Глобальные переменные
# =====================

# Настраиваем формат отображения логов loguru
# Обратите внимание что в проекте помимо loguru используется logging
LOG_FORMAT = (
    "<lvl>{level.icon}</>"
    "<light-black>{time:YYYY-MM-DD HH:mm:ss.SSS}</>"
    "{file}:{function}"
    "<lvl>{message}</>"
)

# Директория откудла будут грузиться все расширения
EXT_PATH = Path("exstensions/")
bot = hikari.GatewayBot(token=config.BOT_TOKEN)
dp = arc.GatewayClient(bot)


# Обработка событий
# =================

# @bot.event
# async def on_command_error(
#     ctx: commands.Context,
#     error: commands.errors.CommandError
# ):
#     """Обработка исключений при выполении команд."""
#     logger.error("Error while process command: {}, {}", ctx, error)

#     if isinstance(error, commands.errors.CommandNotFound):
#         await ctx.send(embed=discord.Embed(
#             title="❌ **Ошибка**",
#             description=f"**{ctx.author}**, Я не знаю такой команды.",
#             color=0xff2b20
#         ))

#     if isinstance(error, commands.errors.MissingPermissions):
#         await ctx.send(embed=discord.Embed(
#             title="❌ **Ошибка**",
#             description=f"**{ctx.author}**, у вас недостаточно прав для использования данной команды.",
#             color=0xff2b20
#         ))


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

    # Простой загрузчик расширений
    _logger.info("Load plugins from {}", EXT_PATH)
    dp.load_extensions_from(EXT_PATH)

    # Устанавливаем активность бота
    # "prefix для получение справки"
    activity = hikari.presences.Activity(
        name=f"для справки {config.BOT_PREFIX}help",
        type=hikari.presences.ActivityType.PLAYING
    )

    # Запускаем бота
    bot.run(activity=activity)