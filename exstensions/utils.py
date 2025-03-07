"""Коробка с утилитами.

Различные полезные команды, которые вы можете использовать.

Предоставляет
-------------

- /delmsg [count] - Удаляет сообщения из канала.
- /user [user] - Информация о пользователе.

Version: v0.2.1 (13)
Author: Milinuri Nirvalen
"""

from datetime import date, timedelta

import arc
import hikari

plugin = arc.GatewayPlugin("utils")


# определение команд
# ==================


@plugin.include
@arc.slash_command(
    "delmsg",
    description="Удалить несколько сообщений в канале",
    default_permissions=hikari.Permissions.MANAGE_MESSAGES,
)
async def delmsg_handler(
    ctx: arc.GatewayContext,
    count: arc.Option[
        int, arc.IntParams("Сколько удалить сообщений (10)")
    ] = 10,
) -> None:
    """Удаляет заданное количество сообщений в чате. По умолчанию 10."""
    channel = ctx.get_channel()
    if channel is not None:
        count = min(max(count, 1), 100)
        ids = []
        for i, message in enumerate(await channel.fetch_history()):
            ids.append(message.id)
            if i + 1 == count:
                break
        await channel.delete_messages(ids)
        await ctx.respond(
            f"Удалено {count} сообщений", flags=hikari.MessageFlag.EPHEMERAL
        )
    else:
        await ctx.respond(
            "Данная команда только для текстовых каналов.",
            flags=hikari.MessageFlag.EPHEMERAL,
        )


def str_delta(delta: timedelta) -> str:
    """Строковая разница во времени."""
    years, days = divmod(delta.days, 365)
    if years > 0:
        return f"{years} л. {days} д."
    else:
        return f"{delta.days} д."


def get_member_info(member: hikari.Member) -> hikari.Member:
    """Получает информацию об участнике сервера."""
    today = date.today()
    create_delta = str_delta(today - member.created_at.date())
    join_delta = str_delta(today - member.joined_at.date())

    role = member.get_top_role()
    if role is not None:
        color = role.color
    else:
        color = hikari.Color(0xCC66FF)

    return hikari.Embed(
        title=f"Участник {member.global_name}",
        description=(
            f"**ID**: {member.id}\n"
            f"**Ник**: {member.nickname}\n"
            f"**Создан**: {member.created_at.strftime('%d/%m/%Y %H:%M:%S')}\n"
            f"**Существует**: {create_delta}\n"
            "**Присоединился**: "
            f"{member.joined_at.strftime('%d/%m/%Y %H:%M:%S')}\n"
            f"**С нами**: {join_delta}"
        ),
        color=color,
    ).set_thumbnail(member.avatar_url)


def get_user_info(user: hikari.User) -> hikari.Embed:
    """ПОлучает общую информацию о пользователе."""
    today = date.today()
    create_delta = str_delta(today - user.created_at.date())

    return hikari.Embed(
        title=f"Пользователь {user.global_name}",
        description=(
            f"**ID**: {user.id}\n"
            f"**Создан**: {user.created_at.strftime('%d/%m/%Y %H:%M:%S')}\n"
            f"**Существует**: {create_delta}"
        ),
        color=hikari.Color(0xCC66FF),
    ).set_thumbnail(user.avatar_url)


@plugin.include
@arc.slash_command("user", description="Информация о пользователе")
async def user_info(
    ctx: arc.GatewayContext,
    user: arc.Option[
        hikari.User | None, arc.UserParams("О ком получить сведения")
    ] = None,
) -> None:
    """Получает общедоступную информацию о пользователе."""
    if user is None:
        user = ctx.user
    guild = ctx.get_guild()
    if guild is not None:
        member = guild.get_member(user)
        if member is not None:
            embed = get_member_info(member)
        else:
            embed = get_user_info(user)
    else:
        embed = get_user_info(user)

    await ctx.respond(embed=embed)


# Загрузчики и выгрузчики плагина
# ===============================


@arc.loader
def loader(client: arc.GatewayClient) -> None:
    """Действия при загрузке плагина."""
    client.add_plugin(plugin)


@arc.unloader
def unloader(client: arc.GatewayClient) -> None:
    """Действия при выгрузке плагина."""
    client.remove_plugin(plugin)
