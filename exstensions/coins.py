"""монетки.

Version: v0.1 (1)
Author: Milinuri Nirvalen
"""

from pathlib import Path

import arc
import hikari
from loguru import logger

from libs import coinengine

from icecream import ic

# Глобальные переменные
# =====================

plugin = arc.GatewayPlugin("Coins")
COINS_DB = coinengine.CoinDB(Path("bot_data/coins.db"))

BAD_TRANSACTION = hikari.Embed(
    title="Ой, ошибочка",
    description="Вероятно у вас недостаточно средств, для даннной транзакции.",
    color=hikari.colors.Color(0xff00aa)
)

# определение команд
# ==================

coin_group = plugin.include_slash_group(
    name="coins",
    description="управляйте финансами ваших пользователей",
    default_permissions=hikari.Permissions.ADMINISTRATOR
)

@coin_group.include
@arc.slash_subcommand("reset", description="Сбрасывает баланс пользователя.")
async def coin_reset_handler(
    ctx: arc.GatewayContext,
    user: arc.Option[
        hikari.User | None, arc.UserParams("У кого сбросить баланс (себе)")
    ] = None
) -> None:
    if user is None:
        user = ctx.user

    await COINS_DB.delete(user_id=user.id)
    await COINS_DB.commit()
    embed = hikari.Embed(
        title="Успешная транзакция",
        description=f"{user.mention} остался без монеток",
        color=hikari.colors.Color(0x00ffcc)
    )
    await ctx.respond(embed=embed)

@coin_group.include
@arc.slash_subcommand("give", description="Выдать монетки игроку.")
async def coin_give_handler(
    ctx: arc.GatewayContext,
    amount: arc.Option[int, arc.IntParams("Сколько дать")],
    user: arc.Option[
        hikari.User | None, arc.UserParams("Кому дать монетки (себе)")
    ] = None
) -> None:
    if user is None:
        user = ctx.user

    await COINS_DB.give(user_id=user.id, amount=amount)
    await COINS_DB.commit()
    embed = hikari.Embed(
        title="Успешная транзакция",
        description=f"Вы выдали {user.mention} {amount} монеток",
        color=hikari.colors.Color(0x00ffcc)
    )
    await ctx.respond(embed=embed)

@coin_group.include
@arc.slash_subcommand("take", description="Забрать монетки у игрока.")
async def coin_take_handler(
    ctx: arc.GatewayContext,
    amount: arc.Option[int, arc.IntParams("Сколько взять")],
    user: arc.Option[
        hikari.User | None, arc.UserParams("У кого забрать (себе)")
    ] = None
) -> None:
    if user is None:
        user = ctx.user

    status = await COINS_DB.take(user_id=user.id, amount=amount)
    if status:
        await COINS_DB.commit()
        embed = hikari.Embed(
            title="Успешная транзакция",
            description=f"Вы взяли у {user.mention} {amount} монеток",
            color=hikari.colors.Color(0x00ffcc)
        )
        await ctx.respond(embed=embed)
    else:
        await ctx.respond(embed=BAD_TRANSACTION)

# ----------------------------------------------------------------------

deposite_group = plugin.include_slash_group(
    name="deposite",
    description="Управляйте вашими накоплениями"
)

@deposite_group.include
@arc.slash_subcommand("put", description="Положить монеты на депозит.")
async def deposite_put_handler(
    ctx: arc.GatewayContext,
    amount: arc.Option[int, arc.IntParams("Сколько положить")],
) -> None:
    status = await COINS_DB.to_deposite(user_id=ctx.user.id, amount=amount)
    if status:
        await COINS_DB.commit()
        embed = hikari.Embed(
            title="Успешная транзакция",
            description=f"Вы положили на депозит {amount} монеток",
            color=hikari.colors.Color(0x00ffcc)
        )
        await ctx.respond(embed=embed)
    else:
        await ctx.respond(embed=BAD_TRANSACTION)

@deposite_group.include
@arc.slash_subcommand("take", description="Взять монеты с депозита.")
async def deposite_take_handler(
    ctx: arc.GatewayContext,
    amount: arc.Option[int, arc.IntParams("Сколько взять")],
) -> None:
    status = await COINS_DB.from_deposite(user_id=ctx.user.id, amount=amount)
    if status:
        await COINS_DB.commit()
        embed = hikari.Embed(
            title="Успешная транзакция",
            description=f"Вы взяли с депозита {amount} монеток",
            color=hikari.colors.Color(0x00ffcc)
        )
        await ctx.respond(embed=embed)
    else:
        await ctx.respond(embed=BAD_TRANSACTION)

@deposite_group.include
@arc.slash_subcommand("info", description="Что такое депозит.")
async def deposite_info_handler(ctx: arc.GatewayContext) -> None:
    user_info = await COINS_DB.get_or_create(ctx.user.id)
    embed = hikari.Embed(
        title="Депозит",
        description=(
            "Итак, здесь вы можете хранить свою монетки.\n"
            "Тут они будут надёжно лежать и ждать вас.\n"
            "А ещё приятный бонус - со времнем их станет только больше."
        ),
        color=hikari.colors.Color(0x00ffcc)
    ).add_field(
        name="Сейчас лежит",
        value=str(user_info.deposite)
    )
    await ctx.respond(embed=embed)

