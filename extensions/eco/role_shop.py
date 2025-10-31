"""Магазин ролей для сервере.

- TODO: Использовать Miru

Version: v1.2.1 (8)
Author: Milinuri Nirvalen
"""

import arc
import hikari

from chioricord.client import ChioClient, ChioContext
from chioricord.plugin import ChioPlugin
from libs.coinengine import CoinsTable
from libs.role_shop import GuildRole, RoleShopTable

plugin = ChioPlugin("Role shop")
role_shop = plugin.include_slash_group("rshop", "Магазин пролей")


async def _get_role(client: ChioClient, role: GuildRole) -> hikari.Role:
    return client.cache.get_role(role.role) or await client.rest.fetch_role(
        role.guild_id, role.role
    )


@role_shop.include
@arc.slash_subcommand("list", description="Доступные для покупки роли.")
async def list_shop_handler(
    ctx: ChioContext, shop: RoleShopTable = arc.inject()
) -> None:
    """Все доступные для покупки роли."""
    if ctx.guild_id is None:
        await ctx.respond("Выполните это команду на сервере.")
        return

    roles = await shop.get_shop(ctx.guild_id)
    res: list[str] = []
    for shop_role in sorted(roles, key=lambda r: r.price):
        role = await _get_role(ctx.client, shop_role)
        res.append(f"- {role.mention}: {shop_role.price}")

    emb = hikari.Embed(
        title="Магазин ролей",
        description="\n".join(res),
        color=hikari.Color(0xFFCC66),
    )
    await ctx.respond(emb)


@role_shop.include
@arc.slash_subcommand("byu", description="Купить роль.")
async def byu_shop_handler(
    ctx: ChioContext,
    role: arc.Option[hikari.Role, arc.RoleParams("Роль для покупки")],
    shop: RoleShopTable = arc.inject(),
    coins: CoinsTable = arc.inject(),
) -> None:
    """купить роль."""
    if ctx.guild_id is None or ctx.member is None:
        await ctx.respond("Выполните это команду на сервере.")
        return

    db_role = await shop.get_role(ctx.guild_id, role.id)
    if db_role is None:
        await ctx.respond("Роль не выставлена на продажу.")
        return

    member_roles = await ctx.member.fetch_roles()
    if role in member_roles:
        await ctx.respond("У вас уже приобретена данная роль.")
        return

    if db_role.require_role is not None:
        req_role = await ctx.client.rest.fetch_role(
            ctx.guild_id, db_role.require_role
        )

        if req_role not in member_roles:
            await ctx.respond(
                f"Для начала вам нужно приобрести {req_role.mention}"
            )
            return

    res = await coins.take(ctx.user.id, db_role.price)
    if not res:
        await ctx.respond("Кажется у вас недостаточно средств.")
        return

    await ctx.member.add_role(role)

    emb = hikari.Embed(
        title="Успешная покупка",
        description=f"Вы приобрели {role.mention} за {db_role.price} монеток",
        color=hikari.Color(0xFFCC66),
    )
    await ctx.respond(emb)


# Управление магазином
# ====================


@role_shop.include
@arc.with_hook(arc.has_permissions(hikari.Permissions.MANAGE_ROLES))
@arc.slash_subcommand("add_role", description="Добавить роль для в магазин.")
async def add_role_handler(
    ctx: ChioContext,
    role: arc.Option[hikari.Role, arc.RoleParams("Роль для продажи")],
    price: arc.Option[int, arc.IntParams("Цена покупки")],
    shop: RoleShopTable = arc.inject(),
) -> None:
    """Все доступные для покупки роли."""
    await shop.set_price(ctx.guild_id, role.id, price)  # type: ignore
    emb = hikari.Embed(
        title="Добавлена роль",
        description=f"{role.mention} за {price} монеток.",
        color=hikari.Color(0xFFCC66),
    )
    await ctx.respond(emb)


@role_shop.include
@arc.with_hook(arc.has_permissions(hikari.Permissions.MANAGE_ROLES))
@arc.slash_subcommand("remove_role", description="Удалить роль из магазина.")
async def remove_role_handler(
    ctx: ChioContext,
    role: arc.Option[hikari.Role, arc.RoleParams("Роль в магазине")],
    shop: RoleShopTable = arc.inject(),
) -> None:
    """Все доступные для покупки роли."""
    await shop.remove_role(ctx.guild_id, role.id)  # type: ignore
    emb = hikari.Embed(
        title="Удалена роль",
        description=f"{role.mention} удалена из магазина",
        color=hikari.Color(0xFFCC66),
    )
    await ctx.respond(emb)


@role_shop.include
@arc.with_hook(arc.has_permissions(hikari.Permissions.MANAGE_ROLES))
@arc.slash_subcommand(
    "set_require", description="Устанавливает необходимую роль."
)
async def set_require_handler(
    ctx: ChioContext,
    role: arc.Option[hikari.Role, arc.RoleParams("Роль в магазине")],
    require: arc.Option[
        hikari.Role | None, arc.RoleParams("Требуемая роль")
    ] = None,
    shop: RoleShopTable = arc.inject(),
) -> None:
    """Все доступные для покупки роли."""
    if require is None:
        req_id = None
        desc = f"Для покупки {role.mention} не требуется дополнительных ролей."
    else:
        req_id = require.id
        desc = f"Для покупки {role.mention} требуется купить {require.mention}"

    await shop.set_require(ctx.guild_id, role.id, req_id)  # type: ignore
    emb = hikari.Embed(
        title="Обновлена роль",
        description=desc,
        color=hikari.Color(0xFFCC66),
    )
    await ctx.respond(emb)


@arc.loader
def loader(client: ChioClient) -> None:
    """Actions on plugin load."""
    plugin.add_table(RoleShopTable)
    client.add_plugin(plugin)
