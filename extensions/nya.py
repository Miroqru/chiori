"""Ня.

да, это маленькое расширение нужно чтобы някать ваших участников,
не больше.

.. tip:: Шаблонное расширение.

    Вы Легко можете начать писать своё расширение для Чиори,
    взяв за основу исходный код данного расширения.

Предоставляет
-------------

- /nya <member> - Някнуть участника

Version: v0.4 (5)
Author: Milinuri Nirvalen
"""

import arc
import hikari

# Глобальные переменные
# =====================

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
    """Действия при загрузке плагина."""
    client.add_plugin(plugin)

@arc.unloader
def unloader(client: arc.GatewayClient) -> None:
    """Действия при выгрузке плагина."""
    client.remove_plugin(plugin)
