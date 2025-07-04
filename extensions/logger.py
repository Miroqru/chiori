"""Журнал событий.

Позволяет отслеживать действия участников в серверах рядом с ботом.
Это полезно для владельцев серверов, поскольку теперь ни одно важное
событие не пройдёт мимо бота.

Предоставляет
-------------

- @GuildMessageDeleteEvent
- @GuildMessageUpdateEvent
- @GuildChannelCreateEvent
- @GuildChannelUpdateEvent
- @GuildChannelDeleteEvent
- @RoleCreateEvent
- @RoleUpdateEvent
- @RoleDeleteEvent
- @MemberCreateEvent
- @MemberDeleteEvent
- @voiceStateUpdateEvent

Version: v1.1.1 (14)
Author: Milinuri Nirvalen
"""

from datetime import UTC, datetime

import arc
import hikari
from loguru import logger

from chioricord.config import PluginConfig, PluginConfigManager

plugin = arc.GatewayPlugin("Logger")


class LoggerConfig(PluginConfig):
    """Настройки для журнала событий."""

    channel_id: int
    """
    ID канала для отправки событий.
    Именно сюда будут отправляться все события бота.
    """


# Отслеживание сообщений
# ======================


@plugin.listen(hikari.GuildMessageDeleteEvent)
@plugin.inject_dependencies()
async def on_message_delete(
    event: hikari.GuildMessageDeleteEvent, config: LoggerConfig = arc.inject()
) -> None:
    """Когда кто-то удаляет сообщение в гильдии."""
    deleted = event.old_message
    if deleted is None or deleted.author.is_bot:
        logger.warning("Not enough information: {}", deleted)
        return None

    emb = hikari.Embed(
        title="💎 message delete",
        description=deleted.content,
        color=hikari.Color(0xFF6699),
        timestamp=deleted.created_at,
    )
    emb.add_field("Author", deleted.author.mention, inline=True)

    channel = event.get_channel()
    if isinstance(channel, hikari.GuildTextChannel):
        emb.add_field("Channel", channel.mention, inline=True)

    guild = event.get_guild()
    if guild is not None:
        emb.add_field("Guild", guild.name, inline=True)

    if len(deleted.attachments) > 0:
        emb.set_image(deleted.attachments[0].url)

    await plugin.client.rest.create_message(config.channel_id, emb)


@plugin.listen(hikari.GuildMessageUpdateEvent)
@plugin.inject_dependencies()
async def on_message_update(
    event: hikari.GuildMessageUpdateEvent, config: LoggerConfig = arc.inject()
) -> None:
    """Когда кто-то удаляет сообщение в гильдии."""
    if (
        isinstance(event.message.author, hikari.User)
        and event.message.author.is_bot
    ):
        return None

    emb = hikari.Embed(
        title="💎 Message edit",
        description=str(event.message.content),
        color=hikari.Color(0x66FF99),
        timestamp=datetime.now(tz=UTC),
    )

    member = event.member
    if isinstance(member, hikari.Member):
        emb.add_field("Author", member.mention, inline=True)

    channel = event.get_channel()
    if isinstance(channel, hikari.GuildTextChannel):
        emb.add_field("Channel", channel.mention, inline=True)

    guild = event.get_guild()
    if guild is not None:
        emb.add_field("Guild", guild.name, inline=True)

    await plugin.client.rest.create_message(config.channel_id, emb)


# Отслеживание каналов
# ====================


def channel_info(channel: hikari.PermissibleGuildChannel) -> str:
    """Возвращает краткую информацию о канале."""
    return (
        f"`{channel.type}` {channel.name}\n\n"
        f"Создан: {channel.created_at}\n"
        f"nsfw: {channel.is_nsfw}\n"
        f"Позиция: {channel.position}\n"
    )


