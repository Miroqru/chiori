"""Активность участников.

Отслеживает активность участников на сервере.
Сколько они написали сообщений, сколько провели в голосовом канале.

Предоставляет
-------------

- /top [category]: Таблица лидеров по активности на сервере.
- /active: Активность участника на сервере.

Version: v1.3 (10)
Author: Milinuri Nirvalen
"""

from dataclasses import dataclass
from time import time

import arc
import hikari
from loguru import logger

from chioricord.config import PluginConfig, PluginConfigManager
from chioricord.db import ChioDatabase
from libs.active_levels import ActiveTable, UserActive

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


def format_duration(minutes: int) -> str:
    """Преобразует количество секунд в более точное время."""
    logger.debug(minutes)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    return f"{days:02d} д. {hours:02d}:{minutes:02d}"


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
    event: hikari.VoiceStateUpdateEvent, active: ActiveTable = arc.inject()
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


@plugin.inject_dependencies
async def on_level_up(
    db: ChioDatabase,
    user_id: int,
    active: UserActive,
    config: LevelsConfig = arc.inject(),
) -> None:
    """Когда пользователь повышает свой уровень."""
    user = db.client.cache.get_user(user_id) or await db.client.rest.fetch_user(
        user_id
    )
    emb = hikari.Embed(
        title="Повышение уровня",
        description=f"{user.mention} повышает свой уровень до {active.level}",
        color=hikari.Color(0xFFCC99),
    )
    emb.set_thumbnail(user.make_avatar_url(file_format="PNG"))
    await db.client.rest.create_message(config.channel_id, emb)


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
    active: ActiveTable = arc.inject(),
) -> None:
    """Таблица лидеров по сообщениям."""
    leaders = await active.get_top(group)

    header = "словам"
    if group == "level":
        header = "Уровню"
    elif group == "voice":
        header = "Голосу"
    elif group == "bumps":
        header = "Бампам"

    leaderboard = ""
    for i, (user_id, user_active) in enumerate(leaders):
        user = ctx.client.cache.get_user(user_id)
        if user is not None:
            name = user.display_name
        else:
            user = await ctx.client.rest.fetch_user(user_id)
            name = user.display_name

        points = (
            f"`{user_active.words}` слов / `{user_active.messages}` сообщений"
        )
        if group == "level":
            target_xp = user_active.count_xp()
            points = f"`{user_active.level}` уровень `{user_active.xp}/{target_xp}` опыта."
        if group == "voice":
            points = f"`{format_duration(user_active.voice)}`"
        if group == "bumps":
            points = f"`{user_active.bumps}` бампов"

        leaderboard += f"\n{i + 1}. **{name}**: {points}"

    emb = hikari.Embed(
        title=f"Таблица лидеров по {header}",
        description=leaderboard,
        color=hikari.Color(0xFFCC99),
    )
    await ctx.respond(emb)


@plugin.include
@arc.slash_command("active", description="Активность пользователя.")
async def user_active(
    ctx: arc.GatewayContext,
    user: arc.Option[  # type: ignore
        hikari.User | None, arc.UserParams("Для какого пользователя.")
    ] = None,
    active: ActiveTable = arc.inject(),
) -> None:
    """Таблица лидеров по сообщениям."""
    if user is None:
        user = ctx.author

    user_active = await active.get_or_default(user.id)
    emb = hikari.Embed(
        title="Активность",
        description=(
            f"**Уровень:** {user_active.level} / 100\n"
            f"**Сообщений:** {user_active.messages}\n"
            f"**Слов:** {user_active.words}\n"
            f"**В голосовом канале:** {format_duration(user_active.voice)}\n"
            f"**Бампов:** {user_active.bumps}\n"
        ),
        color=user.accent_color,
    )

    target_xp = user_active.count_xp()
    pr = round((user_active.xp / target_xp) * 100, 2)
    emb.add_field("Опыт", f"{user_active.xp}/{target_xp} ({pr}%)")
    emb.set_thumbnail(user.make_avatar_url(file_format="PNG"))
    await ctx.respond(emb)


# Загрузчики и выгрузчики плагина
# ===============================


@plugin.listen(arc.events.StoppingEvent)
@plugin.inject_dependencies
async def disconnect(
    event: arc.events.StoppingEvent[arc.GatewayClient],
    active: ActiveTable = arc.inject(),
) -> None:
    """Время отключаться от баз данных, вместе с отключением бота."""
    logger.info("Close connect to active DB")

    now = int(time())
    for k, v in voice_start_times.items():
        logger.info("Remove {} from listener", k)
        duration = round((now - v) / 60)
        if duration > 0:
            await active.add_voice(k, duration)


@arc.loader
def loader(client: arc.GatewayClient) -> None:
    """Действия при загрузке плагина."""
    client.add_plugin(plugin)

    db = client.get_type_dependency(ChioDatabase)
    db.register("active", ActiveTable)
    active = client.get_type_dependency(ActiveTable)
    active.add_level_up_handler(on_level_up)

    cm = client.get_type_dependency(PluginConfigManager)
    cm.register("levels", LevelsConfig)


@arc.unloader
def unloader(client: arc.GatewayClient) -> None:
    """Действия при выгрузке плагина."""
    client.remove_plugin(plugin)
