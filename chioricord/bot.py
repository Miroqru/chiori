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
    command_prefix=commands.when_mentioned_or("c!"),
    intents=Intents.all(),
)
gpt_client = Client()


@bot.event
async def on_ready():
    logger.success("Bot started!")

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
    await bot.start(config.BOT_TOKEN)