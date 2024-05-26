import re
from pathlib import Path
import logging

import discord
from discord import Intents
from discord.ext import commands

from loguru import logger

from chioricord import config
from g4f.client import Client
import g4f.Provider.Aichatos


bot = commands.Bot(
    command_prefix=commands.when_mentioned_or(config.BOT_PREFIX),
    intents=Intents.all(),
)
gpt_client = Client()
COGS_PATH = Path("cogs/")

@bot.event
async def on_ready():
    logger.success("Bot started!")

    logger.info("Set bot rich presence")
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name=f"{config.BOT_PREFIX}help to get help"
        )
    )


@bot.command(description="Responds with 'World'")
async def hello(ctx: commands.Context):
    await ctx.send("Hello!")

@bot.command(description="Talk to ChatGPT")
async def gpt(ctx: commands.context, *, args: str | None):
    if args is None:
        return await ctx.send("Использовать c!gpt <запрос>.")

    response = gpt_client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content":"Твоя задача будет подробно отечать на русском языке"},
            {"role": "system", "content": args}
        ],
        provider=g4f.Provider.Aichatos
    )
    await ctx.send(response.choices[0].message.content)

async def start_bot():
    logging.basicConfig(level=logging.INFO)

    # Простой загрузчик расширений
    logger.info("Load cogs from {}", COGS_PATH)
    for p in COGS_PATH.iterdir():
        if re.match(r"^[^_].*\.py$", p.name):
            await bot.load_extension(str(p).replace("/", ".")[:-3])
            logger.info("Loaded cog: {}", p)

    await bot.start(config.BOT_TOKEN)

