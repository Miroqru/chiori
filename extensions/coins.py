"""монетки.

Предоставляет пользователям доступ к экономической системе.
Тут вы можете как проверять количество своих монеток, управлять
депозитом, так и просматривать таблицу лидеров самых богах участников
сервера.

.. note:: Обязательное ресширение.

    Если вы хотиет использовать экономическую систему, то данное
    расширение является обязательным, посколькуо предоставляет доступ
    к базе данных монетахранилища.

    В ином случае вам самостоятельно придётся её подключать.

Предоставляет
-------------

- /coins - Управление финансами всех пользователей. (особое)
- /coins reset [user] - Полностью сбросить монеты для пользователя.
- /coins give <amount> [user] - Выдать монеты участнику.
- /coins take <amount> [user] - Забрать монеты участника.
- /deposite - Управляйте вашими накоплениями.
- /deposite put <anount> - Положить монеты в банк.
- /deposite take <anount> - Взять монеты из банка.
- /deposite info - Информация о накоплениях.
- /pay <user> <amount> - Оплатить услугу пользователю.
- /balance [user] - Сколько монет у пользователя.
- /cointop - Таблица лидеров самых богатых участников.
- /cointop all - Общая таблица лидеров самых богатых участников.
- /cointop amount - Самые богатые участники с монетками на руках.
- /cointop deposite - Самые богатые участники с монетками в банке.

Version: v0.3 (9)
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
# Экземпляр базы данных монетохранилища
# Получить доступ из других расширений можно через type edpendecies
COINS_DB = coinengine.CoinDB(Path("bot_data/coins.db"))

# Общее сообщение при неудачной транзакции
# К примеру у вас может быть недостаточно средств или ещё какая-то
# иная ошибка во время выполнения транзакции монетахранилища
BAD_TRANSACTION = hikari.Embed(
    title="Ой, ошибочка",
    description="Вероятно у вас недостаточно средств, для даннной транзакции.",
    color=hikari.colors.Color(0xff00aa)
)


# определение команд
# ==================

# Управление финансами ---------------------------------------------------------

coin_group = plugin.include_slash_group(
    name="coins",
    description="управляйте финансами ваших пользователей",
    default_permissions=hikari.Permissions.ADMINISTRATOR
)

@coin_group.include
@arc.slash_subcommand("reset", description="Сбросить баланс участника.")
async def coin_reset_handler(
    ctx: arc.GatewayContext,
    user: arc.Option[
        hikari.User | None, arc.UserParams("У кого сбросить баланс (себе)")
    ] = None
) -> None:
    """Сбрасывает монеты для пользователя.

    Осуществляет полный сброс всех средств пользовтеля.
    Если не укзаано у кого производить сброс, то выберет автора
    вызвывшего команду.
    Вероятно это может быть для чего-то использовано.
    """
    if user is None:
        user = ctx.user

    await COINS_DB.delete(user_id=user.id)
    await COINS_DB.commit()
    embed = hikari.Embed(
        title="Успешный сброс",
        description=f"{user.mention} остался без монеток",
        color=hikari.colors.Color(0x00ffcc)
    )
    await ctx.respond(embed=embed)

@coin_group.include
@arc.slash_subcommand("give", description="Выдать монетки участнику.")
async def coin_give_handler(
    ctx: arc.GatewayContext,
    amount: arc.Option[int, arc.IntParams("Сколько дать")],
    user: arc.Option[
        hikari.User | None, arc.UserParams("Кому дать монетки (себе)")
    ] = None
) -> None:
    """Выдает монеты для участника.

    Выбранное количество монет будет передано в руки участника.
    Если не укзаать целевого участника, то им станет вызвавший команду.
    Данная комнада может быть использована для запуска экономики.
    """
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
@arc.slash_subcommand("take", description="Забрать монетки участника.")
async def coin_take_handler(
    ctx: arc.GatewayContext,
    amount: arc.Option[int, arc.IntParams("Сколько взять")],
    user: arc.Option[
        hikari.User | None, arc.UserParams("У кого забрать (себе)")
    ] = None
) -> None:
    """Забирает монетки участника.

    Это касается только тех монет, которые есть на руках пользователя.
    Если укзаано больше моент, чем имеется у пользователя на руках -
    баланс будет сброшен.
    Если не укзаать участника, то целью станет вызвавший команду.
    Неплохой способ забирать монеты у нарушителей порядка.
    """
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

# Управление накоплениями ------------------------------------------------------

deposite_group = plugin.include_slash_group(
    name="deposite",
    description="Управляйте вашими накоплениями"
)

@deposite_group.include
@arc.slash_subcommand("put", description="Положить монеты в банк.")
async def deposite_put_handler(
    ctx: arc.GatewayContext,
    amount: arc.Option[int, arc.IntParams("Сколько положить")],
) -> None:
    """Перекладывает монеты в банк.

    Это значит что вы не сможете ими воспользоваться.
    Однако это также значит, то они будут находиться в безопасности.
    А также, как приятный бонус, со времменем монетки будут расти.

    Вы не сможете положить в банк больше, чем у вас есить на руках.
    """
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
@arc.slash_subcommand("take", description="Взять монеты из банка.")
async def deposite_take_handler(
    ctx: arc.GatewayContext,
    amount: arc.Option[int, arc.IntParams("Сколько взять")],
) -> None:
    """Берёт монетки из банка.

    Держать монтеки у себя на руках не всегда безопасно.
    Однако монетами на депозите пользоваться нельзя.
    Вы не сможете взять больше, чем у вас нахоидтся в банке.
    """
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
@arc.slash_subcommand("info", description="Информация о накоплениях.")
async def deposite_info_handler(ctx: arc.GatewayContext) -> None:
    """Получает информацию о накоплениях.

    Расскзаывает о том, почему выгодно оставлять монетки в банке.
    А также показывает текущие накопления.
    """
    user_info = await COINS_DB.get_or_create(ctx.user.id)
    embed = hikari.Embed(
        title="Депозит",
        description=(
            "Итак, здесь вы можете хранить свою монетки.\n"
            "Тут они будут надёжно лежать и ждать вас.\n"
            "А ещё приятный бонус - со временем они вырастут."
        ),
        color=hikari.colors.Color(0x00ffcc)
    ).add_field(
        name="Сейчас лежит",
        value=str(user_info.deposite)
    )
    await ctx.respond(embed=embed)

# Основные команды -------------------------------------------------------------

@plugin.include
@arc.slash_command("pay", description="Оплатить услуги участнику.")
async def pay_handler(
    ctx: arc.GatewayContext,
    user: arc.Option[
        hikari.User, arc.UserParams("Кому передать монетки")
    ],
    amount: arc.Option[int, arc.IntParams("Сколько передать")]
) -> None:
    """Оплатить услугу пользователю.

    Определённое число монеток будет передано от вас другому
    пользовтелю.
    Вы не сможете отдать болше, чем у вас есть монет на руках.
    """
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
    """Информация о балансе пользователя.

    Отображает средства пользователя.
    Сколько у него сейчас на руках, а также, сколько в банке.
    Вероятно не совсем правильно. что мы можем подглядывать за другими.
    """
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

# Таблица лидеров --------------------------------------------------------------

cointop_group = plugin.include_slash_group(
    name="cointop",
    description="Таблица лидеров самых богатых участников"
)

def get_leaders_list(
    ctx: arc.GatewayContext,
    leaders: list[coinengine.CoinsData]
) -> str:
    """Собирает таблицу лидеров самых богатых участников сервера.

    Запись в таблице выглядит примерно так:

    1. Milinuri: 630 (570)

    Где сначала идёт порядковый номер, имя пользователя, сколько
    монет на руках и сколько монет в банке.
    Если не удалось получить учатсника, вместе его имени будет его ID.

    :param ctx: Контекст вызванной команды: где, когда, кем.
    :type ctx: arc.GatewayContext
    :param leaders: Список лидеров, полученный из базы данных.
    :type leaders: list[coinengine.CoinsData]
    :return: Строка с таблицей лидеров.
    :rtype: str
    """
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
    """Общая таблица лидеров (на руках + в банке)."""
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
async def cointop_amount_handler(
    ctx: arc.GatewayContext,
):
    """Таблица лидеров самых богатых участников с монетками на руках."""
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
async def cointop_deposite_handler(
    ctx: arc.GatewayContext,
):
    """Таблица лидеров самых богатых участников с монетками в банке."""
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
