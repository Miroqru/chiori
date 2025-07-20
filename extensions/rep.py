"""карма пользователей.

Плагин для примера использование базы данных.

> [!tip] Шаблонное расширение.
> Вы Легко можете начать писать своё расширение для Чиори,
> взяв за основу исходный код данного расширения.

Предоставляет
-------------

- /rep [member] - Репутация пользователя.
- /rep_top - Таблица лидеров по репутации.
- /respect - Оказать уважение пользователю.
- /disrespect - Оказать неуважение к пользователю.

Version: v1.0.1 (10)
Author: Milinuri Nirvalen
"""

from datetime import datetime

import arc
import hikari

from chioricord.db import ChioDB
from libs.rep import ReputationTable, UserReputation

plugin = arc.GatewayPlugin("Reputation")

_COLOR_SUCCESS = hikari.Color(0x66FFCC)
_COLOR_MAIN = hikari.Color(0xFFCC77)
_COLOR_ERROR = hikari.Color(0xFF77CC)


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
        seconds = int(now.timestamp() - time.timestamp())
        tf += f" ({_format_duration(seconds)})"
    return tf


def _user_stats(rep: UserReputation, pos: str) -> str:
    return (
        f"**Репутация**: {rep.reputation} (+{rep.positive} / -{rep.negative})\n"
        f"Карма: {rep.karma}%\n"
        f"Место в рейтинге: {pos}"
    )


# определение команд
# ==================


@plugin.include
@arc.slash_command("rep", description="Репутация пользователя.")
async def user_reputation(
    ctx: arc.GatewayContext,
    user: arc.Option[  # type: ignore
        hikari.User | None, arc.UserParams("Чью репутацию посмотреть")
    ] = None,
    table: ReputationTable = arc.inject(),
) -> None:
    """Просмотре репутации пользователя."""
    now = datetime.now()

    if user is None:
        user = ctx.user
    rep = await table.get_or_create(user.id)
    pos = _pretty_pos(await table.get_position(user.id))
    emb = hikari.Embed(
        title=f"✨ Репутация {user.display_name}",
        description=_user_stats(rep, pos),
        color=_COLOR_MAIN,
    )
    emb.set_thumbnail(user.make_avatar_url())
    if now < rep.next_rep:
        emb.add_field("Перезарядка", _format_time(rep.next_rep, now))
    emb.add_field(
        "Подсказка",
        (
            "`/respect <@member>`: Выказать уважение участнику.\n"
            "`/disrespect <@member>`: Выказать неуважение участнику.\n"
        ),
    )
    await ctx.respond(emb)


@plugin.include
@arc.slash_command("respect", description="Оказать уважение пользователя.")
async def add_reputation(
    ctx: arc.GatewayContext,
    user: arc.Option[  # type: ignore
        hikari.User, arc.UserParams("Кому оказать уважение")
    ],
    table: ReputationTable = arc.inject(),
) -> None:
    """Выказать уважение пользователю."""
    now = datetime.now()
    if ctx.user.id == user.id:
        emb = hikari.Embed(
            title="💦 Минуточку",
            description="Вы пытаетесь добавить себе репутацию?",
            color=_COLOR_ERROR,
            timestamp=now,
        )
        await ctx.respond(emb)
        return

    my_rep = await table.get_or_create(ctx.user.id)
    if now > my_rep.next_rep:
        rep = await table.add_positive(user.id)
        pos = _pretty_pos(await table.get_position(user.id))
        emb = hikari.Embed(
            title="✨ Репутация",
            description=(
                f"{ctx.user.mention} оказывает уважение {user.mention}🎉\n\n"
                f"{_user_stats(rep, pos)}"
            ),
            color=_COLOR_SUCCESS,
        )
        await table.bump_cooldown(ctx.user.id)
    else:
        emb = hikari.Embed(
            title="💦 Минуточку",
            description="Перезарядка ещё не прошла?",
            color=_COLOR_ERROR,
        )
        emb.add_field("Перезарядка", _format_time(my_rep.next_rep, now))
    await ctx.respond(emb)


@plugin.include
@arc.slash_command("disrespect", description="Оказать неуважение пользователя.")
async def remove_reputation(
    ctx: arc.GatewayContext,
    user: arc.Option[  # type: ignore
        hikari.User, arc.UserParams("Кому оказать неуважение")
    ],
    table: ReputationTable = arc.inject(),
) -> None:
    """Выказать уважение пользователю."""
    now = datetime.now()
    if ctx.user.id == user.id:
        emb = hikari.Embed(
            title="💦 Минуточку",
            description="Вы пытаетесь убавить себе репутацию?",
            color=_COLOR_ERROR,
        )
        await ctx.respond(emb)
        return

    my_rep = await table.get_or_create(ctx.user.id)
    if now > my_rep.next_rep:
        rep = await table.add_negative(user.id)
        pos = _pretty_pos(await table.get_position(user.id))
        emb = hikari.Embed(
            title="✨ Репутация",
            description=(
                f"{ctx.user.mention} оказывает неуважение {user.mention}🎉\n\n"
                f"{_user_stats(rep, pos)}"
            ),
            color=_COLOR_MAIN,
        )
        await table.bump_cooldown(ctx.user.id)
    else:
        emb = hikari.Embed(
            title="💦 Минуточку",
            description="Перезарядка ещё не прошла?",
            color=_COLOR_ERROR,
        )
        emb.add_field("Перезарядка", _format_time(my_rep.next_rep, now))
    await ctx.respond(emb)


@plugin.include
@arc.slash_command("rep_top", description="Таблица лидеров по репутации.")
async def reputation_top(
    ctx: arc.GatewayContext,
    table: ReputationTable = arc.inject(),
) -> None:
    """Таблица лидеров по сообщениям."""
    leaders = await table.get_leaders("positive")
    leaderboard: list[str] = []
    for i, rep in enumerate(leaders):
        user = ctx.client.cache.get_user(rep.user_id)
        if user is not None:
            name = user.display_name
        else:
            user = await ctx.client.rest.fetch_user(rep.user_id)
            name = user.display_name

        points = f"✨{rep.positive} ({rep.karma}%)"
        leaderboard.append(f"{_pretty_pos(i + 1)}: **{name}**: {points}")

    emb = hikari.Embed(
        title="Таблица лидеров по репутации",
        description="\n".join(leaderboard),
        color=_COLOR_MAIN,
    )

    my_pos = _pretty_pos(await table.get_position(ctx.user.id))
    my_rep = await table.get_or_create(ctx.user.id)
    points = f"✨{my_rep.positive} ({my_rep.karma}%)"
    emb.add_field("Моя позиция", f"{my_pos}: {ctx.user.display_name} {points}")
    await ctx.respond(emb)


# Загрузчики и выгрузчики плагина
# ===============================


@arc.loader
def loader(client: arc.GatewayClient) -> None:
    """Действия при загрузке плагина."""
    client.add_plugin(plugin)
    db = client.get_type_dependency(ChioDB)
    db.register(ReputationTable)


@arc.unloader
def unloader(client: arc.GatewayClient) -> None:
    """Действия при выгрузке плагина."""
    client.remove_plugin(plugin)
