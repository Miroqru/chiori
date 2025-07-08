"""Активность участников.

Отслеживает активность участников на сервере.
Сколько они написали сообщений, сколько провели в голосовом канале.

Предоставляет
-------------

- /top [category]: Таблица лидеров по активности на сервере.
- /active: Активность участника на сервере.

Version: v1.7 (18)
Author: Milinuri Nirvalen
"""

from dataclasses import dataclass
from time import time

import arc
import hikari
from loguru import logger

from chioricord.config import PluginConfig, PluginConfigManager
from chioricord.db import ChioDatabase
from libs.active_levels import ActiveTable, LevelUpEvent, UserActive

plugin = arc.GatewayPlugin("Active levels")


@dataclass(slots=True)
class UserVoice:
    """Состояние пользователя в голосовом канале."""

    start: int
    start_buffer: int
    xp_buffer: int
    modifier: float


voice_start_times: dict[int, UserVoice] = {}


class LevelsConfig(PluginConfig):
    """Настройки для журнала событий."""

    channel_id: int
    """
    ID канала для отправки событий.
    Именно сюда будут отправляться уведомлений о поднятии уровня.
    """

    send_notify_after: int = 10
    """
    Через сколько минут в голосовом канале отправлять сообщение с поздравление
    за проведённое время.
    """


def format_duration(minutes: int) -> str:
    """Преобразует количество секунд в более точное время."""
    logger.debug(minutes)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    if days > 0:
        return f"{days} д. {hours:02d} ч. {minutes:02d} м."
    return f"{hours:02d} ч. {minutes:02d} м."


def count_modifier(state: hikari.VoiceState) -> float:
    """Высчитывает модификатор на основе."""
    if state.is_guild_deafened or state.is_self_deafened or state.is_suppressed:
        return 0
    base = 1.0

    if state.is_streaming:
        base += 1

    if state.is_guild_muted or state.is_guild_muted:
        base -= 0.5

    if state.is_video_enabled:
        base += 0.5

    return base


def _pretty_pos(pos: int | None) -> str:
    if pos is None:
        return "0"
    if pos == 1:
        return "🥇"
    if pos == 2:  # noqa: PLR2004
        return "🥈"
    if pos == 3:  # noqa: PLR2004
        return "🥉"
    return str(pos)


def _get_points(active: UserActive, group: str) -> str:
    if group == "level":
        target_xp = active.count_xp()
        return f"`{active.level}` уровень `{active.xp}/{target_xp}` опыта."
    if group == "voice":
        return f"`{format_duration(active.voice)}`"
    if group == "bumps":
        return f"`{active.bumps}` бампов"
    return f"`{active.words}` слов / `{active.messages}` сообщений"


