"""
Простой код для работы с цветом.

## Команды

- color: Получить случайный цвет
- color [hex]: получить информацию о цвете

Author: Milinuri Nirvalen
Verion: v0.2 (2)
"""

import discord.colour
from discord.ext import commands
from discord.ext.commands import Bot

from libs.color import Color, ColorParseError


class ColorCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def color(self, ctx: commands.Context, *, color_code: str | None):
        if color_code is None:
            color = Color.random()
        else:
            try:
                color = Color.parse_color(color_code)
            except ColorParseError as e:
                return await ctx.send(
                    "Пример цветового кода: #ffccff; rgb(12, 13, 14)"
                )

        embed = discord.Embed(
            title="Информация о цвете",
            colour=int(color.to_hex_code()[1:], base=16)
        )

        embed.add_field(
            name="hex",
            value=color.to_hex_code(),
            inline=True
        )

        embed.add_field(
            name="rgb",
            value=f"{color.red}, {color.green}, {color.blue}",
            inline=True
        )

        hsv = color.to_hsv()
        embed.add_field(
            name="hsv",
            value=f"{hsv[0]}, {hsv[1]}, {hsv[2]}",
            inline=True
        )


        embed.set_footer(text="Вы просто лапочка")
        await ctx.send(embed=embed)


async def setup(bot: Bot):
    await bot.add_cog(ColorCog(bot))
