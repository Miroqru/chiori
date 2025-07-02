"""Активность участников.

Отслеживает активность участников на сервере.
Сколько они написали сообщений, сколько провели в голосовом канале.

Предоставляет
-------------

- /top [category]: Таблица лидеров по активности на сервере.
- /active: Активность участника на сервере.

Version: v1.1 (7)
Author: Milinuri Nirvalen
"""

from pathlib import Path
from time import time

import arc
import hikari
from loguru import logger

from libs.member_active import ActiveDatabase

plugin = arc.GatewayPlugin("Members active")
voice_start_times: dict[int, int] = {}

ACTIVE_DB = ActiveDatabase(Path("bot_data/active.db"))


def format_duration(minutes: int) -> str:
    """Преобразует количество секунд в более точное время."""
    logger.debug(minutes)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    return f"{days:02d} д. {hours:02d}:{minutes:02d}"


# Отслеживание событий
# ====================


@plugin.listen(hikari.GuildMessageCreateEvent)
async def on_message(event: hikari.GuildMessageCreateEvent) -> None:
    """Добавляем опыт за текстовые сообщения."""
    if event.author.is_bot:
        return

    xp = len(event.message.attachments) * 5
    if event.content is not None:
        xp += len(event.content.split())

    await ACTIVE_DB.add_messages(event.author_id, xp)

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
async def on_voice_update(event: hikari.VoiceStateUpdateEvent) -> None:
    """Отслеживаем активность в голосовом канале."""
    before = event.old_state
    after = event.state
    member = event.state.member

    if member is None or member.is_bot:
        return

    if member.id not in voice_start_times:
        logger.info("Add {} to listener", member.id)
        voice_start_times[member.id] = int(time())

    elif before is not None and after.channel_id is None:
        if member.id in voice_start_times:
            logger.info("Remove {} from listener", member.id)
            start = voice_start_times.pop(member.id)
            duration = round((int(time()) - start) / 60)
            if duration > 0:
                await ACTIVE_DB.add_voice(member.id, duration)


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
) -> None:
    """Таблица лидеров по сообщениям."""
    leaders = await ACTIVE_DB.get_top(group)

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

        points = f"`{active.words}` слов / `{active.messages}` сообщений"
        if group == "level":
            target_xp = active.count_xp()
            points = (
                f"`{active.level}` уровень `{active.xp}/{target_xp}` опыта."
            )
        if group == "voice":
            points = f"`{format_duration(active.voice)}`"
        if group == "bumps":
            points = f"`{active.bumps}` бампов"

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
) -> None:
    """Таблица лидеров по сообщениям."""
    if user is None:
        user = ctx.author

    active = await ACTIVE_DB.get_or_default(user.id)
    emb = hikari.Embed(
        title="Активность",
        description=(
            f"**Уровень:** {active.level} / 100\n"
            f"**Сообщений:** {active.messages}\n"
            f"**Слов:** {active.words}\n"
            f"**В голосовом канале:** {format_duration(active.voice)}\n"
            f"**Бампов:** {active.bumps}\n"
        ),
        color=user.accent_color,
    )

    target_xp = active.count_xp()
    pr = round((active.xp / target_xp) * 100, 2)
    emb.add_field("Опыт", f"{active.xp}/{target_xp} ({pr}%)")
    emb.set_thumbnail(user.make_avatar_url(file_format="PNG"))
    await ctx.respond(emb)


# Загрузчики и выгрузчики плагина
# ===============================


@plugin.listen(arc.events.StartedEvent)
async def connect(event: arc.events.StartedEvent[arc.GatewayClient]) -> None:
    """Подключаемся к базам данных при запуске бота."""
    logger.info("Connect to active DB")
    await ACTIVE_DB.connect()


@plugin.listen(arc.events.StoppingEvent)
async def disconnect(
    event: arc.events.StoppingEvent[arc.GatewayClient],
) -> None:
    """Время отключаться от баз данных, вместе с отключением бота."""
    logger.info("Close connect to active DB")

    now = int(time())
    for k, v in voice_start_times.items():
        logger.info("Remove {} from listener", k)
        duration = round(now - v / 60)
        if duration > 0:
            await ACTIVE_DB.add_voice(k, duration)

    await ACTIVE_DB.commit()
    await ACTIVE_DB.close()


@arc.loader
def loader(client: arc.GatewayClient) -> None:
    """Действия при загрузке плагина."""
    client.add_plugin(plugin)
    client.set_type_dependency(ActiveDatabase, ACTIVE_DB)


@arc.unloader
def unloader(client: arc.GatewayClient) -> None:
    """Действия при выгрузке плагина."""
    client.remove_plugin(plugin)
