import re
from pathlib import Path
import logging

import discord
from discord import Intents
from discord.ext import commands

from loguru import logger

from pytkb5 import config


bot = commands.Bot(
    command_prefix=commands.when_mentioned_or("c!"),
    intents=Intents.all(),
)


@bot.event
async def on_ready():
    logger.success("Bot started!")

@bot.command(description="Responds with 'World'")
async def hello(ctx: commands.Context):
    await ctx.send("Hello!")

async def start_bot():
    logging.basicConfig(level=logging.INFO)
    await bot.start(config.BOT_TOKEN)