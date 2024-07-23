"""Ня.

да, это маленькое расширение нужно чтобы някать ваших участников,
не больше.

Предоставляет
-------------

- /nya <member> - Някнуть участника

Version: v0.3
Author: Milinuri Nirvalen
"""

import arc
import hikari

plugin = arc.GatewayPlugin("Nya")


# определение команд
# ==================

@plugin.include
@arc.slash_command("nya", description="Скажи ня участнику сервера.")
async def nya_handler(
    ctx: arc.GatewayContext,
    user: arc.Option[
        hikari.User | None, arc.UserParams("Кого нужно някнуть")
    ] = None
) -> None:
    """Первая няшная команда для бота.

    Позволяет някнуть участника, пожалуй это достаточно мило.
    Впрочем более эта команда ничего не делает.
    """
    if user is not None:
        await ctx.respond(f"{user.mention}, ня?")
    else:
        await ctx.respond("ня!")


# Загрузчики и выгрузчики плагина
# ===============================

@arc.loader
def loader(client: arc.GatewayClient) -> None:
    client.add_plugin(plugin)

@arc.unloader
def unloader(client: arc.GatewayClient) -> None:
    client.remove_plugin(plugin)
