"""монетки.

Предоставляет пользователям доступ к экономической системе.
Тут вы можете как проверять количество своих монеток, управлять
депозитом, так и просматривать таблицу лидеров самых богах участников
сервера.

.. note:: Обязательное расширение.

    Если вы хотите использовать экономическую систему, то данное
    расширение является обязательным, поскольку предоставляет доступ
    к базе данных монетное хранилище.

    В ином случае вам самостоятельно придётся её подключать.

Предоставляет
-------------

- /coins - Управление финансами всех пользователей.
- /coins reset [user] - Сбросить монеты пользователя.
- /coins give <amount> [user] - Выдать монеты участнику.
- /coins take <amount> [user] - Забрать монеты участника.
- /deposit - Управление вашими накоплениями.
- /deposit put <amount> - Положить монеты в банк.
- /deposit take <amount> - Взять монеты из банка.
- /deposit info - Информация о накоплениях.
- /pay <user> <amount> - Оплатить услугу пользователю.
- /balance [user] - Сколько монет у пользователя на руках.
- /cointop - Таблица лидеров самых богатых участников.
- /cointop all - Общая таблица лидеров самых богатых участников.
- /cointop amount - Самые богатые участники с монетками на руках.
- /cointop deposit - Самые богатые участники с монетками в банке.

Version: v0.3.2 (12)
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
# Экземпляр базы данных монетное хранилище
# Получить доступ из других расширений можно через type dependencies
COINS_DB = coinengine.CoinDB(Path("bot_data/coins.db"))

# Общее сообщение при неудачной транзакции
# К примеру у вас может быть недостаточно средств или ещё какая-то
# иная ошибка во время выполнения транзакции монетное хранилище
BAD_TRANSACTION = hikari.Embed(
    title="Ой, ошибочка",
    description="Вероятно у вас недостаточно средств, для данной транзакции.",
    color=hikari.Color(0xFF00AA),
)


# определение команд
# ==================

# Управление финансами ---------------------------------------------------------

coin_group = plugin.include_slash_group(
    name="coins",
    description="Управление финансами всех пользователей.",
    default_permissions=hikari.Permissions.ADMINISTRATOR,
)


@coin_group.include
@arc.slash_subcommand("reset", description="Сбросить баланс участника.")
async def coin_reset_handler(
    ctx: arc.GatewayContext,
    user: arc.Option[  # type: ignore
        hikari.User | None, arc.UserParams("У кого сбросить баланс (себе)")
    ] = None,
) -> None:
    """Сбрасывает монеты для пользователя.

    Осуществляет полный сброс всех средств пользователя.
    Если не указано у кого производить сброс, то выберет автора
    вызвавшего команду.
    Вероятно это может быть для чего-то использовано.
    """
    if user is None:
        user = ctx.user

    await COINS_DB.delete(user_id=user.id)
    await COINS_DB.commit()
    embed = hikari.Embed(
        title="Успешный сброс",
        description=f"{user.mention} остался без монеток",
        color=hikari.Color(0x00FFCC),
    )
    await ctx.respond(embed=embed)


@coin_group.include
@arc.slash_subcommand("give", description="Выдать монетки участнику.")
async def coin_give_handler(
    ctx: arc.GatewayContext,
    amount: arc.Option[int, arc.IntParams("Сколько дать")],  # type: ignore
    user: arc.Option[  # type: ignore
        hikari.User | None, arc.UserParams("Кому дать монетки (себе)")
    ] = None,
) -> None:
    """Выдает монеты для участника.

    Выбранное количество монет будет передано в руки участника.
    Если не указать целевого участника, то им станет вызвавший команду.
    Данная команда может быть использована для запуска экономики.
    """
    if user is None:
        user = ctx.user

    await COINS_DB.give(user_id=user.id, amount=amount)
    await COINS_DB.commit()
    embed = hikari.Embed(
        title="Успешная транзакция",
        description=f"Вы выдали {user.mention} {amount} монеток",
        color=hikari.Color(0x00FFCC),
    )
    await ctx.respond(embed=embed)


@coin_group.include
@arc.slash_subcommand("take", description="Забрать монетки участника.")
async def coin_take_handler(
    ctx: arc.GatewayContext,
    amount: arc.Option[int, arc.IntParams("Сколько взять")],  # type: ignore
    user: arc.Option[  # type: ignore
        hikari.User | None, arc.UserParams("У кого забрать (себе)")
    ] = None,
) -> None:
    """Забирает монетки участника.

    Это касается только тех монет, которые есть на руках пользователя.
    Если указано больше монет, чем имеется у пользователя на руках -
    баланс будет сброшен.
    Если не указать участника, то целью станет вызвавший команду.
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
            color=hikari.Color(0x00FFCC),
        )
        await ctx.respond(embed=embed)
    else:
        await ctx.respond(embed=BAD_TRANSACTION)


