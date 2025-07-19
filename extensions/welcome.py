"""Приветствие.

Приветствует новых участников на сервере.

Version: v1.0 (1)
Author: Milinuri Nirvalen
"""

import arc
import hikari

from chioricord.config import PluginConfig, PluginConfigManager

plugin = arc.GatewayPlugin("Welcome")


class WelcomeConfig(PluginConfig):
    """Пример использования настроек для плагина."""

    listen_guild: int

    welcome_channel: int

    welcome_role: int | None = None


# Обработка событий
# =================


@plugin.listen(hikari.MemberCreateEvent)
@plugin.inject_dependencies()
async def on_join(
    event: hikari.MemberCreateEvent, config: WelcomeConfig = arc.inject()
) -> None:
    """Когда кто-то заходит на сервере."""
    if event.user.is_bot or event.guild_id != config.listen_guild:
        return

    if config.welcome_role is not None:
        await event.member.add_role(config.welcome_role)

    emb = hikari.Embed(
        title="Добро пожаловать.",
        description=f"Мы рабы приветствовать {event.member.mention}!",
        color=hikari.Color(0x99FFCC),
    )
    emb.set_thumbnail(event.member.make_avatar_url())
    await event.app.rest.create_message(config.welcome_channel, emb)


# Загрузчики и выгрузчики плагина
# ===============================


@arc.loader
def loader(client: arc.GatewayClient) -> None:
    """Действия при загрузке плагина."""
    client.add_plugin(plugin)
    cm = client.get_type_dependency(PluginConfigManager)
    cm.register("welcome", WelcomeConfig)


@arc.unloader
def unloader(client: arc.GatewayClient) -> None:
    """Действия при выгрузке плагина."""
    client.remove_plugin(plugin)
