"""Ядро бота ChioriCord.

Используется для загрузки и запуска плагинов.

Author: Mulinuri Nirvalen
Verion: v0.3 (8)
"""

import logging
import re
from pathlib import Path

import hikari
from loguru import logger

from chioricord import config

# Глобальные переменные
# =====================

COGS_PATH = Path("cogs/")
bot = hikari.GatewayBot(token=config.BOT_TOKEN)


@bot.listen()
async def event_handler(event: hikari.GuildMessageCreateEvent) -> None:
    """Обрабатываем входящие события..."""
    logger.debug(event)

    # Отсеиваем сообщения от ботов / хуков
    if not event.is_human:
        return

    me = bot.get_me()
    if me.id in event.message.user_mentions_ids:
        await event.message.respond("Кусь!")



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
    logging.basicConfig(level=logging.INFO)

    # Простой загрузчик расширений
    # logger.info("Load cogs from {}", COGS_PATH)
    # for p in COGS_PATH.iterdir():
    #     if re.match(r"^[^_].*\.py$", p.name):
    #         await bot.load_extension(str(p).replace("/", ".")[:-3])
    #         logger.info("Loaded cog: {}", p)

    # await bot.start(config.BOT_TOKEN)

    # Устанавливаем активность бота
    # "prefix для получение справки"
    activity = hikari.presences.Activity(
        name=f"для справки {config.BOT_PREFIX}help",
        type=hikari.presences.ActivityType.PLAYING
    )

    # Запускаем бота
    bot.run(activity=activity)