import disnake
from disnake import Intents
from disnake.ext.commands import Bot

from loguru import logger

from pytkb5 import config


bot = Bot(command_prefix="!",
    intents=Intents.all(),
)


@bot.event
async def on_ready():
    logger.success("Bot started!")


@bot.command(description="Responds pong!")
async def ping(
    inter: disnake.ApplicationCommandInteraction
) -> None:
    await inter.send("pong!")


async def start_bot():
    await bot.start(config.BOT_TOKEN)