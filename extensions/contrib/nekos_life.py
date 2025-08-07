"""Милые картинки из nekos.life.

Отправляет различные весёлые анимешные картиночки.

Скоре всего сервис уже устарел, поскольку последнее обновление в
репозитории было несколько лет назад.
Однако сервис продолжает работать, так что продолжаем.

Version: v1.3.1 (6)
Author: Milinuri Nirvalen
"""

from dataclasses import dataclass
from urllib.parse import quote

import aiohttp
import arc
import hikari
from aiohttp import ClientSession

from chioricord.client import ChioClient, ChioContext
from chioricord.plugin import ChioPlugin

plugin = ChioPlugin("Nekos life")
neko = plugin.include_slash_group(
    name="nekos", description="Различные милые команды."
)

API_URL = "https://nekos.life/api/v2"


@dataclass
class NekoImage:
    """Описывает отдельный тип команды для картинки."""

    header: str
    url: str
    color: hikari.Color = hikari.Color(0xFF99CC)


_IMAGE_TYPES = {
    "avatar": NekoImage("🩷 Аватар.", "/img/avatar"),
    "cuddle": NekoImage("🩷 Прижаться.", "/img/cuddle"),
    "8ball": NekoImage("🩷 Мудрый шар.", "/img/8ball"),
    "smug": NekoImage("🩷 Довольная мордочка.", "/img/smug"),
    "woof": NekoImage("🩷 Гав.", "/img/woof"),
    "goose": NekoImage("🩷 Гусёк.", "/img/goose"),
    "slap": NekoImage("🩷 Пощёчина.", "/img/slap"),
    "pat": NekoImage("🩷 Поглаживания.", "/img/pat"),
    "gecg": NekoImage("🩷 Every dollar ...", "/img/gecg"),
    "feed": NekoImage("🩷 Покормить.", "/img/feed/"),
    "fox_girl": NekoImage("🩷 Девочка-лисичка.", "/img/fox_girl"),
    "hug": NekoImage("🩷 Обнимашки.", "/img/hug"),
    "neko": NekoImage("🩷 Кошкодевочка.", "/img/neko"),
    "meow": NekoImage("🩷 Котик.", "/img/meow"),
    "kiss": NekoImage("🩷 Поцелуй.", "/img/kiss"),
    "wallpaper": NekoImage("🩷 Аниме обои.", "/img/wallpaper"),
    "tickle": NekoImage("🩷 Щекотка.", "/img/tickle"),
    "lizard": NekoImage("🩷 Ящерица", "/img/lizard"),
    "ngif": NekoImage("🩷 Неко гифка.", "/img/ngif"),
    "waifu": NekoImage("🩷 Ваша вайфу.", "/img/waifu"),
    "gasm": NekoImage("🩷 Оргазм.", "/img/gasm"),
    "spank": NekoImage("🩷 Шлепок.", "/img/spank"),
}


async def fetch(
    session: ClientSession, url: str, get: str, query: str | None = None
) -> str:
    """Получает данные из указанного источника."""
    url = f"{API_URL}/{url}"
    if url.endswith("?") and query is not None:
        url = f"{url}text={quote(query)}"

    async with session.get(url) as res:
        resp: str = (await res.json()).get(get)
    return resp


# Весёлые команды
# ===============


@neko.include
@arc.slash_subcommand(name="image", description="Анимешная рп картинка.")
async def neko_image(
    ctx: ChioContext,
    group: arc.Option[  # type: ignore
        str, arc.StrParams("Тип картинки", choices=list(_IMAGE_TYPES.keys()))
    ],
    member: arc.Option[  # type: ignore
        hikari.Member | None, arc.MemberParams("к кому применить действие")
    ] = None,
) -> None:
    """Отправляет аниме картинку.

    Одну из выбранной группы.
    Можно указать участника и тогда действие применится к нему.
    """
    image = _IMAGE_TYPES[group]
    async with aiohttp.ClientSession() as session:
        desc = ""
        if member is not None:
            desc += f"{member.mention}"
        emb = hikari.Embed(
            title=image.header, description=desc, color=image.color
        )
        emb.set_image(await fetch(session, image.url, "url"))
        await ctx.respond(emb)


@neko.include
@arc.slash_subcommand("cat", description="Кошачья мордочка.")
async def neko_cat(ctx: ChioContext) -> None:
    """Отправляет кошачью мордочку."""
    async with aiohttp.ClientSession() as session:
        await ctx.respond(await fetch(session, "/cat", "cat"))


@neko.include
@arc.slash_subcommand("fact", description="Интересный факт.")
async def neko_fact(ctx: ChioContext) -> None:
    """Отправляет интересный факт."""
    async with aiohttp.ClientSession() as session:
        await ctx.respond(await fetch(session, "/fact", "fact"))


@neko.include
@arc.slash_subcommand("name", description="Случайное имя.")
async def neko_name(ctx: ChioContext) -> None:
    """Отправляет интересный факт."""
    async with aiohttp.ClientSession() as session:
        await ctx.respond(await fetch(session, "/name", "name"))


@neko.include
@arc.slash_subcommand("why", description="Вопрос дня.")
async def neko_nya(ctx: ChioContext) -> None:
    """Отправляет случайный вопрос."""
    async with aiohttp.ClientSession() as session:
        await ctx.respond(await fetch(session, "/why", "why"))


# Загрузчики и выгрузчики плагина
# ===============================


@arc.loader
def loader(client: ChioClient) -> None:
    """Действия при загрузке плагина."""
    client.add_plugin(plugin)
