"""Расширение для сервера ModCraft.

Сделано с целью интеграции с одноимённым сервером Discord.

Предоставляет
-------------

Version: v0.6.1 (11)
Author: Milinuri Nirvalen
"""

from pathlib import Path

import arc
import hikari
from loguru import logger
from mcstatus import JavaServer
from mcstatus.responses import JavaStatusPlayers

from libs.static_embeds import StaticCommands, load_commands

plugin = arc.GatewayPlugin("ModCraft")
_SERVER_IP = "hydra.minerent.net:25598"
sc = StaticCommands()
COMMANDS_PATh = Path("bot_data/modcraft_embeds.json")


# определение команд
# ==================

cmd_group = plugin.include_slash_group(
    name="mc", description="Взаимодействие с сервером ModCraft."
)


def online_status(players: JavaStatusPlayers) -> str:
    """Собирает сообщение с онлайном сервера."""
    if players.online == 0:
        return "Сейчас никого нет, может поиграем? 🥹"
    if players.sample is None:
        return "🕸️ Нет информации об онлайне."

    list_online = ""
    for player in players.sample:
        list_online += f"- {player.name}\n"
    return list_online


@cmd_group.include
@arc.slash_subcommand("status", description="Статус Minecraft сервера.")
async def server_status(ctx: arc.GatewayContext) -> None:
    """Статус Minecraft сервера.

    Получает основную информацию о сервере.
    Название, версия, количество игроков, пинг.
    Также информация о Forge, если имеется.
    """
    server = await JavaServer.async_lookup(_SERVER_IP)
    status = await server.async_status()
    ping = round(status.latency, 2)

    emb = hikari.Embed(
        title="🌟 Статус сервера",
        description=(
            f"{status.version.name} ({status.version.protocol})\n"
            f"Motd: {status.motd.to_plain()}\n"
            f"Ping {ping} мс.\n"
        ),
        color=0x3D994C,
    )
    if status.forge_data is not None:
        emb.add_field(
            "Forge",
            (
                f"FML version: `{status.forge_data.fml_network_version}`\n"
                f"Channels: `{len(status.forge_data.channels)}`\n"
                f"Mods: `{len(status.forge_data.mods)}`\n"
                f"truncated: {status.forge_data.truncated}"
            ),
            inline=True,
        )
    emb.add_field(
        f"В сети {status.players.online}/{status.players.max}",
        online_status(status.players),
        inline=True,
    )
    await ctx.respond(emb)


@cmd_group.include
@arc.slash_subcommand("mods", description="Какие моды установлены на сервере.")
async def server_mods(ctx: arc.GatewayContext) -> None:
    """Список модов на сервере.

    Содержит название и версию мода.
    """
    server = await JavaServer.async_lookup(_SERVER_IP)
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
        mod_list = ""
        for mod in sorted(status.forge_data.mods, key=lambda m: m.name):
            mod_list += f"✨ {mod.name}: {mod.marker}\n"

        emb = hikari.Embed(
            title=f"📦 Список модов ({len(status.forge_data.mods)})",
            description=mod_list,
            color=0x3D994C,
        )

    await ctx.respond(emb)


@cmd_group.include
@arc.slash_subcommand("ping", description="Скорость ответа от сервера.")
async def server_ping(ctx: arc.GatewayContext) -> None:
    """Пинг Minecraft сервера.

    Получает задержку между ботом и сервером.
    Уровень задержки отображает цветом.
    """
    server = await JavaServer.async_lookup(_SERVER_IP)
    ping = round(await server.async_ping(), 2)
    green = min(0, int(0xFF * (1 - ping / 150)))
    color = hikari.Color.from_rgb(0xFF, green, 0x99)
    emb = hikari.Embed(
        title="⚡ Ping", description=f"Ping сервера: `{ping}` мс.", color=color
    )
    await ctx.respond(emb)


# Загрузчики и выгрузчики плагина
# ===============================


@arc.loader
def loader(client: arc.GatewayClient) -> None:
    """Действия при загрузке плагина."""
    commands = load_commands(COMMANDS_PATh)
    for command in commands:
        logger.info("Add command: {}: {}", command.name, command.desc)
        cmd_group.include(sc.add_subcommand(command))

    client.add_plugin(plugin)


@arc.unloader
def unloader(client: arc.GatewayClient) -> None:
    """Действия при выгрузке плагина."""
    client.remove_plugin(plugin)