# Управление накоплениями ------------------------------------------------------

deposit_group = plugin.include_slash_group(
    name="deposit", description="Управление вашими накоплениями."
)


@deposit_group.include
@arc.slash_subcommand("put", description="Положить монеты в банк.")
async def deposit_put_handler(
    ctx: arc.GatewayContext,
    amount: arc.Option[int, arc.IntParams("Сколько положить")],  # type: ignore
) -> None:
    """Перекладывает монеты в банк.

    Это значит что вы не сможете ими воспользоваться.
    Однако это также значит, то они будут находиться в безопасности.
    А также, как приятный бонус, со временем монетки будут расти.

    Вы не сможете положить в банк больше, чем у вас есть на руках.
    """
    status = await COINS_DB.to_deposit(user_id=ctx.user.id, amount=amount)
    if status:
        await COINS_DB.commit()
        embed = hikari.Embed(
            title="Успешная транзакция",
            description=f"Вы положили на депозит {amount} монеток",
            color=hikari.Color(0x00FFCC),
        )
        await ctx.respond(embed=embed)
    else:
        await ctx.respond(embed=BAD_TRANSACTION)


@deposit_group.include
@arc.slash_subcommand("take", description="Взять монеты из банка.")
async def deposit_take_handler(
    ctx: arc.GatewayContext,
    amount: arc.Option[int, arc.IntParams("Сколько взять")],  # type: ignore
) -> None:
    """Берёт монетки из банка.

    Держать монеты у себя на руках не всегда безопасно.
    Однако монетами на депозите пользоваться нельзя.
    Вы не сможете взять больше, чем у вас находятся в банке.
    """
    status = await COINS_DB.from_deposit(user_id=ctx.user.id, amount=amount)
    if status:
        await COINS_DB.commit()
        embed = hikari.Embed(
            title="Успешная транзакция",
            description=f"Вы взяли с депозита {amount} монеток",
            color=hikari.Color(0x00FFCC),
        )
        await ctx.respond(embed=embed)
    else:
        await ctx.respond(embed=BAD_TRANSACTION)


