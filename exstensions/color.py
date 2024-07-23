"""Цвета.

небольшой плагин для художников.
позволяет выбрать цвета в формате HEX, RGB, HSV.

Предоставляет
-------------

- /color - Получить случайный цвет
- /color [color] - Узнать информацию о цвете.

Version: v0.3 (3)
Author: Milinuri Nirvalen
"""

import arc
import hikari

from libs.color import Color, ColorParseError

plugin = arc.GatewayPlugin("color")


# определение команд
# ==================

@plugin.include
@arc.slash_command("color", description="Узнать информцию о цвете.")
async def color_hadnler(
    ctx: arc.GatewayContext,
    color: arc.Option[
        str | None, arc.StrParams("Hex, RGB, HSV (случайный цвет)")
    ] = None
) -> None:
    """Получает информацию о цвете.

    Выводит hex, rgb, hsv коды цвета.
    Если не передавать никакого цвета, то получил случайный цвет
    из палитры.
    """
    # получаем цвет
    if color is None:
        color = Color.random()
    else:
        try:
            color = Color.parse_color(color)
        except ColorParseError:
            emb = hikari.Embed(title="Неправильный формат?",
                description="Пример: `#ffccff`; `rgb(12, 13, 14)`.",
                color=hikari.colors.Color(0xff00aa)
            )
            return await ctx.respond(embed=emb)

    # Собираем информацию о цвете
    emb = hikari.Embed(
        title="🎨 Информация о цвете",
        colour=int(color.to_hex_code()[1:], base=16)
    ).add_field(name="hex", value=color.to_hex_code(), inline=True
    ).add_field(
        name="rgb",
        value=f"{color.red}, {color.green}, {color.blue}",
        inline=True
    )

    hsv = color.to_hsv()
    emb.add_field(
        name="hsv",
        value=f"{hsv[0]}, {hsv[1]}, {hsv[2]}",
        inline=True
    )

    await ctx.respond(embed=emb)


# Загрузчики и выгрузчики плагина
# ===============================

@arc.loader
def loader(client: arc.GatewayClient) -> None:
    client.add_plugin(plugin)

@arc.unloader
def unloader(client: arc.GatewayClient) -> None:
    client.remove_plugin(plugin)
