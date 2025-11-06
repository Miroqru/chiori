"""Активность участников.

Отслеживает активность участников на сервере.
Оповещает о получении нового уровня.
Отслеживает активность в текстовых каналах.
Для отслеживания голосовых каналов, есть отдельное расширение.

Version: v1.10 (27)
Author: Milinuri Nirvalen
"""

import arc
import hikari

from chioricord.api import PluginConfig
from chioricord.client import ChioClient, ChioContext
from chioricord.plugin import ChioPlugin
from libs.active_levels import ActiveTable, LevelUpEvent, UserActive

plugin = ChioPlugin("Active levels")


class LevelsConfig(PluginConfig, config="levels"):
    """Настройки для журнала событий."""

    channel_id: int
    """
    ID канала для отправки событий.
    Именно сюда будут отправляться уведомлений о поднятии уровня.
    """


def format_duration(minutes: int) -> str:
    """Преобразует количество секунд в более точное время."""
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    if days > 0:
        return f"{days} д. {hours:02d} ч. {minutes:02d} м."
    return f"{hours:02d} ч. {minutes:02d} м."


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

    if xp > 0:
        await active.add_messages(event.author_id, xp)


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


@arc.loader
def loader(client: ChioClient) -> None:
    """Действия при загрузке плагина."""
    plugin.set_config(LevelsConfig)
    plugin.add_table(ActiveTable)
    client.add_plugin(plugin)
