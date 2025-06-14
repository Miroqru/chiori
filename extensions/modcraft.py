"""Расширение для сервера ModCraft.

Сделано с целью интеграции с одноимённым сервером Discord.

Предоставляет
-------------

Version: v0.5 (9)
Author: Milinuri Nirvalen
"""

from datetime import UTC, datetime

import arc
import hikari
from mcstatus import JavaServer
from mcstatus.responses import JavaStatusPlayers

# Глобальные переменные
# =====================

plugin = arc.GatewayPlugin("ModCraft")
_RULE_TIMESTAMP = datetime(2024, 6, 6, 15, 49, tzinfo=UTC)
_SERVER_IP = "polaris.minerent.net:25598"


# определение команд
# ==================

cmd_group = plugin.include_slash_group(
    name="mc", description="Взаимодействие с сервером ModCraft."
)

_SERVER_DESC = (
    "**ModCraft** — это уникальный сервер Minecraft, "
    "созданный для любителей модов.\n"
    "Здесь вы найдете множество интересных модификаций, "
    "которые добавят новые механики, предметы и возможности в вашу игру."
)

_SERVER_EVENTS = (
    "Мы регулярно проводим конкурсы и ивенты с призами для активных игроков."
)

_SERVER_FEATURES = (
    "**Моды**: множество популярных модов, таких как create, tacz, "
    "sophisticated backpacks, и многие другие.\n"
    "**Кастомные механики**: Уникальные механики и квесты, которые сделают "
    "игру еще более интересной и разнообразной.\n"
    "**Сообщество**: У нас дружелюбное и активное сообщество игроков, "
    "которые всегда готовы помочь новичкам.\n"
    "**Регулярные обновления**: Мы постоянно обновляем сервер, добавляя новые "
    "моды, исправляя баги и улучшая игровой процесс.\n"
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
@arc.slash_subcommand("info", description="Информация о сервере.")
async def server_info(ctx: arc.GatewayContext) -> None:
    """Общая информация о сервере.

    Позволяет новым участника больше узнать о сервере.
    """
    emb = hikari.Embed(
        title="🎮 Сервер ModCraft",
        description=_SERVER_DESC,
        color=0x814634,
        timestamp=_RULE_TIMESTAMP,
    )
    emb.add_field(name="🎁 События", value=_SERVER_EVENTS)
    emb.add_field(name="🌟 Особенности", value=_SERVER_FEATURES)
    emb.add_field(
        name="🍷 Правила сервера",
        value=(
            "1.Уважайте других игроков\n"
            "2.Не используйте читы или эксплоиты\n"
            "3.Следуйте указаниям администрации\n"
        ),
    )
    await ctx.respond(emb)


@cmd_group.include
@arc.slash_subcommand("rules", description="Правила discord сервера.")
async def server_rules(ctx: arc.GatewayContext) -> None:
    """Правила Discord сервера.

    Позволяет новым участникам ознакомиться с командами сервера.
    """
    emb = hikari.Embed(
        title="☕ Правила сервера ModCraft",
        description=(
            "1.Запрещено строить лаг машины\n"
            "Нарушение данного правила приведет к постоянному бану.\n\n"
            "2.Оскорбление игроков\n"
            "за Направленное оскорбление конкретного игрока бан на 1 месяц\n\n"
            "3.Уничтожение объектов общего пользования\n"
            "В зависимости от сезона, бан на 3 месяца\n\n"
            "4.Распространение непристойного контента\n"
        ),
        color=0x814634,
        timestamp=_RULE_TIMESTAMP,
    )
    await ctx.respond(emb)


@cmd_group.include
@arc.slash_subcommand("commands", description="Список основных команд.")
async def server_commands(ctx: arc.GatewayContext) -> None:
    """Основные команды в Minecraft.

    Позволяет новым участникам разобраться с базовыми командами.
    """
    emb = hikari.Embed(
        title="📖 Основные команды",
        description=(
            "**/seller** - скупщик\n"
            "**/ah** - аукцион\n"
            "**/baltop** или **/balancetop /ball** - топ по балансу\n"
            "**/ah sell** `[цена]` - выставить предмет в руке на аукцион\n"
            "**/login** `[пароль]` - вход в аккаунт\n"
            "**/register** `[пароль]` `[пароль]` - регистрация аккаунта\n"
            "**/changepassword** `<старый>` `<новый>` - смена пароля\n"
            "**/reports** - жалоба на игрока"
        ),
        color=0x814634,
        timestamp=_RULE_TIMESTAMP,
    )
    await ctx.respond(emb)


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

    if status.forge_data is None or status.forge_data.mods is None:
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
    client.add_plugin(plugin)


@arc.unloader
def unloader(client: arc.GatewayClient) -> None:
    """Действия при выгрузке плагина."""
    client.remove_plugin(plugin)
