"""Управление каналами на сервере.

позволяет просматривать/изменять/удалять каналы для сервера.

Version: v1.0 (1)
Author: Milinuri Nirvalen
"""

import arc
import hikari

from chioricord.client import ChioClient, ChioContext
from chioricord.plugin import ChioPlugin
from libs.channels import ChannelsTable, GuildChannels

plugin = ChioPlugin("Channels")

channels_group = plugin.include_slash_group(
    "channels",
    "Управление каналами сервера.",
    default_permissions=hikari.Permissions.MANAGE_CHANNELS,
)


async def _get_chan(
    client: arc.GatewayClient, channel_id: hikari.Snowflakeish
) -> hikari.TextableGuildChannel:
    """Возвращает канал по его ID."""
    chan = client.cache.get_guild_channel(
        channel_id
    ) or await client.rest.fetch_channel(channel_id)
    if not isinstance(chan, hikari.TextableGuildChannel):
        raise ValueError("Channel is not guild textable channel")
    return chan


@channels_group.include
@arc.slash_subcommand("list", description="Каналы на сервере")
async def list_channels(
    ctx: ChioContext, chan: GuildChannels = arc.inject()
) -> None:
    """Список установленных каналов сервера."""
    chan_list: list[str] = []
    for name, c in (await chan.channels()).items():
        text_chan = await _get_chan(ctx.client, c.channel_id)
        chan_list.append(f"- `{name}`: {text_chan.mention}")

    emb = hikari.Embed(
        title="📣 каналы",
        description="\n".join(chan_list),
        color=hikari.Color(0xFFCC99),
    )
    await ctx.respond(emb)


@channels_group.include
@arc.slash_subcommand("set", description="Связать канал с именем")
async def set_channel(
    ctx: ChioContext,
    chan: arc.Option[
        hikari.TextableChannel, arc.ChannelParams("Канал для привязки")
    ],
    name: arc.Option[str, arc.StrParams("Имя для канала")],
    channels: GuildChannels = arc.inject(),
) -> None:
    """Связывает канал с его именем."""
    await channels.set(name, chan.id)
    emb = hikari.Embed(
        title="📣 Привязка канала",
        description=f"Канал {chan.mention} с именем `{name}`",
        color=hikari.Color(0xCCFF99),
    )
    await ctx.respond(emb)


@channels_group.include
@arc.slash_subcommand("remove", description="Удалить канал")
async def remove_channel(
    ctx: ChioContext,
    name: arc.Option[str, arc.StrParams("Имя для канала")],
    channels: GuildChannels = arc.inject(),
) -> None:
    """Отвязывает канал от имени."""
    await channels.unset(name)
    emb = hikari.Embed(
        title="📣 Отвязка канала",
        description=f"Канал `{name}` сброшен",
        color=hikari.Color(0xFF99CC),
    )
    await ctx.respond(emb)


@channels_group.include
@arc.slash_subcommand("reset", description="Сбросить все каналы")
async def reset_channels(
    ctx: ChioContext, chan: GuildChannels = arc.inject()
) -> None:
    """Сбрасывает все каналы на сервере."""
    await chan.reset()
    emb = hikari.Embed(
        title="📣 сброс каналов",
        description="Все каналы на сервере сброшены. Можете приступать.",
        color=hikari.Color(0xFF99CC),
    )
    await ctx.respond(emb)


@arc.loader
def loader(client: ChioClient) -> None:
    """Actions on plugin load."""
    plugin.add_table(ChannelsTable)
    client.add_plugin(plugin)
