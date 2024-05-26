"""Простой ког для общения с GPT

Author: Milinuri
Version: v0.1 (2)
"""

from discord.ext import commands

from g4f.client import Client
import g4f.Provider.Aichatos


gpt_client = Client()


class GPTCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(description="Talk to ChatGPT")
    async def gpt(self, ctx: commands.Context, *, args: str | None):
        if args is None:
            return await ctx.send("Использовать c!gpt <запрос>.")

        response = gpt_client.chat.completions.create(
            model="gpt-4",
            messages=[
                {
                    "role": "system",
                    "content":"Твоя задача подробно отвечать на русском языке"
                },
                {"role": "user", "content": args}
            ],
            provider=g4f.Provider.Aichatos
        )
        await ctx.send(response.choices[0].message.content)


async def setup(bot: commands.Bot):
    await bot.add_cog(GPTCog(bot))