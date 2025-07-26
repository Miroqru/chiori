"""Коробка с утилитами.

Различные полезные команды, которые вы можете использовать.

Предоставляет
-------------

- /delmsg [count] - Удаляет сообщения из канала.
- /user [user] - Информация о пользователе.
- /server - Информация о сервере.

Version: v0.4 (17)
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


@plugin.include
@arc.slash_command("server", description="Информация о сервере")
async def guild_info(ctx: arc.GatewayContext) -> None:
    """Информация о сервер."""
    guild = ctx.get_guild()
    if guild is None:
        await ctx.respond(
            "Эта команда для сервера.", flags=hikari.MessageFlag.EPHEMERAL
        )
        return

    owner = await guild.fetch_owner()
    emb = hikari.Embed(
        title=guild.name,
        description=(
            f"> {guild.description or 'без описания'}\n\n"
            f"Участников: {guild.member_count}\n"
            f"Владелец: {owner.mention}\n"
            f"Создан: {guild.created_at}\n"
        ),
        color=hikari.Color(0xCC99FF),
    )
    emb.set_thumbnail(guild.make_icon_url())
    await ctx.respond(emb)


# Управление ролями участника
# ===========================


@plugin.include
@arc.slash_command(
    "member_roles",
    description="Роли участника",
    default_permissions=hikari.Permissions.MANAGE_ROLES,
)
async def list_roles_handler(
    ctx: arc.GatewayContext,
    member: arc.Option[
        hikari.Member | None, arc.MemberParams("Для какого участника")
    ] = None,
) -> None:
    """Отображает полный список ролей участника."""
    member = member or ctx.member
    if member is None:
        raise ValueError("Where is member")

    member_roles = await member.fetch_roles()
    roles_list: list[str] = []
    for role in member_roles:
        roles_list.append(f"- {role.mention}")

    emb = hikari.Embed(
        title=f"Роли {member.mention} ({len(member_roles)})",
        description="\n".join(roles_list),
        color=hikari.Color(0x66CC99),
    )
    emb.set_thumbnail(member.make_avatar_url())
    await ctx.respond(emb)


@plugin.include
@arc.slash_command(
    "add_role",
    description="Добавляет роль участнику",
    default_permissions=hikari.Permissions.MANAGE_ROLES,
)
async def add_role_handler(
    ctx: arc.GatewayContext,
    role: arc.Option[hikari.Role, arc.RoleParams("Какую роль добавить")],
    member: arc.Option[
        hikari.Member | None, arc.MemberParams("Для какого участника")
    ] = None,
    reason: arc.Option[
        str, arc.StrParams("По какой причине")
    ] = "Used /add_role command",
) -> None:
    """Добавляет новую роль участнику."""
    member = member or ctx.member
    if member is None:
        raise ValueError("Where is member")

    await member.add_role(role, reason=reason)
    emb = hikari.Embed(
        title="Добавлена роль",
        description=f"{member.mention} получил роль {role.mention}",
        color=hikari.Color(0x66CC99),
    )
    emb.set_thumbnail(member.make_avatar_url())
    await ctx.respond(emb)


@plugin.include
@arc.slash_command(
    "add_role_all",
    description="Добавляет роль всем участникам",
    default_permissions=hikari.Permissions.MANAGE_ROLES,
)
async def add_role_all_handler(
    ctx: arc.GatewayContext,
    role: arc.Option[hikari.Role, arc.RoleParams("Какую роль добавить")],
    reason: arc.Option[
        str, arc.StrParams("По какой причине")
    ] = "Used /add_role_all command",
) -> None:
    """Добавляет новую роль участнику."""
    if ctx.guild_id is None:
        await ctx.respond(
            "Вам нужно выполнить эту команду на сервере.",
            flags=hikari.MessageFlag.EPHEMERAL,
        )
        return

    members = ctx.client.cache.get_members_view_for_guild(ctx.guild_id)
    for member in members.values():
        await member.add_role(role)

    emb = hikari.Embed(
        title="Добавлена роль",
        description=f"Всем участникам добавлена роль {role.mention}!",
        color=hikari.Color(0x66CC99),
    )
    await ctx.respond(emb)


@plugin.include
@arc.slash_command(
    "remove_role",
    description="Удалить роль участника",
    default_permissions=hikari.Permissions.MANAGE_ROLES,
)
async def remove_role_handler(
    ctx: arc.GatewayContext,
    role: arc.Option[hikari.Role, arc.RoleParams("Какую роль удалить")],
    member: arc.Option[
        hikari.Member | None, arc.MemberParams("Для какого участника")
    ] = None,
    reason: arc.Option[
        str, arc.StrParams("По какой причине")
    ] = "Used /remove_role command",
) -> None:
    """Добавляет новую роль участнику."""
    member = member or ctx.member
    if member is None:
        raise ValueError("Where is member")

    await member.remove_role(role, reason=reason)
    emb = hikari.Embed(
        title="Удалена роль",
        description=f"{member.mention} лишился роли {role.mention}",
        color=hikari.Color(0xCC6699),
    )
    emb.set_thumbnail(member.make_avatar_url())
    await ctx.respond(emb)


@plugin.include
@arc.slash_command(
    "remove_role_all",
    description="Удаляет роль всем участникам",
    default_permissions=hikari.Permissions.MANAGE_ROLES,
)
async def remove_role_all_handler(
    ctx: arc.GatewayContext,
    role: arc.Option[hikari.Role, arc.RoleParams("Какую роль добавить")],
    reason: arc.Option[
        str, arc.StrParams("По какой причине")
    ] = "Used /add_role command",
) -> None:
    """Добавляет новую роль участнику."""
    if ctx.guild_id is None:
        await ctx.respond(
            "Вам нужно выполнить эту команду на сервере.",
            flags=hikari.MessageFlag.EPHEMERAL,
        )
        return

    members = ctx.client.cache.get_members_view_for_guild(ctx.guild_id)
    for member in members.values():
        await member.remove_role(role)

    emb = hikari.Embed(
        title="Удалена роль",
        description=f"Всем участникам удален роль {role.mention}!",
        color=hikari.Color(0xCC6699),
    )
    await ctx.respond(emb)


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
