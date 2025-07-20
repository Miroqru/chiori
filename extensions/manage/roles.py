"""Роли.

Управляет ролями пользователей.

предоставляет
-------------

/role status [user]: Узнать роль пользователя.
/role ban <user>: Заблокировать пользователя.
/role user <user>: Разблокировать пользователя.
/role vip <user>: назначить особой персоной.
/role moder <user>: назначить модератором.
/role admin <user>: назначить администратором.
/role reset <user>: Сбросить роль.

Version: v1.0 (1)
Author: Milinuri Nirvalen
"""

import arc
import hikari

from chioricord.hooks import has_role
from chioricord.roles import RoleLevel, RoleTable, UserRole

plugin = arc.GatewayPlugin("Roles")
plugin.add_hook(has_role(RoleLevel.ADMINISTRATOR))

role_group = plugin.include_slash_group(
    "role", "Управление ролями пользователей."
)

_EMBED_NO_PERMISSION = hikari.Embed(
    title="🔒 Подождите",
    description="Вы не можете управлять администраторами.",
    color=hikari.Color(0xCC3366),
)

# Определение команд
# ==================


def change_role_status(
    user: hikari.User, old: UserRole, new: UserRole
) -> hikari.Embed:
    """Статус смены роли для пользователя."""
    emb = hikari.Embed(
        title="Смена роли",
        description=(
            f"{user.mention}: `{old.role} -> {new.role}`\n"
            f"> {new.reason or 'без причины'}"
        ),
        color=hikari.Color(0x6633CC),
    )
    emb.set_thumbnail(user.make_avatar_url())
    return emb


@role_group.include
@arc.slash_subcommand("status", description="Узнать роль пользователя")
async def role_handler(
    ctx: arc.GatewayContext,
    user: arc.Option[
        hikari.User | None, arc.UserParams("Чью роль просмотреть")
    ] = None,
    table: RoleTable = arc.inject(),
) -> None:
    """Роль пользователя."""
    user = user or ctx.user
    role = await table.get_or_create(user.id)
    emb = hikari.Embed(
        title=f"{user.display_name}",
        description=(
            f"> {role.reason or 'Нет причины.'}\n\n"
            f"Уровень: `{role.role}`\n"
            f"От: {role.from_id}\n"
            f"Выдана: {role.start_time}\n"
        ),
        color=hikari.Color(0x6666CC),
    )
    emb.set_thumbnail(user.make_avatar_url())
    await ctx.respond(emb)


@role_group.include
@arc.slash_subcommand("ban", description="Заблокировать пользователя.")
async def set_ban_role(
    ctx: arc.GatewayContext,
    user: arc.Option[hikari.User, arc.UserParams("Кого заблокировать")],
    reason: arc.Option[str | None, arc.StrParams("Причина блокировки")] = None,
    table: RoleTable = arc.inject(),
    my_role: UserRole = arc.inject(),
) -> None:
    """Роль пользователя."""
    role = await table.get_or_create(user.id)
    if role.role > RoleLevel.MODERATOR and my_role.role != RoleLevel.OWNER:
        emb = _EMBED_NO_PERMISSION
    else:
        new_role = await table.set_banned(user.id, ctx.user.id, reason)
        emb = change_role_status(user, role, new_role)
    await ctx.respond(emb)


@role_group.include
@arc.slash_subcommand("user", description="Разблокировать пользователя.")
async def set_user_role(
    ctx: arc.GatewayContext,
    user: arc.Option[hikari.User, arc.UserParams("Кого разблокировать")],
    reason: arc.Option[str | None, arc.StrParams("Причина смены роли")] = None,
    table: RoleTable = arc.inject(),
    my_role: UserRole = arc.inject(),
) -> None:
    """Роль пользователя."""
    role = await table.get_or_create(user.id)
    if role.role > RoleLevel.MODERATOR and my_role.role != RoleLevel.OWNER:
        emb = _EMBED_NO_PERMISSION
    else:
        new_role = await table.set_user(user.id, ctx.user.id, reason)
        emb = change_role_status(user, role, new_role)
    await ctx.respond(emb)


@role_group.include
@arc.slash_subcommand("vip", description="Назначить особой персоной.")
async def set_vip_role(
    ctx: arc.GatewayContext,
    user: arc.Option[hikari.User, arc.UserParams("Какого пользователя")],
    reason: arc.Option[str | None, arc.StrParams("Причина смены роли")] = None,
    table: RoleTable = arc.inject(),
    my_role: UserRole = arc.inject(),
) -> None:
    """Роль пользователя."""
    role = await table.get_or_create(user.id)
    if role.role > RoleLevel.MODERATOR and my_role.role != RoleLevel.OWNER:
        emb = _EMBED_NO_PERMISSION
    else:
        new_role = await table.set_vip(user.id, ctx.user.id, reason)
        emb = change_role_status(user, role, new_role)
    await ctx.respond(emb)


@role_group.include
@arc.slash_subcommand("moder", description="Назначить модератором.")
async def set_moderator_role(
    ctx: arc.GatewayContext,
    user: arc.Option[hikari.User, arc.UserParams("Какого пользователя")],
    reason: arc.Option[str | None, arc.StrParams("Причина смены роли")] = None,
    table: RoleTable = arc.inject(),
    my_role: UserRole = arc.inject(),
) -> None:
    """Роль пользователя."""
    role = await table.get_or_create(user.id)
    if role.role > RoleLevel.MODERATOR and my_role.role != RoleLevel.OWNER:
        emb = _EMBED_NO_PERMISSION
    else:
        new_role = await table.set_moderator(user.id, ctx.user.id, reason)
        emb = change_role_status(user, role, new_role)
    await ctx.respond(emb)


@role_group.include
@arc.with_hook(has_role(RoleLevel.OWNER))
@arc.slash_subcommand("admin", description="Назначить администратором.")
async def set_administrator_role(
    ctx: arc.GatewayContext,
    user: arc.Option[hikari.User, arc.UserParams("Какого пользователя")],
    reason: arc.Option[str | None, arc.StrParams("Причина смены роли")] = None,
    table: RoleTable = arc.inject(),
) -> None:
    """Роль пользователя."""
    role = await table.get_or_create(user.id)
    new_role = await table.set_administrator(user.id, ctx.user.id, reason)
    emb = change_role_status(user, role, new_role)
    await ctx.respond(emb)


@role_group.include
@arc.with_hook(has_role(RoleLevel.OWNER))
@arc.slash_subcommand("reset", description="Сбросить роль.")
async def reset_role(
    ctx: arc.GatewayContext,
    user: arc.Option[hikari.User, arc.UserParams("Какого пользователя")],
    table: RoleTable = arc.inject(),
) -> None:
    """Сбрасывать роль пользователя.."""
    await table.remove_role(user.id)
    await ctx.respond(f"Роль {user.mention} сброшена.")


@arc.loader
def loader(client: arc.GatewayClient) -> None:
    """Actions on plugin load."""
    client.add_plugin(plugin)


@arc.unloader
def unloader(client: arc.GatewayClient) -> None:
    """Actions on plugin unload."""
    client.remove_plugin(plugin)
