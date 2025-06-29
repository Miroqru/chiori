"""Обработчик для nekos.best.

Отправляет различные весёлые анимешные картиночки.
В отличие от собрата nekos.life выглядит более презентабельно.

Предоставляет
-------------

- /neko <group> - Милая аниме картинка.

Version: v1.0 (2)
Author: Milinuri Nirvalen
"""

from dataclasses import dataclass
from typing import TypedDict

import aiohttp
import arc
import hikari

plugin = arc.GatewayPlugin("Nekos best")

API_URL = "https://nekos.best/api/v2"


@dataclass
class NekoImage:
    """Описывает отдельный тип команды для картинки."""

    header: str
    color: hikari.Color = hikari.Color(0xFF99CC)


_CATEGORIES = {
    "husbando": NekoImage("🩷 Муженёк."),
    "kitsune": NekoImage("🩷 Китсуна."),
    "neko": NekoImage("🩷 Неко."),
    "waifu": NekoImage("🩷 Вайфу."),
    "angry": NekoImage("🩷 Злость."),
    "baka": NekoImage("🩷 Бяка."),
    "bite": NekoImage("🩷 Укусить."),
    "blush": NekoImage("🩷 Румянец."),
    "bored": NekoImage("🩷 Грусть."),
    "cry": NekoImage("🩷 Грусть."),
    "cuddle": NekoImage("🩷 Прижиматься."),
    "dance": NekoImage("🩷 Танцевать."),
    "facepalm": NekoImage("🩷 Фейспалм."),
    "feed": NekoImage("🩷 Покормить."),
    "handhold": NekoImage("🩷 Взять за руку."),
    "handshake": NekoImage("🩷 Пожать руку."),
    "happy": NekoImage("🩷 Счастье."),
    "highfive": NekoImage("🩷 Дать пять"),
    "hug": NekoImage("🩷 Обнять."),
    "kick": NekoImage("🩷 Ударить."),
    "kiss": NekoImage("🩷 Поцелуй."),
    "laugh": NekoImage("🩷 Посмеяться"),
    "lurk": NekoImage("🩷 Спрятаться."),
    "nod": NekoImage("🩷 Кивнуть."),
    "nom": NekoImage("🩷 Ням."),
    "nope": NekoImage("🩷 Отказаться."),
    "pat": NekoImage("🩷 Погладить."),
    "peck": NekoImage("🩷 Чмок."),
    "poke": NekoImage("🩷 Тык."),
    "pout": NekoImage("🩷 Надуться."),
    "punch": NekoImage("🩷 Ударить."),
    "run": NekoImage("🩷 Убежать."),
    "shoot": NekoImage("🩷 Выстрелить."),
    "shrug": NekoImage("🩷 Пожать плечами."),
    "slap": NekoImage("🩷 Пощёчина."),
    "sleep": NekoImage("🩷 Сон."),
    "smile": NekoImage("🩷 Улыбка."),
    "smug": NekoImage("🩷 Довольная морда."),
    "stare": NekoImage("🩷 пялиться."),
    "think": NekoImage("🩷 Раздумия."),
    "thumbsup": NekoImage("🩷 Одобрить."),
    "tickle": NekoImage("🩷 Шекотка."),
    "wave": NekoImage("🩷 Помахать рукой."),
    "wink": NekoImage("🩷 Подмигнуть."),
    "yawn": NekoImage("🩷 Зевнуть."),
    "yeet": NekoImage("🩷 Швырнуть."),
}


async def category_opts(
    data: arc.AutocompleteData[arc.GatewayClient, str],
) -> list[str]:
    """Авто дополнение для списка расширений."""
    extensions = sorted(list(_CATEGORIES.keys()))
    if data.focused_value is None:
        return extensions[:25]

    res: list[str] = []
    for ext in extensions:
        if ext.startswith(data.focused_value):
            res.append(ext)
    return res[:25]


class ImageResult(TypedDict):
    """Результат получения картинки."""

    artist_name: str | None
    artist_href: str | None
    source_url: str | None
    anime_name: str | None
    url: str


@plugin.include
@arc.slash_command(name="neko", description="Милая аниме картинка.")
async def neko_image(
    ctx: arc.GatewayContext,
    category: arc.Option[  # type: ignore
        str, arc.StrParams("Тип картинки", autocomplete_with=category_opts)
    ],
) -> None:
    """Отправляет аниме картинку."""
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{API_URL}/{category}") as res:
            resp: ImageResult = (await res.json())["results"][0]

    image = _CATEGORIES[category]
    emb = hikari.Embed(
        title=image.header,
        description=resp.get("anime_name"),
        color=image.color,
        url=resp.get("source_url"),
    )
    emb.set_image(resp["url"])
    if resp.get("artist_name"):
        emb.set_author(name=resp["artist_name"], url=resp["artist_href"])
    await ctx.respond(emb)


# Загрузчики и выгрузчики плагина
# ===============================


@arc.loader
def loader(client: arc.GatewayClient) -> None:
    """Действия при загрузке плагина."""
    client.add_plugin(plugin)


@arc.unloader
def unloader(client: arc.GatewayClient) -> None:
    """Действия при выгрузке плагина."""
    client.remove_plugin(plugin)