@plugin.listen(hikari.GuildChannelCreateEvent)
@plugin.inject_dependencies()
async def on_channel_create(
    event: hikari.GuildChannelCreateEvent, config: LoggerConfig = arc.inject()
) -> None:
    """при создании новой роли."""
    emb = hikari.Embed(
        title="💎 Channel create",
        description=channel_info(event.channel),
        color=hikari.Color(0x6699FF),
        timestamp=datetime.now(tz=UTC),
    )

    guild = plugin.client.cache.get_guild(event.guild_id)
    if guild is not None:
        emb.add_field("Guild", guild.name, inline=True)
    emb.add_field("Channel", event.channel.mention, inline=True)

    await plugin.client.rest.create_message(config.channel_id, emb)


@plugin.listen(hikari.GuildChannelUpdateEvent)
@plugin.inject_dependencies()
async def on_channel_update(
    event: hikari.GuildChannelUpdateEvent, config: LoggerConfig = arc.inject()
) -> None:
    """при создании новой роли."""
    emb = hikari.Embed(
        title="💎 Channel update",
        description=channel_info(event.channel),
        color=hikari.Color(0x66FF99),
        timestamp=datetime.now(tz=UTC),
    )

    guild = plugin.client.cache.get_guild(event.guild_id)
    if guild is not None:
        emb.add_field("Guild", guild.name, inline=True)
    emb.add_field("Channel", event.channel.mention, inline=True)

    if event.old_channel is not None:
        emb.add_field("Оригинал", channel_info(event.old_channel))

    await plugin.client.rest.create_message(config.channel_id, emb)


@plugin.listen(hikari.GuildChannelDeleteEvent)
@plugin.inject_dependencies()
async def on_channel_delete(
    event: hikari.GuildChannelDeleteEvent, config: LoggerConfig = arc.inject()
) -> None:
    """при создании новой роли."""
    emb = hikari.Embed(
        title="💎 Channel delete",
        description=channel_info(event.channel),
        color=hikari.Color(0xFF6699),
        timestamp=datetime.now(tz=UTC),
    )

    guild = plugin.client.cache.get_guild(event.guild_id)
    if guild is not None:
        emb.add_field("Guild", guild.name, inline=True)
    emb.add_field("Channel", event.channel.mention, inline=True)

    await plugin.client.rest.create_message(config.channel_id, emb)


# Отслеживание ролей
# ==================


def role_info(role: hikari.Role) -> str:
    """Выводит сжатую избыточную информацию о роли из события."""
    flags = "Флаги:"

    if role.is_available_for_purchase:
        flags += " purchase;"

    if role.is_guild_linked_role:
        flags += " linked;"

    if role.is_hoisted:
        flags += " hoisted;"

    if role.is_managed:
        flags += " managed;"

    if role.is_mentionable:
        flags += " mentionable;"

    if role.is_premium_subscriber_role:
        flags += " premium subscriber;"

    if role.unicode_emoji is not None:
        emoji = str(role.unicode_emoji)
    else:
        emoji = ""

    return (
        f"{emoji} {role.name} ({role.color})\n"
        f"Создана: {role.created_at}\n"
        f"{flags}\n"
        f"Permissions: `{role.permissions}`"
    )


@plugin.listen(hikari.RoleCreateEvent)
@plugin.inject_dependencies()
async def on_role_create(
    event: hikari.RoleCreateEvent, config: LoggerConfig = arc.inject()
) -> None:
    """при создании новой роли."""
    emb = hikari.Embed(
        title="💎 Role create",
        description=role_info(event.role),
        color=hikari.Color(0x6699FF),
        timestamp=datetime.now(tz=UTC),
    )

    emb.set_thumbnail(event.role.make_icon_url(file_format="PNG"))
    guild = plugin.client.cache.get_guild(event.guild_id)
    if guild is not None:
        emb.add_field("Guild", guild.name, inline=True)
    emb.add_field("Role", event.role.mention, inline=True)

    await plugin.client.rest.create_message(config.channel_id, emb)


