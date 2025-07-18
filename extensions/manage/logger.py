"""Журнал событий.

Позволяет отслеживать действия участников в серверах рядом с ботом.
Это полезно для владельцев серверов, поскольку теперь ни одно важное
событие не пройдёт мимо бота.

Предоставляет
-------------

- Channel:
    - @GuildChannelCreateEvent
    - @GuildChannelDeleteEvent
    - @GuildChannelUpdateEvent
    - @GuildPinsUpdateEvent

- Threads:
    - @GuildThreadCreateEvent
    - @GuildThreadDeleteEvent
    - @GuildThreadUpdateEvent

- Invites
    - @InviteCreateEvent
    - @InviteDeleteEvent

- Webhooks:
    - @WebhookUpdateEvent

- @GuildMessageDeleteEvent
- @GuildMessageUpdateEvent
- @RoleCreateEvent
- @RoleUpdateEvent
- @RoleDeleteEvent
- @MemberCreateEvent
- @MemberDeleteEvent
- @voiceStateUpdateEvent

Version: v1.2 (18)
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

    async def send(self, emb: hikari.Embed) -> None:
        """Отправляет сообщение в канал."""
        await plugin.client.rest.create_message(self.channel_id, emb)


_COLOR_CREATE = hikari.Color(0x33FFCC)
_COLOR_UPDATE = hikari.Color(0x66CCFF)
_COLOR_DELETE = hikari.Color(0xFF66CC)

# Общее форматирование
# ====================


def _format_duration(seconds: int) -> str:
    """Преобразует количество секунд в более точное время."""
    minutes = seconds // 60
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    if days > 0:
        return f"{days} д. {hours:02d} ч. {minutes:02d} м."
    return f"{hours:02d} ч. {minutes:02d} м."


def _format_time(time: datetime, now: datetime | None = None) -> str:
    tf = time.strftime("%d/%m/%Y, %H:%M:%S")
    if now is not None:
        seconds = int((now - time).total_seconds())
        tf += f" ({_format_duration(seconds)})"
    return tf


# Получение данных из кеша
# ========================


def _get_channel(channel_id: int) -> str:
    channel = plugin.client.cache.get_guild_channel(channel_id)
    if channel is not None:
        return channel.mention
    return f"`{channel_id}`"


async def _get_guild(guild_id: int) -> hikari.Guild:
    return plugin.client.cache.get_guild(
        guild_id
    ) or await plugin.client.rest.fetch_guild(guild_id)


# Отслеживание каналов
# ====================


def channel_info(
    channel: hikari.PermissibleGuildChannel, now: datetime | None = None
) -> str:
    """Возвращает краткую информацию о канале."""
    nsfw = " 🔞" if channel.is_nsfw else ""
    return (
        f"`{channel.type}` {channel.name}{nsfw}\n\n"
        f"Позиция: {channel.position}\n"
    )


def channel_compare(
    old: hikari.PermissibleGuildChannel | None,
    new: hikari.PermissibleGuildChannel,
    now: datetime,
) -> str:
    """Сравнивает изменения двух каналов."""
    if old is None:
        return channel_info(new, now)

    status: list[str] = []
    items = (
        ("name", old.name, new.name),
        ("type", old.type, new.type),
        ("position", old.position, new.position),
        ("nsfw", old.is_nsfw, new.is_nsfw),
    )

    for name, old_attr, new_attr in items:
        if old_attr != new_attr:
            status.append(f"{name}: `{old_attr}` -> `{new_attr}`")
        else:
            status.append(f"{name}: `{new_attr}`")

    status.append(f"Создан: {_format_time(new.created_at, now)}")
    return "\n".join(status)


@plugin.listen(hikari.GuildChannelCreateEvent)
@plugin.inject_dependencies()
async def on_channel_create(
    event: hikari.GuildChannelCreateEvent, config: LoggerConfig = arc.inject()
) -> None:
    """при создании нового канала."""
    emb = hikari.Embed(
        title="📁 Channel create",
        description=channel_info(event.channel),
        color=_COLOR_CREATE,
        timestamp=datetime.now(UTC),
    )

    guild = await _get_guild(event.guild_id)
    emb.set_author(name=guild.name, icon=guild.make_icon_url())
    emb.add_field("Channel", event.channel.mention, inline=True)
    await config.send(emb)


@plugin.listen(hikari.GuildChannelDeleteEvent)
@plugin.inject_dependencies()
async def on_channel_delete(
    event: hikari.GuildChannelDeleteEvent, config: LoggerConfig = arc.inject()
) -> None:
    """При удалении канала."""
    now = datetime.now(tz=UTC)
    emb = hikari.Embed(
        title="📁 Channel delete",
        description=channel_info(event.channel, now),
        color=_COLOR_DELETE,
        timestamp=now,
    )

    guild = await _get_guild(event.guild_id)
    emb.set_author(name=guild.name, icon=guild.make_icon_url())
    emb.add_field("Channel", event.channel.mention, inline=True)
    await config.send(emb)


@plugin.listen(hikari.GuildChannelUpdateEvent)
@plugin.inject_dependencies()
async def on_channel_update(
    event: hikari.GuildChannelUpdateEvent, config: LoggerConfig = arc.inject()
) -> None:
    """при создании новой роли."""
    now = datetime.now(tz=UTC)
    emb = hikari.Embed(
        title="📁 Channel update",
        description=channel_compare(event.old_channel, event.channel, now),
        color=_COLOR_UPDATE,
        timestamp=now,
    )

    guild = await _get_guild(event.guild_id)
    emb.set_author(name=guild.name, icon=guild.make_icon_url())
    emb.add_field("Channel", event.channel.mention, inline=True)
    await plugin.client.rest.create_message(config.channel_id, emb)


@plugin.listen(hikari.GuildPinsUpdateEvent)
@plugin.inject_dependencies()
async def on_pins_update(
    event: hikari.GuildPinsUpdateEvent, config: LoggerConfig = arc.inject()
) -> None:
    """Когда в канале прикрепляется/открепляется сообщение."""
    now = datetime.now(tz=UTC)
    if event.last_pin_timestamp is not None:
        status = f"Last pin: {_format_time(event.last_pin_timestamp, now)}"
    else:
        status = "No pins in channel"

    emb = hikari.Embed(
        title="📌 Pins update",
        description=status,
        color=_COLOR_UPDATE,
        timestamp=now,
    )

    guild = await _get_guild(event.guild_id)
    emb.set_author(name=guild.name, icon=guild.make_icon_url())
    emb.add_field("Channel", _get_channel(event.channel_id), inline=True)
    await plugin.client.rest.create_message(config.channel_id, emb)


# Отслеживание веток
# ==================


def thread_info(thread: hikari.GuildThreadChannel, now: datetime) -> str:
    """Краткая информация о созданной ветке."""
    status: list[str] = []

    locked = " 🔒" if thread.is_locked else ""
    status.append(f"`{thread.type}` {thread.name}{locked}")
    status.append(f"~members `{thread.approximate_member_count}`")
    status.append(f"~messages `{thread.approximate_message_count}`")
    status.append(f"Owner id: `{thread.owner_id}`")
    status.append(f"Auto archive: {thread.auto_archive_duration}")
    status.append(f"Rate limit: {thread.rate_limit_per_user}")

    if thread.thread_created_at is not None:
        status.append(f"Created: {_format_time(thread.thread_created_at, now)}")

    if thread.last_pin_timestamp is not None:
        status.append(
            f"Last pin: {_format_time(thread.last_pin_timestamp, now)}"
        )

    if thread.is_archived:
        status.append(
            f"Archived: {_format_time(thread.archive_timestamp, now)}"
        )

    return "\n".join(status)


def thread_compare(
    old: hikari.GuildThreadChannel | None,
    new: hikari.GuildThreadChannel,
    now: datetime,
) -> str:
    """Сравнивает изменения двух веток."""
    if old is None:
        return thread_info(new, now)

    status: list[str] = []
    items = (
        ("Name", old.name, new.name),
        ("Type", old.type, new.type),
        ("Locked", old.is_locked, new.is_locked),
        (
            "~Members",
            old.approximate_member_count,
            new.approximate_member_count,
        ),
        (
            "~Messages",
            old.approximate_message_count,
            new.approximate_message_count,
        ),
        ("Owner", old.owner_id, new.owner_id),
        (
            "Auto archive",
            old.auto_archive_duration,
            new.auto_archive_duration,
        ),
        (
            "Rate limit",
            old.rate_limit_per_user,
            new.rate_limit_per_user,
        ),
    )

    for name, old_attr, new_attr in items:
        if old_attr != new_attr:
            status.append(f"{name}: `{old_attr}` -> `{new_attr}`")
        else:
            status.append(f"{name}: `{new_attr}`")

    if new.thread_created_at is not None:
        status.append(f"Created: `{_format_time(new.thread_created_at, now)}`")

    # Сравнение времени последнего закрепления
    if old.last_pin_timestamp != new.last_pin_timestamp:
        last_pin_old = (
            _format_time(old.last_pin_timestamp, now)
            if old.last_pin_timestamp
            else "?"
        )
        last_pin_new = (
            _format_time(new.last_pin_timestamp, now)
            if new.last_pin_timestamp
            else "?"
        )
        status.append(f"Last pin: `{last_pin_old}` -> `{last_pin_new}`")
    elif new.last_pin_timestamp is not None:
        status.append(
            f"Last pin: `{_format_time(new.last_pin_timestamp, now)}`"
        )

    # Сравнение статуса архивирования
    if old.is_archived != new.is_archived:
        status.append(f"Archived: `{old.is_archived}` -> `{new.is_archived}`")
    elif new.is_archived:
        status.append("Archived")

    return "\n".join(status)


@plugin.listen(hikari.GuildThreadCreateEvent)
@plugin.inject_dependencies()
async def on_thread_create(
    event: hikari.GuildThreadCreateEvent, config: LoggerConfig = arc.inject()
) -> None:
    """при создании новой ветки."""
    now = datetime.now(UTC)
    emb = hikari.Embed(
        title="🌱 Thread create",
        description=thread_info(event.thread, now),
        color=_COLOR_CREATE,
        timestamp=now,
    )

    guild = await _get_guild(event.guild_id)
    emb.set_author(name=guild.name, icon=guild.make_icon_url())
    emb.add_field("Thread", event.thread.mention, inline=True)
    await config.send(emb)


@plugin.listen(hikari.GuildThreadDeleteEvent)
@plugin.inject_dependencies()
async def on_thread_delete(
    event: hikari.GuildThreadDeleteEvent, config: LoggerConfig = arc.inject()
) -> None:
    """При удалении канала."""
    now = datetime.now(tz=UTC)
    thread = plugin.client.cache.get_thread(event.thread_id)
    if thread is not None:
        status = thread_info(thread, now)
    else:
        status = f"`{event.type}` {event.thread_id}"

    emb = hikari.Embed(
        title="🌱 Thread delete",
        description=status,
        color=_COLOR_DELETE,
        timestamp=now,
    )

    guild = await _get_guild(event.guild_id)
    emb.set_author(name=guild.name, icon=guild.make_icon_url())
    await config.send(emb)


@plugin.listen(hikari.GuildThreadUpdateEvent)
@plugin.inject_dependencies()
async def on_thread_update(
    event: hikari.GuildThreadUpdateEvent, config: LoggerConfig = arc.inject()
) -> None:
    """Когда обновляются данные ветки."""
    now = datetime.now(tz=UTC)
    emb = hikari.Embed(
        title="🌱 Thread update",
        description=thread_compare(event.old_thread, event.thread, now),
        color=_COLOR_UPDATE,
        timestamp=now,
    )

    guild = await _get_guild(event.guild_id)
    emb.set_author(name=guild.name, icon=guild.make_icon_url())
    emb.add_field("Thread", event.thread.mention, inline=True)
    await plugin.client.rest.create_message(config.channel_id, emb)


# Отслеживание ссылок-приглашений
# ===============================


def invite_info(invite: hikari.InviteWithMetadata, now: datetime) -> str:
    """Информация о ссылке-приглашении."""
    temporary = " ⏳" if invite.is_temporary else ""
    status = [
        f"Code: `{invite.code}`{temporary}",
        f"Uses: `{invite.uses}/{invite.max_uses or '?'}`",
        f"Created: {_format_time(invite.created_at, now)}",
    ]

    if invite.expires_at is not None:
        expired_delta = int((invite.expires_at - now).total_seconds())
        status.append(f"Expired: {_format_duration(expired_delta)}")

    if invite.max_age is not None:
        status.append(f"Max age: {invite.max_age}")

    return "\n".join(status)


@plugin.listen(hikari.InviteCreateEvent)
@plugin.inject_dependencies()
async def on_invite_create(
    event: hikari.InviteCreateEvent, config: LoggerConfig = arc.inject()
) -> None:
    """Когда создаётся новая ссылка-приглашение на сервер.."""
    now = datetime.now(tz=UTC)
    emb = hikari.Embed(
        title="📎 Invite create",
        description=invite_info(event.invite, now),
        color=_COLOR_CREATE,
        timestamp=now,
    )

    inviter = event.invite.inviter
    if inviter is not None:
        emb.set_author(
            name=inviter.display_name or inviter.global_name,
            icon=inviter.make_avatar_url(),
        )

    guild = event.invite.guild or await _get_guild(event.guild_id)
    emb.set_thumbnail(guild.make_icon_url())
    emb.add_field("Guild", guild.name, inline=True)
    emb.add_field("Channel", _get_channel(event.channel_id), inline=True)
    await plugin.client.rest.create_message(config.channel_id, emb)


@plugin.listen(hikari.InviteDeleteEvent)
@plugin.inject_dependencies()
async def on_invite_delete(
    event: hikari.InviteDeleteEvent, config: LoggerConfig = arc.inject()
) -> None:
    """Когда удаляется ссылка-приглашение на сервер.."""
    now = datetime.now(tz=UTC)
    invite = event.old_invite
    if invite is not None:
        guild = invite.guild or await _get_guild(event.guild_id)
        status = invite_info(invite, now)
        inviter = invite.inviter
    else:
        guild = await _get_guild(event.guild_id)
        status = f"Code: `{event.code}`"
        inviter = None

    emb = hikari.Embed(
        title="📎 Invite delete",
        description=status,
        color=_COLOR_DELETE,
        timestamp=now,
    )

    if inviter is not None:
        emb.set_author(
            name=inviter.display_name or inviter.global_name,
            icon=inviter.make_avatar_url(),
        )

    emb.set_thumbnail(guild.make_icon_url())
    emb.add_field("Guild", guild.name, inline=True)
    emb.add_field("Channel", _get_channel(event.channel_id), inline=True)
    await plugin.client.rest.create_message(config.channel_id, emb)


# Отслеживание webhook
# ====================


@plugin.listen(hikari.WebhookUpdateEvent)
@plugin.inject_dependencies()
async def on_webhook_update(
    event: hikari.WebhookUpdateEvent, config: LoggerConfig = arc.inject()
) -> None:
    """Когда обновляются данные webhook."""
    now = datetime.now(tz=UTC)
    emb = hikari.Embed(
        title="📻 Webhook update",
        description=f"Channel: {_get_channel(event.channel_id)}",
        color=_COLOR_UPDATE,
        timestamp=now,
    )

    guild = await _get_guild(event.guild_id)
    emb.set_author(name=guild.name, icon=guild.make_icon_url())

    webhooks = await event.fetch_channel_webhooks()
    for hook in webhooks:
        emb.add_field(
            hook.name,
            f"`{hook.type}` {_format_time(hook.created_at, now)}\n",
        )

    await plugin.client.rest.create_message(config.channel_id, emb)


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
    new_channel = _get_channel(new.channel_id)
    if old.channel_id == new.channel_id:
        status.append(f"Channel: {new_channel}")
    else:
        updates.append(f"{_get_channel(old.channel_id)} -> {new_channel}")

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
