"""Расширение для сервера ModCraft.

Просмотр статуса, пинг и списка модов Minecraft сервера.
Сделано с целью интеграции с одноимённым сервером Discord.

Version: v0.9 (20)
Author: Milinuri Nirvalen
"""

import arc
import hikari
from mcstatus import JavaServer
from mcstatus.responses import JavaStatusPlayers

from chioricord.api import PluginConfig
from chioricord.client import ChioClient, ChioContext
from chioricord.plugin import ChioPlugin

plugin = ChioPlugin("ModCraft")

cmd_group = plugin.include_slash_group(
    name="mc", description="Взаимодействие с сервером ModCraft."
)


class ModcraftConfig(PluginConfig, config="modcraft"):
    """Настройки Modcraft сервера."""

    server_ip: str = "helix.minerent.net:21024"
    """IP minecraft сервера по умолчанию."""


def online_status(players: JavaStatusPlayers) -> str:
    """Собирает сообщение с онлайном сервера."""
    if players.online == 0:
        return "Сейчас никого нет, может поиграем? 🥹"
    if players.sample is None:
        return "🕸️ Нет информации об онлайне."

    list_online = [f"- {player.name}" for player in players.sample]
    return "\n".join(list_online)


@cmd_group.include
@arc.slash_subcommand("status", description="Статус Minecraft сервера.")
async def server_status(
    ctx: ChioContext,
    server_ip: arc.Option[
        str | None, arc.StrParams("IP Minecraft сервера.")
    ] = None,
    config: ModcraftConfig = arc.inject(),
) -> None:
    """Статус Minecraft сервера.

    Получает основную информацию о сервере.
    Название, версия, количество игроков, пинг.
    Также информация о Forge, если имеется.
    """
    server_ip = server_ip or config.server_ip
    server = await JavaServer.async_lookup(server_ip)
    status = await server.async_status()
    ping = round(status.latency, 2)

    emb = hikari.Embed(
        title="🌟 Статус сервера",
        description=(
            f"> {status.motd.to_plain()}\n\n"
            f"{status.version.name} ({status.version.protocol})\n"
            f"Ping {ping} мс.\n"
        ),
        color=0x3D994C,
    )
    if status.forge_data is not None:
        emb.add_field(
            f"FML `v{status.forge_data.fml_network_version}`",
            (
                f"Channels: `{len(status.forge_data.channels)}` "
                f"Mods: `{len(status.forge_data.mods)}`\n"
            ),
        )
    emb.add_field(
        f"В сети {status.players.online}/{status.players.max}",
        online_status(status.players),
    )
    emb.set_thumbnail(status.icon)
    await ctx.respond(emb)


@cmd_group.include
@arc.slash_subcommand("mods", description="Моды на сервере.")
async def server_mods(
    ctx: ChioContext,
    server_ip: arc.Option[
        str | None, arc.StrParams("IP Minecraft сервера.")
    ] = None,
    config: ModcraftConfig = arc.inject(),
) -> None:
    """Список модов для Forge сервера.

    Содержит название и версию мода.
    """
    server_ip = server_ip or config.server_ip
    server = await JavaServer.async_lookup(server_ip)
    status = await server.async_status()
    if status.forge_data is None:
        emb = hikari.Embed(
            title="📦 Список модов",
            description=(
                "А тут пусто и есть 2 варианта:\n"
                "- Это ванильный сервер.\n"
                "- На сервере не установлено ни одного мода."
            ),
            color=0x814634,
        )
    else:
        mod_list: list[str] = [
            f"✨ {mod.name}: {mod.marker}"
            for mod in sorted(status.forge_data.mods, key=lambda m: m.name)
        ]

        emb = hikari.Embed(
            title=(
                f"📦 Список модов {status.version.name} "
                f"(всего {len(status.forge_data.mods)})"
            ),
            description="\n".join(mod_list),
            color=0x3D994C,
        )

    emb.set_thumbnail(status.icon)
    await ctx.respond(emb)


def color_gradient(x: float) -> hikari.Color:
    """Цветовой градиент от зелёного к красному."""
    m = round(x / 1 * 0xFF)
    return hikari.Color((m << 16) + (0xFF - m << 8) + 0x99)


@cmd_group.include
@arc.slash_subcommand("ping", description="Скорость ответа от сервера.")
async def server_ping(
    ctx: ChioContext,
    server_ip: arc.Option[
        str | None, arc.StrParams("IP Minecraft сервера.")
    ] = None,
    config: ModcraftConfig = arc.inject(),
) -> None:
    """Пинг Minecraft сервера.

    Получает задержку между ботом и сервером.
    Уровень задержки отображает цветом.
    """
    server_ip = server_ip or config.server_ip
    server = await JavaServer.async_lookup(server_ip)
    ping = round(await server.async_ping(), 2)
    emb = hikari.Embed(
        title="⚡ Ping",
        description=f"Ping сервера: `{ping}` мс.",
        color=color_gradient(max(min(ping / 200, 1), 0)),
    )
    await ctx.respond(emb)


# Загрузчики и выгрузчики плагина
# ===============================


@arc.loader
def loader(client: ChioClient) -> None:
    """Действия при загрузке плагина."""
    plugin.set_config(ModcraftConfig)
    client.add_plugin(plugin)
