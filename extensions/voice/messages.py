"""Оповещения о голосовой активности.

Для начала это пример использования голосовых событий.
А потом, вы все будете знать что происходило в канале.
Разве не весело.

Version: v1.1 (3)
Author: Milinuri Nirvalen
"""

from time import time

import arc
import hikari

from chioricord.client import ChioClient
from chioricord.plugin import ChioPlugin
from libs import voice_events

plugin = ChioPlugin("Voice messages")


def format_duration(minutes: int) -> str:
    """Преобразует количество секунд в более точное время."""
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    if days > 0:
        return f"{days} д. {hours:02d} ч. {minutes:02d} м."
    return f"{hours:02d} ч. {minutes:02d} м."


def _state_flags(state: hikari.VoiceState) -> str:
    flags: list[str] = []

    if state.is_self_muted:
        flags.append("без микро")
    if state.is_self_deafened:
        flags.append("спрятался")
    if state.is_guild_muted:
        flags.append("отрезали микро")
    if state.is_guild_deafened:
        flags.append("заглушили")
    if state.is_streaming:
        flags.append("транслирует")
    if state.is_suppressed:
        flags.append("подавлен")
    if state.is_video_enabled:
        flags.append("с камерой")
    if state.requested_to_speak_at is not None:
        flags.append(f"Хочет сказать {state.requested_to_speak_at}")

    return ", ".join(flags)


def _state_compare(old: hikari.VoiceState, new: hikari.VoiceState) -> str:
    """Сопоставляет информацию о двух состояниях."""
    flags = [
        (
            old.is_self_muted,
            new.is_self_muted,
            "включил микрофон",
            "отключил микрофон",
        ),
        (
            old.is_self_deafened,
            new.is_self_deafened,
            "включил звук",
            "отключил звук",
        ),
        (
            old.is_guild_muted,
            new.is_guild_muted,
            "отрезали микро",
            "вернули микро",
        ),
        (
            old.is_guild_deafened,
            new.is_guild_deafened,
            "отрезали звук",
            "вернули звук",
        ),
        (
            old.is_streaming,
            new.is_streaming,
            "начал трансляцию",
            "закончил трансляцию",
        ),
        (
            old.is_suppressed,
            new.is_suppressed,
            "откис",
            "вкис",
        ),
        (
            old.is_video_enabled,
            new.is_video_enabled,
            "включил камеру",
            "отключил камеру",
        ),
    ]
    changes: list[str] = []
    for old_flag, new_flag, on_text, off_text in flags:
        if old_flag == new_flag:
            continue
        elif new_flag:
            changes.append(off_text)
        else:
            changes.append(on_text)

    return ", ".join(changes)


# События пользователя
# ====================


def _set_author(emb: hikari.Embed, member: hikari.Member | None) -> None:
    if member is None:
        return
    emb.set_author(name=member.display_name, icon=member.make_avatar_url())


@plugin.listen(voice_events.UserStartVoice)
async def user_start_voice(event: voice_events.UserStartVoice) -> None:
    """Когда пользователь заходит в голосовой канал."""
    emb = hikari.Embed(
        title="☕ Добро пожаловать!",
        description=f"Пробирается к нам {_state_flags(event.state)}",
        color=hikari.Color(0xCCFF99),
    )
    _set_author(emb, event.state.member)
    await event.client.rest.create_message(event.channel_id, emb)


@plugin.listen(voice_events.UserUpdateVoice)
async def user_update_voice(event: voice_events.UserUpdateVoice) -> None:
    """Когда пользователь обновляет обновляет статус голосового канала."""
    if event.old_state is None:
        changes = _state_flags(event.state)
    else:
        changes = _state_compare(event.old_state, event.state)
    duration = (int(time()) - event.start_time) // 60
    emb = hikari.Embed(
        title="👀 Суета",
        description=(
            f"Участник **{changes}**.\n"
            f"Мурчит уже `{format_duration(duration)}`\n"
        ),
        color=hikari.Color(0xCC99FF),
    )
    _set_author(emb, event.state.member)
    await event.client.rest.create_message(event.channel_id, emb)


@plugin.listen(voice_events.UserChangeVoice)
async def user_change_voice(event: voice_events.UserChangeVoice) -> None:
    """Когда пользователь прыгает в другой канал."""
    emb = hikari.Embed(
        title="☕ Приветик!",
        description=(
            f"Пробирается из другого канала. {_state_flags(event.state)}"
        ),
        color=hikari.Color(0x99FFCC),
    )
    _set_author(emb, event.state.member)
    await event.client.rest.create_message(event.channel_id, emb)


@plugin.listen(voice_events.UserEndVoice)
async def user_end_voice(event: voice_events.UserEndVoice) -> None:
    """Когда пользователь покидает голосовой канал."""
    duration = (int(time()) - event.start_time) // 60
    emb = hikari.Embed(
        title="👋 Ещё увидимся",
        description=(
            "Рады были с вами пообщаться.\n"
            f"Вы мурлыкали с нами `{format_duration(duration)}`"
        ),
        color=hikari.Color(0xFFCC99),
    )
    _set_author(emb, event.state.member)
    await event.client.rest.create_message(event.channel_id, emb)


# События звонка
# ==============


@plugin.listen(voice_events.GuildStartVoice)
async def guild_start_voice(event: voice_events.GuildStartVoice) -> None:
    """Когда начинается звонок в голосовом канале."""
    emb = hikari.Embed(
        title="📞 Начался звонок",
        description="Желаю вам приятно провести время! ❤️",
        color=hikari.Color(0x99FFCC),
    )
    await event.client.rest.create_message(event.channel_id, emb)


@plugin.listen(voice_events.GuildEndVoice)
async def guild_end_voice(event: voice_events.GuildEndVoice) -> None:
    """Когда завершается звонок в голосовом канале."""
    duration = (int(time()) - event.state.start_time) // 60
    emb = hikari.Embed(
        title="📞 Звонок завершился",
        description=(
            "Это было великолепно!\n"
            f"Вы мурчали `{format_duration(duration)}`.\n"
            "Буду с нетерпением ждать вашего возвращения. ❤️"
        ),
        color=hikari.Color(0xFF99CC),
    )
    await event.client.rest.create_message(event.channel_id, emb)


# Загрузка плагина
# ================


@arc.loader
def loader(client: ChioClient) -> None:
    """Actions on plugin load."""
    client.add_plugin(plugin)