@deposit_group.include
@arc.slash_subcommand("info", description="Ваши накопления.")
async def deposit_info_handler(ctx: arc.GatewayContext) -> None:
    """Получает информацию о накоплениях.

    Рассказывает о том, почему выгодно оставлять монетки в банке.
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
        color=hikari.Color(0x00FFCC),
    ).add_field(name="Сейчас лежит", value=str(user_info.deposit))
    await ctx.respond(embed=embed)


# Основные команды -------------------------------------------------------------


@plugin.include
@arc.slash_command("pay", description="Оплатить услуги пользователю.")
async def pay_handler(
    ctx: arc.GatewayContext,
    user: arc.Option[hikari.User, arc.UserParams("Кому передать монетки")],  # type: ignore
    amount: arc.Option[int, arc.IntParams("Сколько передать")],  # type: ignore
) -> None:
    """Оплатить услугу пользователю.

    Определённое число монеток будет передано от вас другому
    пользователю.
    Вы не сможете отдать больше, чем у вас есть монет на руках.
    """
    status = await COINS_DB.move(amount, ctx.user.id, user.id)
    if status:
        await COINS_DB.commit()
        embed = hikari.Embed(
            title="Успешная транзакция",
            description=(
                f"{ctx.user.mention} перевёл {user.mention} {amount} монеток"
            ),
            color=hikari.Color(0x00FFCC),
        )
        await ctx.respond(embed=embed)
    else:
        await ctx.respond(embed=BAD_TRANSACTION, delete_after=10)


@plugin.include
@arc.slash_command("balance", description="Сколько монеток у вас на руках.")
async def balance_handler(
    ctx: arc.GatewayContext,
    user: arc.Option[  # type: ignore
        hikari.User | None, arc.UserParams("Чьи монетки хотите посмотреть")
    ] = None,
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

    embed = (
        hikari.Embed(
            title="Баланс",
            description="Это все монетки, что у вас есть.",
            color=hikari.Color(0xFFCC00),
        )
        .add_field("Всего", str(user_coins.balance), inline=True)
        .add_field("На руках", str(user_coins.amount), inline=True)
        .add_field("Депозит", str(user_coins.deposit), inline=True)
    )
    await ctx.respond(embed=embed)


# Таблица лидеров --------------------------------------------------------------

cointop_group = plugin.include_slash_group(
    name="cointop", description="Таблица лидеров самых богатых участников."
)


def get_leaders_list(
    ctx: arc.GatewayContext, leaders: list[coinengine.CoinsData]
) -> str:
    """Собирает таблицу лидеров самых богатых участников сервера.

    Запись в таблице выглядит примерно так:

    1. Milinuri: 630 (570)

    Где сначала идёт порядковый номер, имя пользователя, сколько
    монет на руках и сколько монет в банке.
    Если не удалось получить участника, вместе его имени будет его ID.

    :param ctx: Контекст вызванной команды: где, когда, кем.
    :type ctx: arc.GatewayContext
    :param leaders: Список лидеров, полученный из базы данных.
    :type leaders: list[coinengine.CoinsData]
    :return: Строка с таблицей лидеров.
    :rtype: str
    """
    res = ""
    for i, user in enumerate(leaders):
        guild = ctx.get_guild()
        if guild is None:
            logger.warning("{} {} guild is Noe", i, user)
            continue
        member = guild.get_member(user.user_id)
        if member is not None:
            username = member.nickname
        else:
            username = str(user.user_id)

        res += f"\n{i + 1}. {username}: {user.amount} ({user.deposit})"
    return res


@cointop_group.include
@arc.slash_subcommand(
    name="all", description="Самые богатые участники сервера."
)
async def cointop_all_handler(ctx: arc.GatewayContext) -> None:
    """Общая таблица лидеров (на руках + в банке)."""
    leaders = await COINS_DB.get_leaderboard(coinengine.OrderBy.ALL)
    embed = hikari.Embed(
        title="Таблица лидеров / общее",
        description=get_leaders_list(ctx, leaders),
        color=hikari.Color(0xFFCC66),
    )
    await ctx.respond(embed=embed)


@cointop_group.include
@arc.slash_subcommand(
    name="amount", description="Самые богатые участники (монетки на руках)."
)
async def cointop_amount_handler(
    ctx: arc.GatewayContext,
) -> None:
    """Таблица лидеров самых богатых участников с монетками на руках."""
    leaders = await COINS_DB.get_leaderboard(coinengine.OrderBy.AMOUNT)
    embed = hikari.Embed(
        title="Таблица лидеров / на руках",
        description=get_leaders_list(ctx, leaders),
        color=hikari.Color(0xFF9966),
    )
    await ctx.respond(embed=embed)


@cointop_group.include
@arc.slash_subcommand(
    name="deposit", description="Самые богатые участники (банк)."
)
async def cointop_deposit_handler(
    ctx: arc.GatewayContext,
) -> None:
    """Таблица лидеров самых богатых участников с монетками в банке."""
    leaders = await COINS_DB.get_leaderboard(coinengine.OrderBy.deposit)
    embed = hikari.Embed(
        title="Таблица лидеров / в банке",
        description=get_leaders_list(ctx, leaders),
        color=hikari.Color(0x66CCFF),
    )
    await ctx.respond(embed=embed)


# Загрузчики и выгрузчики плагина
# ===============================


@plugin.listen(arc.events.StartedEvent)
async def connect(event: arc.events.StartedEvent[arc.GatewayClient]) -> None:
    """Подключаемся к базам данных при запуске бота."""
    logger.info("Connect to index/inventory DB")
    await COINS_DB.connect()
    await COINS_DB.create_tables()


@plugin.listen(arc.events.StoppingEvent)
async def disconnect(
    event: arc.events.StoppingEvent[arc.GatewayClient],
) -> None:
    """Время отключаться от баз данных, вместе с отключением бота."""
    logger.info("Close connect to index/inventory DB")
    await COINS_DB.commit()
    await COINS_DB.close()


@arc.loader
def loader(client: arc.GatewayClient) -> None:
    """Действия при загрузке плагина.

    Подключаем базу данных монетного хранилища.
    """
    client.add_plugin(plugin)
    client.set_type_dependency(coinengine.CoinDB, COINS_DB)


@arc.unloader
def unloader(client: arc.GatewayClient) -> None:
    """Действия при выгрузке плагина."""
    client.remove_plugin(plugin)
