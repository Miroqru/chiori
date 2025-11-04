"""Расчёт активности в голосовом канале.

Дополнительный модуль для active levels, отвечающий за более точную выдачу
опыта в голосовом канале.
Опыт выдаётся за тип активности в канале и количество участников.

Version: v1.3 (8)
Author: Milinuri Nirvalen
"""

from dataclasses import dataclass
from time import time

import arc
import hikari
from loguru import logger

from chioricord.client import ChioClient, ChioContext
from chioricord.plugin import ChioPlugin
from libs import voice_events
from libs.active_levels import ActiveTable, UserActive

plugin = ChioPlugin("Voice active")


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


def format_duration(minutes: int) -> str:
    """Преобразует количество секунд в более точное время."""
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    if days > 0:
        return f"{days} д. {hours:02d} ч. {minutes:02d} м."
    return f"{hours:02d} ч. {minutes:02d} м."


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
        return self.users.pop(user_id)


def _voice_stats(
    user: hikari.Member, voice: UserVoice, active: UserActive
) -> hikari.Embed:
    duration = (int(time()) - voice.start) // 60
    to_next_level = format_duration(
        (active.count_xp() - active.xp - voice.xp) // 5
    )

    emb = hikari.Embed(
        title="😺 Голосовая активность",
        description=(f"{user.display_name} Благодарим вас за участие."),
        color=hikari.Color(0xFFFF99),
    )
    emb.add_field("Мурлыкали", format_duration(duration), inline=True)
    emb.add_field("Опыт", f"{voice.xp * 5}✨", inline=True)
    emb.add_field("До повышения", to_next_level, inline=True)
    emb.add_field(
        "Подсказка",
        (
            "- Количество опыта зависит от вида активности.\n"
            "- Опыт начисляется после вашего выхода из звонка."
        ),
    )

    emb.set_thumbnail(user.make_avatar_url())
    return emb


@plugin.listen(voice_events.UserStartVoice)
@plugin.inject_dependencies()
async def on_join_voice(
    event: voice_events.UserStartVoice,
    active: ActiveTable = arc.inject(),
    timer: VoiceTimer = arc.inject(),
) -> None:
    """Добавляет участника в таймер."""
    timer.start(event.state.user_id)


@plugin.listen(voice_events.UserUpdateVoice)
@plugin.inject_dependencies()
async def on_voice_update(
    event: voice_events.UserUpdateVoice,
    active: ActiveTable = arc.inject(),
    timer: VoiceTimer = arc.inject(),
) -> None:
    """Добавляет участника в таймер."""
    if event.old_state is None:
        return

    timer.tick(event.state.user_id, count_modifier(event.old_state))


@plugin.listen(voice_events.UserEndVoice)
@plugin.inject_dependencies()
async def on_leave_voice(
    event: voice_events.UserEndVoice,
    active: ActiveTable = arc.inject(),
    timer: VoiceTimer = arc.inject(),
) -> None:
    """Отслеживаем активность в голосовом канале."""
    timer.tick(event.state.user_id, count_modifier(event.state))
    user = timer.stop(event.state.user_id)
    duration = (int(time()) - user.start) // 60

    if event.state.member is None:
        return

    if user.xp > 0:
        await active.add_voice(event.state.user_id, duration, user.xp)

    await plugin.client.rest.create_message(
        event.channel_id,
        _voice_stats(
            event.state.member,
            user,
            await active.get_or_default(event.state.user_id),
        ),
    )


@plugin.include
@arc.slash_command("voice", description="Активность в голосовом канале.")
async def voice_active(
    ctx: ChioContext,
    user: arc.Option[
        hikari.Member | None, arc.MemberParams("Для какого пользователя.")
    ] = None,
    at: ActiveTable = arc.inject(),
    timer: VoiceTimer = arc.inject(),
) -> None:
    """Активность пользователя в голосовом канале."""
    user = user or ctx.member
    if user is None:
        raise ValueError("Where member")

    active = await at.get_or_default(user.id)
    now = int(time())
    user_voice = timer.users.get(user.id, UserVoice(now, now, 0))
    emb = _voice_stats(user, user_voice, active)
    await ctx.respond(emb)


@plugin.listen(arc.StoppingEvent)
@plugin.inject_dependencies
async def clear_voice_state(
    event: arc.StoppingEvent[ChioClient],
    active: ActiveTable = arc.inject(),
    timer: VoiceTimer = arc.inject(),
) -> None:
    """Время сохранять голосовую активность пользователей."""
    logger.info("Save active time")
    now = int(time())
    for user_id, voice in timer.users.items():
        logger.info("Remove {} from listener", user_id)
        duration = round((now - voice.start) / 60)
        await active.add_voice(user_id, duration, voice.xp)


@arc.loader
def loader(client: ChioClient) -> None:
    """Actions on plugin load."""
    client.set_type_dependency(VoiceTimer, VoiceTimer())
    client.add_plugin(plugin)
