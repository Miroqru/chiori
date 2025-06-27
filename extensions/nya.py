"""Ня.

да, это маленькое расширение нужно чтобы някать ваших участников,
не больше.

> [!tip] Шаблонное расширение.
> Вы Легко можете начать писать своё расширение для Чиори,
> взяв за основу исходный код данного расширения.

Предоставляет
-------------

- /nya <member> - Някнуть участника

Version: v0.4 (6)
Author: Milinuri Nirvalen
"""

import arc
import hikari

from chioricord.config import PluginConfig, PluginConfigManager

plugin = arc.GatewayPlugin("Nya")


class NyaConfig(PluginConfig):
    """Пример использования настроек для плагина."""

    message: str = "ня!"
    mention: str = "{user}, ня?"


# определение команд
# ==================


@plugin.include
@arc.slash_command("nya", description="Скажи ня участнику сервера.")
async def nya_handler(
    ctx: arc.GatewayContext,
    user: arc.Option[  # type: ignore
        hikari.User | None, arc.UserParams("Кого нужно някнуть")
    ] = None,
    config: NyaConfig = arc.inject(),
) -> None:
    """Первая няшная команда для бота.

    Позволяет някнуть участника, пожалуй это достаточно мило.
    Впрочем более эта команда ничего не делает.
    """
    if user is not None:
        await ctx.respond(config.mention.format(user=user.mention))
    else:
        await ctx.respond(config.message)


# Загрузчики и выгрузчики плагина
# ===============================


@arc.loader
def loader(client: arc.GatewayClient) -> None:
    """Действия при загрузке плагина."""
    client.add_plugin(plugin)
    cm = client.get_type_dependency(PluginConfigManager)
    cm.register("nya", NyaConfig)


@arc.unloader
def unloader(client: arc.GatewayClient) -> None:
    """Действия при выгрузке плагина."""
    client.remove_plugin(plugin)