@plugin.listen(hikari.RoleUpdateEvent)
@plugin.inject_dependencies()
async def on_role_update(
    event: hikari.RoleUpdateEvent, config: LoggerConfig = arc.inject()
) -> None:
    """при создании новой роли."""
    emb = hikari.Embed(
        title="💎 Role update",
        description=role_info(event.role),
        color=hikari.Color(0x66FF99),
        timestamp=datetime.now(tz=UTC),
    )

    emb.set_thumbnail(event.role.make_icon_url(file_format="PNG"))
    guild = plugin.client.cache.get_guild(event.guild_id)
    if guild is not None:
        emb.add_field("Guild", guild.name, inline=True)
    emb.add_field("Role", event.role.mention, inline=True)

    if event.old_role is not None:
        emb.add_field("Old role", role_info(event.old_role))

    await plugin.client.rest.create_message(config.channel_id, emb)


@plugin.listen(hikari.RoleDeleteEvent)
@plugin.inject_dependencies()
async def on_role_remove(
    event: hikari.RoleDeleteEvent, config: LoggerConfig = arc.inject()
) -> None:
    """Когда удаляется роль."""
    if event.old_role is None:
        return

    emb = hikari.Embed(
        title="💎 Role delete",
        description=role_info(event.old_role),
        color=hikari.Color(0xFF6699),
        timestamp=datetime.now(tz=UTC),
    )

    emb.set_thumbnail(event.old_role.make_icon_url(file_format="PNG"))
    guild = plugin.client.cache.get_guild(event.guild_id)
    if guild is not None:
        emb.add_field("Guild", guild.name, inline=True)
    emb.add_field("Role", event.old_role.mention, inline=True)

    await plugin.client.rest.create_message(config.channel_id, emb)


# Отслеживание участников
# =======================


# TODO: Ну это ни в какие ворота, надо нормальное представление
def member_status(member: hikari.Member) -> str:
    """Сводка об участнике сервер."""
    return f"{member}"


@plugin.listen(hikari.MemberCreateEvent)
@plugin.inject_dependencies()
async def on_member_join(
    event: hikari.MemberCreateEvent, config: LoggerConfig = arc.inject()
) -> None:
    """Когда участник заходит на сервер."""
    emb = hikari.Embed(
        title="💎 Member create",
        description=member_status(event.member),
        color=hikari.Color(0x6699FF),
        timestamp=datetime.now(UTC),
    )

    guild = plugin.client.cache.get_guild(event.guild_id)
    if guild is not None:
        emb.add_field("Guild", guild.name, inline=True)

    emb.add_field("User", event.member.mention, inline=True)

    avatar_url = event.member.make_avatar_url(file_format="PNG")
    if avatar_url is not None:
        emb.set_thumbnail(avatar_url)

    await plugin.client.rest.create_message(config.channel_id, emb)


@plugin.listen(hikari.MemberDeleteEvent)
@plugin.inject_dependencies()
async def on_member_leave(
    event: hikari.MemberDeleteEvent, config: LoggerConfig = arc.inject()
) -> None:
    """когда участник покидает сервер."""
    if event.old_member is None:
        return

    emb = hikari.Embed(
        title="💎 Member delete",
        description=member_status(event.old_member),
        color=hikari.Color(0x6699FF),
        timestamp=datetime.now(UTC),
    )

    guild = plugin.client.cache.get_guild(event.guild_id)
    if guild is not None:
        emb.add_field("Guild", guild.name, inline=True)

    emb.add_field("User", event.old_member.mention, inline=True)

    avatar_url = event.old_member.make_avatar_url(file_format="PNG")
    if avatar_url is not None:
        emb.set_thumbnail(avatar_url)

    await plugin.client.rest.create_message(config.channel_id, emb)


# Отслеживание голосовых каналов
# ==============================


def _get_channel(channel_id: int) -> str:
    channel = plugin.client.cache.get_guild_channel(channel_id)
    if channel is not None:
        return channel.mention
    return f"`{channel_id}`"


async def _voice_status(state: hikari.VoiceState, app: hikari.RESTAware) -> str:
    if state.channel_id is not None:
        in_channel = _get_channel(state.channel_id)
    else:
        in_channel = "< без канала >"

    flags = "Flags:"
    if state.is_self_muted:
        flags += " mute;"
    if state.is_self_deafened:
        flags += " def;"
    if state.is_guild_muted:
        flags += " server mute;"
    if state.is_guild_deafened:
        flags += " server def;"
    if state.is_streaming:
        flags += " stream;"
    if state.is_suppressed:
        flags += " suppress;"
    if state.is_video_enabled:
        flags += " video;"
    if state.requested_to_speak_at is not None:
        flags += f"\nTo speak: {state.requested_to_speak_at}\n"

    return f"{flags}\nChannel: {in_channel}"


