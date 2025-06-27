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
async def delete_messages(
    ctx: arc.GatewayContext,
    channel: arc.Option[  # type: ignore
        hikari.TextableGuildChannel,
        arc.ChannelParams("Канал для очистки сообщений"),
    ],
    count: arc.Option[  # type: ignore
        int, arc.IntParams("Сколько удалить сообщений (10)")
    ] = 10,
) -> None:
    """Удаляет заданное количество сообщений в чате. По умолчанию 10."""
    count = min(max(count, 1), 100)
    ids: list[int] = []
    for i, message in enumerate(await channel.fetch_history()):
        ids.append(message.id)
        if i + 1 == count:
            break
    await channel.delete_messages(ids)
    await ctx.respond(
        f"Удалено {count} сообщений", flags=hikari.MessageFlag.EPHEMERAL
    )


def str_delta(delta: timedelta) -> str:
    """Строковая разница во времени."""
    years, days = divmod(delta.days, 365)
    if years > 0:
        return f"{years} л. {days} д."
    else:
        return f"{delta.days} д."


def get_member_info(member: hikari.Member) -> hikari.Embed:
    """Получает информацию об участнике сервера."""
    today = date.today()
    create_delta = str_delta(today - member.created_at.date())
    role = member.get_top_role()
    if role is not None:
        color = role.color
    else:
        color = hikari.Color(0xCC66FF)

    emb = hikari.Embed(
        title=f"Участник {member.global_name}",
        description=(
            f"**ID**: {member.id}\n"
            f"**Ник**: {member.nickname}\n"
            f"**Создан**: {member.created_at.strftime('%d/%m/%Y %H:%M:%S')}\n"
            f"**Существует**: {create_delta}\n"
        ),
        color=color,
    )
    emb.set_thumbnail(member.make_avatar_url(file_format="PNG"))
    if member.joined_at is not None:
        join_delta = str_delta(today - member.joined_at.date())
        emb.add_field(
            "Присоединился",
            f"{member.joined_at.strftime('%d/%m/%Y %H:%M:%S')}\n"
            f"**С нами**: {join_delta}",
        )

    return emb


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
    ).set_thumbnail(user.make_avatar_url(file_format="PNG"))


@plugin.include
@arc.slash_command("user", description="Информация о пользователе")
async def user_info(
    ctx: arc.GatewayContext,
    user: arc.Option[  # type: ignore
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