# ----------------------------------------------------------------------

@plugin.include
@arc.slash_command("pay", description="Оплатить услуги участнику.")
async def pay_handler(
    ctx: arc.GatewayContext,
    user: arc.Option[
        hikari.User, arc.UserParams("Кому передать монетки")
    ],
    amount: arc.Option[int, arc.IntParams("Сколько передать")]
) -> None:
    status = await COINS_DB.move(amount, ctx.user.id, user.id)
    if status:
        await COINS_DB.commit()
        embed = hikari.Embed(
            title="Успешная транзакчия",
            description=(
                f"{ctx.user.mention} перевёл {user.mention} {amount} монеток"
            ),
            color=hikari.colors.Color(0x00ffcc)
        )
        await ctx.respond(embed=embed)
    else:
        await ctx.respond(embed=BAD_TRANSACTION, delete_after=10)


@plugin.include
@arc.slash_command("balance", description="Сколько монеток у вас есть.")
async def balance_handler(
    ctx: arc.GatewayContext,
    user: arc.Option[
        hikari.User | None, arc.UserParams("Чьи монетки хотите посмотреть")
    ] = None
) -> None:
    if user is None:
        user_id = ctx.user.id
    else:
        user_id = user.id

    user_coins = await COINS_DB.get_or_create(user_id)

    embed = hikari.Embed(
        title="Баланс",
        description="Это все монетки, что у вас есть.",
        color=hikari.colors.Color(0xffcc00)
    ).add_field(
        name="Всего", value=user_coins.balance, inline=True
    ).add_field(
        name="На руках", value=user_coins.amount, inline=True
    ).add_field(
        name="Депозит", value=user_coins.deposite, inline=True
    )
    await ctx.respond(embed=embed)

# ----------------------------------------------------------------------

cointop_group = plugin.include_slash_group(
    name="cointop",
    description="Таблица лидеров самых богатых участников"
)

def get_leaders_list(
    ctx: arc.GatewayContext,
    leaders: list[coinengine.CoinsData]
) -> str:
    res = ""
    for i, coindata in enumerate(leaders):
        member = ctx.get_guild().get_member(coindata.user_id)
        if member is not None:
            username = member.nickname
        else:
            username = coindata.user_id

        res += (
            f"\n{i+1}. {username}: {coindata.amount}"
            f" ({coindata.deposite})"
        )
    return res

@cointop_group.include
@arc.slash_subcommand(name="all", description="Самые богатые участники сервера")
async def cointop_all_handler(
    ctx: arc.GatewayContext,
):
    leaders = await COINS_DB.get_leaderboard(coinengine.OrderBy.ALL)
    embed = hikari.Embed(
        title="Таблица лидеров / общее",
        description=get_leaders_list(ctx, leaders),
        color=hikari.Color(0xffcc66)
    )
    await ctx.respond(embed=embed)

@cointop_group.include
@arc.slash_subcommand(
    name="amount", description="Самые богатые участники (монетки на руках)"
)
async def cointop_all_handler(
    ctx: arc.GatewayContext,
):
    leaders = await COINS_DB.get_leaderboard(coinengine.OrderBy.AMOUNT)
    embed = hikari.Embed(
        title="Таблица лидеров / на руках",
        description=get_leaders_list(ctx, leaders),
        color=hikari.Color(0xff9966)
    )
    await ctx.respond(embed=embed)

@cointop_group.include
@arc.slash_subcommand(
    name="deposite", description="Самые богатые участники (банк)"
)
async def cointop_all_handler(
    ctx: arc.GatewayContext,
):
    leaders = await COINS_DB.get_leaderboard(coinengine.OrderBy.DEPOSITE)
    embed = hikari.Embed(
        title="Таблица лидеров / в банке",
        description=get_leaders_list(ctx, leaders),
        color=hikari.Color(0x66ccff)
    )
    await ctx.respond(embed=embed)


# Загрузчики и выгрузчики плагина
# ===============================

@plugin.listen(arc.events.StartedEvent)
async def connect(event: arc.events.StartedEvent):
    """Подключаемся к базам данных при запуске бота."""
    logger.info("Connect to index/inventory DB")
    await COINS_DB.connect()
    await COINS_DB.create_tables()


@plugin.listen(arc.events.StoppingEvent)
async def disconnect(event: arc.events.StoppingEvent):
    """Время отключаться от баз данных, вместе с отключением бота."""
    logger.info("Close connect to index/inventory DB")
    await COINS_DB.commit()
    await COINS_DB.close()


# ----------------------------------------------------------------------

@arc.loader
def loader(client: arc.GatewayClient) -> None:
    """Действия при загрузке плагина.

    Подключаем базу данных индекса предметов и инвенторя.
    """
    client.add_plugin(plugin)
    client.set_type_dependency(coinengine.CoinDB, COINS_DB)

@arc.unloader
def unloader(client: arc.GatewayClient) -> None:
    """Действия при выгрузке плагина.

    Завершаем подключение к базе данных предметов и инвенторя.
    """
    client.remove_plugin(plugin)