def _voice_stats(
    user: hikari.User, duration: int, xp: int, active: UserActive
) -> hikari.Embed:
    to_next_level = format_duration((active.count_xp() - active.xp) // 5)

    emb = hikari.Embed(
        title="😺 Голосовая активность",
        description=(
            f"{user.display_name}, вы мурлыкали в канале "
            f"`{format_duration(duration)}`\n"
            f"и получаете за это {xp * 5}✨\n\n"
            f"**До нового уровня**: `{to_next_level}`"
        ),
        color=hikari.Color(0xFF66B2),
    )
    emb.set_thumbnail(user.make_avatar_url(file_format="PNG"))
    return emb


# Отслеживание событий
# ====================


@plugin.listen(hikari.GuildMessageCreateEvent)
@plugin.inject_dependencies()
async def on_message(
    event: hikari.GuildMessageCreateEvent, active: ActiveTable = arc.inject()
) -> None:
    """Добавляем опыт за текстовые сообщения."""
    if event.author.is_bot:
        return

    xp = len(event.message.attachments) * 5
    if event.content is not None:
        xp += len(event.content.split())

    await active.add_messages(event.author_id, xp)

    # # -> Message Bumps
    # if event.author.is_bot:
    #     embed = event.embeds[0]

    #     if embed.description and "Время реакции" in embed.description:
    #         if embed.author is None:
    #             return
    #         user_name = embed.author.name

    #         guild = event.get_guild()
    #         if guild is None:
    #             return

    #         members = guild.get_members()
    #         user = None

    #         for member in members:
    #             member = guild.get_member(member)
    #             if member is None:
    #                 continue
    #             if member.username == user_name:
    #                 user = member
    #                 break

    #         if user is None or user_name is None:
    #             return

    #         await update_bump_count(user.id, user_name)

    #         session = async_sessionmaker(
    #             database_manager.engine, expire_on_commit=True
    #         )
    #         async with session() as session:
    #             async with session.begin():
    #                 stmt = select(UserData.bump_count).where(
    #                     UserData.user_id == user.id
    #                 )
    #                 bump_count = await session.scalar(stmt)

    #         embed_success = hikari.Embed(
    #             description=f"Hey, {user.mention}, thank u!\n Your total bumps: `{bump_count}`",
    #             color=0x2B2D31,
    #         )
    #         channel = event.get_channel()
    #         if isinstance(channel, hikari.GuildTextChannel):
    #             await channel.send(embed=embed_success)


@plugin.listen(hikari.VoiceStateUpdateEvent)
@plugin.inject_dependencies()
async def on_voice_update(
    event: hikari.VoiceStateUpdateEvent,
    active: ActiveTable = arc.inject(),
    config: LevelsConfig = arc.inject(),
) -> None:
    """Отслеживаем активность в голосовом канале."""
    before = event.old_state
    after = event.state
    member = event.state.member

    if member is None or member.is_bot:
        return

    # Добавляет человека если его ещё нету
    # Может быть такое что человек зашёл раньше, чем запустился бот
    now = int(time())
    if member.id not in voice_start_times:
        logger.info("Add {} to listener", member.id)
        voice_start_times[member.id] = UserVoice(
            now, now, 0, count_modifier(after)
        )

    # Пользователь только зашёл в канал
    if before is None:
        return

    user_voice = voice_start_times[member.id]
    user_voice.xp_buffer += round(
        ((now - user_voice.start_buffer) / 60) * user_voice.modifier
    )
    user_voice.start_buffer = now
    user_voice.modifier = count_modifier(after)

    logger.debug("{}: {}", member.id, user_voice)

    # Когда человек покидает голосовой канал -> начисляем опыт.
    if after.channel_id is None and member.id in voice_start_times:
        logger.info("Remove {} from listener", member.id)
        duration = round((now - user_voice.start) / 60)
        voice_start_times.pop(member.id)
        if duration > 0:
            await active.add_voice(member.id, duration, user_voice.xp_buffer)

        if duration > config.send_notify_after:
            await plugin.client.rest.create_message(
                config.channel_id,
                _voice_stats(
                    member,
                    duration,
                    user_voice.xp_buffer,
                    await active.get_or_default(member.id),
                ),
            )


@plugin.listen(LevelUpEvent)
@plugin.inject_dependencies
async def on_level_up(
    event: LevelUpEvent,
    config: LevelsConfig = arc.inject(),
    at: ActiveTable = arc.inject(),
) -> None:
    """Когда пользователь повышает свой уровень."""
    user = event.client.cache.get_user(
        event.user_id
    ) or await event.client.rest.fetch_user(event.user_id)

    level_pos = _pretty_pos(await at.get_position("level", event.user_id))
    words_pos = _pretty_pos(await at.get_position("words", event.user_id))
    voice_pos = _pretty_pos(await at.get_position("voice", event.user_id))
    bumps_pos = _pretty_pos(await at.get_position("bumps", event.user_id))

    emb = hikari.Embed(
        title="Повышение уровня 🎉",
        description=(
            f"🌷 Дорогой {user.mention}.\n"
            f"поздравляем с повышением до {event.active.level} уровня.\n\n"
            f"**Место в рейтинге**: {level_pos}\n"
            f"**Опыт**: {event.active.xp} / {event.active.count_xp()}."
        ),
        color=hikari.Color(0xFF66B2),
    )
    emb.add_field(
        "Ваша статистика",
        (
            f"**Слов** {event.active.words} ({event.active.messages} сообщений\n"
            f"**Общался голосом**: `{format_duration(event.active.voice)}`\n"
            f"**Бампов**: {event.active.bumps}"
        ),
    )
    emb.add_field(
        "место в рейтинге",
        (
            f"{words_pos} - по словам\n"
            f"{voice_pos} - по голосу\n"
            f"{bumps_pos} - по бампам"
        ),
    )

    emb.set_thumbnail(user.make_avatar_url(file_format="PNG"))
    await event.client.rest.create_message(config.channel_id, emb)


# определение команд
# ==================


@plugin.include
@arc.slash_command("top", description="Таблица лидеров по активности.")
async def message_top(
    ctx: arc.GatewayContext,
    group: arc.Option[  # type: ignore
        str,
        arc.StrParams(
            "По какому критерию.",
            choices=["words", "level", "voice", "bumps"],
        ),
    ] = "level",
    at: ActiveTable = arc.inject(),
) -> None:
    """Таблица лидеров по сообщениям."""
    leaders = await at.get_top(group)

    header = "словам"
    if group == "level":
        header = "Уровню"
    elif group == "voice":
        header = "Голосу"
    elif group == "bumps":
        header = "Бампам"

    leaderboard = ""
    for i, (user_id, active) in enumerate(leaders):
        user = ctx.client.cache.get_user(user_id)
        if user is not None:
            name = user.display_name
        else:
            user = await ctx.client.rest.fetch_user(user_id)
            name = user.display_name

        points = _get_points(active, group)
        leaderboard += f"\n{_pretty_pos(i + 1)}: **{name}**: {points}"

    emb = hikari.Embed(
        title=f"Таблица лидеров по {header}",
        description=leaderboard,
        color=hikari.Color(0xFFCC99),
    )

    my_pos = _pretty_pos(await at.get_position(group, ctx.user.id))
    my_active = await at.get_or_default(ctx.user.id)
    points = _get_points(my_active, group)
    emb.add_field("Моя позиция", f"{my_pos}: {ctx.user.display_name} {points}")
    await ctx.respond(emb)


@plugin.include
@arc.slash_command("active", description="Активность пользователя.")
async def user_active(
    ctx: arc.GatewayContext,
    user: arc.Option[  # type: ignore
        hikari.User | None, arc.UserParams("Для какого пользователя.")
    ] = None,
    at: ActiveTable = arc.inject(),
) -> None:
    """Таблица лидеров по сообщениям."""
    if user is None:
        user = ctx.author

    active = await at.get_or_default(user.id)
    emb = hikari.Embed(
        title="Активность",
        description=(
            f"**Уровень**: {active.level} / 100\n"
            f"**Слов**: {active.words} ({active.messages} сообщений)\n"
            f"**В голосовом канале**: {format_duration(active.voice)}\n"
            f"**Бампов**: {active.bumps}\n"
        ),
        color=hikari.Color(0x5C991F),
    )

    target_xp = active.count_xp()
    pr = round((active.xp / target_xp) * 100, 2)
    emb.add_field("Опыт", f"{active.xp}/{target_xp} ({pr}%)")
    emb.set_thumbnail(user.make_avatar_url(file_format="PNG"))

    level_pos = _pretty_pos(await at.get_position("level", user.id))
    words_pos = _pretty_pos(await at.get_position("words", user.id))
    voice_pos = _pretty_pos(await at.get_position("voice", user.id))
    bumps_pos = _pretty_pos(await at.get_position("bumps", user.id))

    emb.add_field(
        "Место в рейтинге",
        (
            f"{level_pos} - по уровню.\n"
            f"{words_pos} - по словам.\n"
            f"{voice_pos} - по голосу.\n"
            f"{bumps_pos} - по бампам."
        ),
    )

    await ctx.respond(emb)


@plugin.include
@arc.slash_command("voice", description="Активность в голосовом канале.")
async def voice_active(
    ctx: arc.GatewayContext,
    user: arc.Option[  # type: ignore
        hikari.User | None, arc.UserParams("Для какого пользователя.")
    ] = None,
    at: ActiveTable = arc.inject(),
) -> None:
    """Активность пользователя в голосовом канале."""
    if user is None:
        user = ctx.author

    active = await at.get_or_default(user.id)
    now = int(time())
    user_voice = voice_start_times.get(user.id, UserVoice(now, 0, 0, 0))
    duration = round((now - user_voice.start) / 60)
    total_xp = (
        user_voice.xp_buffer
        + round((now - user_voice.start_buffer) / 60) * user_voice.modifier
    )

    emb = _voice_stats(user, duration, total_xp, active)
    emb.color = hikari.Color(0x5C991F)
    if user_voice.xp_buffer > 0:
        emb.add_field(
            "Подсказка",
            (
                "- Xp зависит от типа активности в голосовом канале.\n"
                "- Опыт начисляется после выхода из голосового канала."
            ),
        )
    await ctx.respond(emb)


# Загрузчики и выгрузчики плагина
# ===============================


@plugin.listen(arc.StartedEvent)
async def check_voice_state(event: arc.StartedEvent[arc.GatewayClient]) -> None:
    """Записывает участников в голосовые каналы."""
    states = event.client.cache.get_voice_states_view()
    now = int(time())
    for guild_states in states.values():
        for user_id, state in guild_states.items():
            logger.debug("Add {} to listener", user_id)
            voice_start_times[user_id] = UserVoice(
                now, now, 0, count_modifier(state)
            )


@plugin.listen(arc.StoppingEvent)
@plugin.inject_dependencies
async def clear_voice_state(
    event: arc.StoppingEvent[arc.GatewayClient],
    active: ActiveTable = arc.inject(),
    config: LevelsConfig = arc.inject(),
) -> None:
    """Время отключаться от баз данных, вместе с отключением бота."""
    logger.info("Close connect to active DB {}")

    now = int(time())
    for k, v in voice_start_times.items():
        logger.info("Remove {} from listener", k)
        duration = round((now - v.start) / 60)
        if duration > 0:
            await active.add_voice(k, duration, v.xp_buffer)

        user = event.client.cache.get_user(k)
        logger.debug("{} {} {}", user, k, duration)
        if user is not None and duration > config.send_notify_after:
            await plugin.client.rest.create_message(
                config.channel_id,
                _voice_stats(
                    user,
                    duration,
                    v.xp_buffer,
                    await active.get_or_default(k),
                ),
            )


@arc.loader
def loader(client: arc.GatewayClient) -> None:
    """Действия при загрузке плагина."""
    client.add_plugin(plugin)

    db = client.get_type_dependency(ChioDatabase)
    db.register("active", ActiveTable)

    cm = client.get_type_dependency(PluginConfigManager)
    cm.register("levels", LevelsConfig)


@arc.unloader
def unloader(client: arc.GatewayClient) -> None:
    """Действия при выгрузке плагина."""
    client.remove_plugin(plugin)