async def voice_status(event: hikari.VoiceStateUpdateEvent) -> hikari.Embed:
    """Информация о статусе голосового канала."""
    return hikari.Embed(
        title="🔊 Join voice channel",
        description=await _voice_status(event.state, event.app),
        color=hikari.Color(0x6699FF),
    )


async def leave_from_channel(
    event: hikari.VoiceStateUpdateEvent,
) -> hikari.Embed:
    """Embed о выходе из голосового канала."""
    if event.old_state is None:
        status = None
    else:
        status = await _voice_status(event.old_state, event.app)

    return hikari.Embed(
        title="🔊 Leave voice channel",
        description=status,
        color=hikari.Color(0xFF6699),
    )


async def voice_compare(event: hikari.VoiceStateUpdateEvent) -> hikari.Embed:
    """Сопоставляет информацию о двух состояниях."""
    old = event.old_state
    new = event.state

    if old is None or old.channel_id is None:
        return await voice_status(event)
    if new.channel_id is None:
        return await leave_from_channel(event)

    updates: list[str] = []
    status: list[str] = []

    # Переход по каналам
    new_channel = _get_channel(old.channel_id)
    if old.channel_id == new.channel_id:
        status.append(f"Channel: {new_channel}")
    else:
        updates.append(f"{_get_channel(new.channel_id)} -> {new_channel}")

    if new.requested_to_speak_at is not None:
        if old.requested_to_speak_at == new.requested_to_speak_at:
            status.append(f"👋 {new.requested_to_speak_at}")
        else:
            updates.append(
                f"👋 {old.requested_to_speak_at} -> {new.requested_to_speak_at}"
            )

    flags = [
        (old.is_self_muted, new.is_self_muted, "muted"),
        (old.is_self_deafened, new.is_self_deafened, "def"),
        (old.is_guild_muted, new.is_guild_muted, "server muted"),
        (old.is_guild_deafened, new.is_guild_deafened, "server def"),
        (old.is_streaming, new.is_streaming, "streaming"),
        (old.is_suppressed, new.is_suppressed, "suppressed"),
        (old.is_video_enabled, new.is_video_enabled, "video"),
    ]

    status.append("Flags: ")
    for old_flag, new_flag, name in flags:
        if old_flag == new_flag:
            if new_flag:
                status[-1] += f" {name};"
        elif new_flag:
            updates.append(f"✅ Now {name}")
        else:
            updates.append(f"❌ Disable {name}")

    emb = hikari.Embed(
        title="🔊 Update voice",
        description="\n".join(updates),
        color=hikari.Color(0x66FF99),
        timestamp=datetime.now(UTC),
    )
    emb.add_field("Status", "\n".join(status))
    return emb


@plugin.listen(hikari.VoiceStateUpdateEvent)
@plugin.inject_dependencies()
async def on_voice_update(
    event: hikari.VoiceStateUpdateEvent, config: LoggerConfig = arc.inject()
) -> None:
    """Изменение состояние голосового канала."""
    emb = await voice_compare(event)

    guild = plugin.client.cache.get_guild(event.guild_id)
    if guild is not None:
        emb.add_field("Guild", guild.name, inline=True)

    if event.state.member is not None:
        emb.add_field("Member", event.state.member.mention, inline=True)

    await plugin.client.rest.create_message(config.channel_id, emb)


# Загрузчики и выгрузчики плагина
# ===============================


@arc.loader
def loader(client: arc.GatewayClient) -> None:
    """Действия при загрузке плагина."""
    client.add_plugin(plugin)
    cm = client.get_type_dependency(PluginConfigManager)
    cm.register("logger", LoggerConfig)


@arc.unloader
def unloader(client: arc.GatewayClient) -> None:
    """Действия при выгрузке плагина."""
    client.remove_plugin(plugin)
