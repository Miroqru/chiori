"""Эффекты изображения.

Небольшой шуточный плагин для применения эффекта на аватарках
пользователя.

Version: v0.1.2 (3)
Author: Milinuri Nirvalen
"""

import arc
import hikari

from chioricord.client import ChioClient, ChioContext
from chioricord.plugin import ChioPlugin

plugin = ChioPlugin("Avatar effects")


@plugin.include
@arc.slash_command("avatar", description="Аватарка пользователя.")
async def user_avatar(
    ctx: ChioContext,
    user: arc.Option[  # type: ignore
        hikari.User | None, arc.UserParams("Чью получить аватарку")
    ] = None,
) -> None:
    """Получает аватарку пользователя."""
    # avatar =
    if user is None:
        user = ctx.author
    emb = hikari.Embed(
        title="Ава пользователя",
    )
    avatar_url = user.make_avatar_url(file_format="PNG")
    if avatar_url is not None:
        emb.set_image(avatar_url)
    else:
        emb.description = "у пользователя не обнаружена аватарка."
    await ctx.respond(emb)


@plugin.include
@arc.slash_command("triggered", description="Триггеред аватар пользователя.")
async def triggered_avatar(
    ctx: ChioContext,
    user: arc.Option[  # type: ignore
        hikari.User | None, arc.UserParams("Чью получить аватарку")
    ] = None,
) -> None:
    """Получает аватарку пользователя."""
    # avatar =
    if user is None:
        user = ctx.author
    avatar_url = user.make_avatar_url(file_format="PNG")

    # async with aiohttp.ClientSession() as session:
    #     async with session.get(avatar_url) as res:
    #         data = await res.text()

    emb = hikari.Embed(
        title="Ава пользователя",
    )
    emb.set_image(avatar_url)
    await ctx.respond(emb)


# Загрузчики и выгрузчики плагина
# ===============================


@arc.loader
def loader(client: ChioClient) -> None:
    """Действия при загрузке плагина."""
    client.add_plugin(plugin)
