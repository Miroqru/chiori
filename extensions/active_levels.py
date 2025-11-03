"""Активность участников.

Отслеживает активность участников на сервере.
Сколько они написали сообщений, сколько провели в голосовом канале.

Version: v1.9.1 (25)
Author: Milinuri Nirvalen
"""

# TODO: Приветствие в канале
# TODO: Прощание в канале
# TODO: Начало звонка
# TODO: Окончание звонка

from dataclasses import dataclass
from time import time

import arc
import hikari
from loguru import logger

from chioricord.api import PluginConfig
from chioricord.client import ChioClient, ChioContext
from chioricord.plugin import ChioPlugin
from libs.active_levels import ActiveTable, LevelUpEvent, UserActive

plugin = ChioPlugin("Active levels")


@dataclass(slots=True)
class UserVoice:
    """Состояние пользователя в голосовом канале."""

    start: int
    updated: int
    xp: int


class VoiceTimer:
    """Таймер голосового канала."""

    def __init__(self) -> None:
        self.users: dict[int, UserVoice] = {}

    def start(self, user_id: int) -> UserVoice:
        """Начинает отсчёт времени для пользователя."""
        logger.info("Add {} to timer", user_id)
        now = int(time())
        voice = UserVoice(now, now, 0)
        self.users[user_id] = voice
        return voice

    def tick(self, user_id: int, mod: float = 1) -> None:
        """Переключает новое состояние пользователя."""
        logger.debug("Update state for {}", user_id)
        user = self.users.get(user_id) or self.start(user_id)
        now = int(time())
        duration = (now - user.updated) // 60
        user.xp += round(duration * mod)
        user.updated = now
        self.users[user_id] = user

    def stop(self, user_id: int, mod: float = 1) -> UserVoice:
        """Заканчивает сеанс пользователя."""
        logger.info("Remove {} from timer", user_id)
        self.tick(user_id)
        return self.users.pop(user_id)


class LevelsConfig(PluginConfig, config="levels"):
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
    user: hikari.User, voice: UserVoice, active: UserActive
) -> hikari.Embed:
    duration = (int(time()) - voice.start) // 60
    to_next_level = format_duration(
        (active.count_xp() - active.xp - voice.xp) // 5
    )

    emb = hikari.Embed(
        title="😺 Голосовая активность",
        description=(
            f"{user.display_name}, вы мурлыкали в канале "
            f"`{format_duration(duration)}`\n"
            f"и получаете за это {voice.xp}✨\n\n"
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


@plugin.listen(hikari.VoiceStateUpdateEvent)
@plugin.inject_dependencies()
async def on_voice_update(
    event: hikari.VoiceStateUpdateEvent,
    active: ActiveTable = arc.inject(),
    config: LevelsConfig = arc.inject(),
    timer: VoiceTimer = arc.inject(),
) -> None:
    """Отслеживаем активность в голосовом канале."""
    before = event.old_state
    after = event.state
    member = event.state.member

    if member is None or member.is_bot:
        return

    if member.id not in timer.users:
        timer.start(member.id)

    if before is None:
        return

    timer.tick(member.id, count_modifier(before))
    if after.channel_id is None and member.id in timer.users:
        user = timer.stop(member.id)
        duration = (int(time()) - user.start) // 60

        if user.xp > 0:
            await active.add_voice(member.id, duration, user.xp)

        if duration > config.send_notify_after:
            await plugin.client.rest.create_message(
                config.channel_id,
                _voice_stats(
                    member,
                    user,
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
    ctx: ChioContext,
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
    for i, active in enumerate(leaders):
        user = ctx.client.cache.get_user(active.user_id)
        if user is not None:
            name = user.display_name
        else:
            user = await ctx.client.rest.fetch_user(active.user_id)
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
    ctx: ChioContext,
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
    ctx: ChioContext,
    user: arc.Option[  # type: ignore
        hikari.User | None, arc.UserParams("Для какого пользователя.")
    ] = None,
    at: ActiveTable = arc.inject(),
    timer: VoiceTimer = arc.inject(),
) -> None:
    """Активность пользователя в голосовом канале."""
    user = user or ctx.author
    active = await at.get_or_default(user.id)

    now = int(time())
    user_voice = timer.users.get(user.id, UserVoice(now, now, []))
    emb = _voice_stats(user, user_voice, active)
    emb.color = hikari.Color(0x5C991F)
    emb.add_field(
        "Подсказка",
        (
            "- Xp зависит от вида активности в голосовом канале.\n"
            "- Опыт начисляется после завершения вашего звонка."
        ),
    )
    await ctx.respond(emb)


# Загрузчики и выгрузчики плагина
# ===============================


@plugin.listen(arc.StartedEvent)
async def check_voice_state(event: arc.StartedEvent[ChioClient]) -> None:
    """Записывает участников в голосовые каналы."""
    timer = event.client.get_type_dependency(VoiceTimer)
    states = event.client.cache.get_voice_states_view()
    logger.debug(states)
    for guild_states in states.values():
        for user_id in guild_states.keys():
            timer.start(user_id)


@plugin.listen(arc.StoppingEvent)
@plugin.inject_dependencies
async def clear_voice_state(
    event: arc.StoppingEvent[ChioClient],
    active: ActiveTable = arc.inject(),
    config: LevelsConfig = arc.inject(),
    timer: VoiceTimer = arc.inject(),
) -> None:
    """Время отключаться от баз данных, вместе с отключением бота."""
    logger.info("Save active time")
    now = int(time())

    for user_id, voice in timer.users.items():
        logger.info("Remove {} from listener", user_id)
        duration = round((now - voice.start) / 60)
        await active.add_voice(user_id, duration, voice.xp)

        user = event.client.cache.get_user(user_id)
        if user is not None and duration > config.send_notify_after:
            await plugin.client.rest.create_message(
                config.channel_id,
                _voice_stats(user, voice, await active.get_or_default(user_id)),
            )


@arc.loader
def loader(client: ChioClient) -> None:
    """Действия при загрузке плагина."""
    client.set_type_dependency(VoiceTimer, VoiceTimer())
    plugin.set_config(LevelsConfig)
    plugin.add_table(ActiveTable)
    client.add_plugin(plugin)
