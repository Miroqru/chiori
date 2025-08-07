"""Цвета.

небольшой плагин для художников.
позволяет выбрать цвета в формате HEX, RGB, HSV.

Version: v0.3.4 (8)
Author: Milinuri Nirvalen
"""

import arc
import hikari

from chioricord.client import ChioClient, ChioContext
from chioricord.plugin import ChioPlugin
from libs.color import Color, ColorParseError

plugin = ChioPlugin("Color")


# определение команд
# ==================


@plugin.include
@arc.slash_command("color", description="Информация о цвете.")
async def color_selector(
    ctx: ChioContext,
    color: arc.Option[  # type: ignore
        str | None, arc.StrParams("Hex, RGB, HSV (случайный цвет)")
    ] = None,
) -> None:
    """Получает информацию о цвете.

    Выводит hex, rgb, hsv коды цвета.
    Если не передавать никакого цвета, то получил случайный цвет
    из палитры.
    """
    # получаем цвет
    if color is None:
        parse_color = Color.random()
    else:
        parse_color = Color.parse_color(color)

    # Собираем информацию о цвете
    emb = (
        hikari.Embed(
            title="🎨 Информация о цвете",
            colour=int(parse_color.to_hex_code()[1:], base=16),
        )
        .add_field(name="hex", value=parse_color.to_hex_code(), inline=True)
        .add_field(
            name="rgb",
            value=f"{parse_color.red}, {parse_color.green}, {parse_color.blue}",
            inline=True,
        )
    )

    hsv = parse_color.to_hsv()
    emb.add_field(
        name="hsv", value=f"{hsv[0]}, {hsv[1]}, {hsv[2]}", inline=True
    )

    await ctx.respond(embed=emb)


@color_selector.set_error_handler
async def error_handler(ctx: ChioContext, exc: Exception) -> None:
    """Обрабатывает ошибки получения цвета."""
    if isinstance(exc, ColorParseError):
        emb = hikari.Embed(
            title="Неправильный формат?",
            description="Пример: `#ffccff`; `rgb(12, 13, 14)`.",
            color=hikari.Color(0xFF00AA),
        )
        await ctx.respond(emb)
        return
    raise exc


# Загрузчики и выгрузчики плагина
# ===============================


@arc.loader
def loader(client: ChioClient) -> None:
    """Действия при загрузке плагина."""
    client.add_plugin(plugin)
