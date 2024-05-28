"""Всякие разнообразные команды для бота.

Author: Milinuri
Version: v0.1 (1)
"""

import random

from discord.ext import commands


# Основной класс кога
# ===================

class FunBox(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(description="Check bot online")
    async def ping(self, ctx: commands.Context):
        return await ctx.send("Pong!")

    @commands.command(description="Check bot online")
    async def dice(self, ctx: commands.Context):
        return await ctx.send(f"🎲{random.randint(1, 6)}")


# Функция для загрузки кога
# =========================

async def setup(bot: commands.Bot):
    await bot.add_cog(FunBox(bot))