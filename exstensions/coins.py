"""монетки.


Version: v0.1 (1)
Author: Milinuri Nirvalen
"""

from pathlib import Path

import arc
import hikari

from loguru import logger

from libs import coinengine



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
