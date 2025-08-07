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

Version: v2.1.1 (19)
Author: Milinuri Nirvalen
"""

import arc
import hikari

from chioricord.client import ChioClient, ChioContext
from chioricord.hooks import has_role
from chioricord.plugin import ChioPlugin
from chioricord.roles import RoleLevel
from libs.coinengine import CoinsTable

plugin = ChioPlugin("Coins")

# Общее сообщение при неудачной транзакции
# К примеру у вас может быть недостаточно средств или ещё какая-то
# иная ошибка во время выполнения транзакции монетное хранилище
_BAD_TRANSACTION = hikari.Embed(
    title="🗑️ Ошибка транзакции",
    description=(
        "Нам не удалось перевести средства.\n\n"
        "**Возможные причины**:\n"
        "- Недостаточно средств на балансе.\n"
        "- Указанного пользователя не существует."
    ),
    color=hikari.Color(0xFF99CC),
)

_COLOR_MAIN = hikari.Color(0x00FF99)


def _success_transaction(text: str) -> hikari.Embed:
    return hikari.Embed(
        title="💸 Успешная транзакция",
        description=text,
        color=_COLOR_MAIN,
    )


def _pretty_pos(pos: int | None) -> str:
    if pos is None:
        return "0"
    if pos == 1:
        return "🥇"
    if pos == 2:  # noqa: PLR2004
        return "🥈"
    if pos == 3:  # noqa: PLR2004
        return "🥉"
    return str(pos)


# Управление финансами пользователе
# =================================

coin_group = plugin.include_slash_group(
    name="coins", description="Управление финансами всех пользователей."
)


@coin_group.include
@arc.with_hook(has_role(RoleLevel.MODERATOR))
@arc.slash_subcommand("give", description="Выдать монетки участнику.")
async def coin_give_handler(
    ctx: ChioContext,
    amount: arc.Option[int, arc.IntParams("Сколько дать", min=1)],  # type: ignore
    user: arc.Option[  # type: ignore
        hikari.User | None, arc.UserParams("Кому дать монетки (себе)")
    ] = None,
    coins: CoinsTable = arc.inject(),
) -> None:
    """Выдает монеты для участника.

    Выбранное количество монет будет передано в руки участника.
    Если не указать целевого участника, то им станет вызвавший команду.
    Данная команда может быть использована для запуска экономики.
    """
    user = user or ctx.user
    await coins.give(user_id=user.id, amount=amount)
    emb = _success_transaction(f"Вы выдали {user.mention} {amount} монеток.")
    await ctx.respond(emb)


@coin_group.include
@arc.with_hook(has_role(RoleLevel.MODERATOR))
@arc.slash_subcommand("take", description="Забрать монетки участника.")
async def coin_take_handler(
    ctx: ChioContext,
    amount: arc.Option[int, arc.IntParams("Сколько взять", min=1)],  # type: ignore
    user: arc.Option[  # type: ignore
        hikari.User | None, arc.UserParams("У кого забрать (себе)")
    ] = None,
    coins: CoinsTable = arc.inject(),
) -> None:
    """Забирает монетки участника.

    Это касается только тех монет, которые есть на руках пользователя.
    Если указано больше монет, чем имеется у пользователя на руках -
    баланс будет сброшен.
    Если не указать участника, то целью станет вызвавший команду.
    Неплохой способ забирать монеты у нарушителей порядка.
    """
    user = user or ctx.user
    status = await coins.take(user_id=user.id, amount=amount)
    if status:
        emb = _success_transaction(
            f"Вы взяли у {user.mention} {amount} монеток."
        )
    else:
        emb = _BAD_TRANSACTION
    await ctx.respond(emb)


# Управление накоплениями
# =======================

deposit_group = plugin.include_slash_group(
    name="deposit", description="Управление вашими накоплениями."
)


@deposit_group.include
@arc.slash_subcommand("put", description="Положить монеты в банк.")
async def deposit_put_handler(
    ctx: ChioContext,
    amount: arc.Option[int, arc.IntParams("Сколько положить", min=1)],  # type: ignore
    coins: CoinsTable = arc.inject(),
) -> None:
    """Перекладывает монеты в банк.

    Это значит что вы не сможете ими воспользоваться.
    Однако это также значит, то они будут находиться в безопасности.
    А также, как приятный бонус, со временем монетки будут расти.

    Вы не сможете положить в банк больше, чем у вас есть на руках.
    """
    status = await coins.to_deposit(user_id=ctx.user.id, amount=amount)
    if status:
        emb = _success_transaction(f"Вы положили на депозит {amount} монеток.")
    else:
        emb = _BAD_TRANSACTION
    await ctx.respond(emb)


@deposit_group.include
@arc.slash_subcommand("take", description="Взять монеты из банка.")
async def deposit_take_handler(
    ctx: ChioContext,
    amount: arc.Option[int, arc.IntParams("Сколько взять")],  # type: ignore
    coins: CoinsTable = arc.inject(),
) -> None:
    """Берёт монетки из банка.

    Держать монеты у себя на руках не всегда безопасно.
    Однако монетами на депозите пользоваться нельзя.
    Вы не сможете взять больше, чем у вас находятся в банке.
    """
    status = await coins.from_deposit(user_id=ctx.user.id, amount=amount)
    if status:
        emb = _success_transaction(f"Вы взяли с депозита {amount} монеток.")
    else:
        emb = _BAD_TRANSACTION
    await ctx.respond(emb)


@deposit_group.include
@arc.slash_subcommand("status", description="Ваши накопления.")
async def deposit_info_handler(
    ctx: ChioContext, coins: CoinsTable = arc.inject()
) -> None:
    """Получает информацию о накоплениях.

    Рассказывает о том, почему выгодно оставлять монетки в банке.
    А также показывает текущие накопления.
    """
    user_info = await coins.get_or_create(ctx.user.id)
    emb = hikari.Embed(
        title="Депозит",
        description=(
            "Здесь вы можете хранить свою монетки.\n"
            "Тут они будут надёжно лежать и ждать вас.\n"
            "А ещё приятный бонус - со временем они растут."
        ),
        color=hikari.Color(0x00FF99),
    )
    emb.add_field(
        name="Сейчас лежит", value=f"`{user_info.deposit}`", inline=True
    )
    pos = await coins.get_position(ctx.user.id)
    if pos is not None:
        emb.add_field("Место в рейтинге", f"{_pretty_pos(pos)} по накоплениям")
    await ctx.respond(emb)


# Основные команды -------------------------------------------------------------


@plugin.include
@arc.slash_command("pay", description="Оплатить услуги пользователю.")
async def pay_handler(
    ctx: ChioContext,
    user: arc.Option[hikari.User, arc.UserParams("Кому передать монетки")],  # type: ignore
    amount: arc.Option[
        int, arc.IntParams("Сколько передать", min=1, max=10_000_000)
    ],  # type: ignore
    coins: CoinsTable = arc.inject(),
) -> None:
    """Оплатить услугу пользователю.

    Определённое число монеток будет передано от вас другому
    пользователю.
    Вы не сможете отдать больше, чем у вас есть монет на руках.
    """
    status = await coins.move(amount, ctx.user.id, user.id)
    if status:
        emb = _success_transaction(
            f"Вы перевели {user.mention} {amount} монеток."
        )
    else:
        emb = _BAD_TRANSACTION

    await ctx.respond(emb)


@plugin.include
@arc.slash_command("balance", description="Сколько монеток у вас на руках.")
async def balance_handler(
    ctx: ChioContext,
    user: arc.Option[  # type: ignore
        hikari.User | None, arc.UserParams("Чьи монетки хотите посмотреть")
    ] = None,
    coins: CoinsTable = arc.inject(),
) -> None:
    """Информация о балансе пользователя.

    Отображает средства пользователя.
    Сколько у него сейчас на руках, а также, сколько в банке.
    Вероятно не совсем правильно. что мы можем подглядывать за другими.
    """
    user = user or ctx.user
    user_coins = await coins.get_or_create(user.id)
    emb = hikari.Embed(
        title="💸 Счёт пользователя",
        description=f"На счету {user.mention} имеется:",
        color=hikari.Color(0xFFCC66),
    )
    emb.add_field("Всего", str(user_coins.balance), inline=True)
    emb.add_field("На руках", str(user_coins.amount), inline=True)
    emb.add_field("В банке", str(user_coins.deposit), inline=True)

    pos = await coins.get_position(user.id)
    if pos is not None:
        emb.add_field("Место в рейтинге", f"{_pretty_pos(pos)} по накоплениям")

    emb.add_field(
        "Управление балансом",
        (
            "`/pay <user> <amount>`: Оплатить пользователю.\n"
            "`/deposit put/take <amount>`: Управление депозитом.\n"
            "`/rich [group]`: Самые богатые участники сервера."
        ),
    )

    await ctx.respond(emb)


# Таблица лидеров --------------------------------------------------------------


@plugin.include
@arc.slash_command("rich", description="Самый богатые участники сервера.")
async def rich_handler(
    ctx: ChioContext,
    group: arc.Option[
        str,
        arc.StrParams(
            "по какой категории",
            choices=["amount+deposit", "amount", "deposit"],
        ),
    ] = "amount+deposit",
    coins: CoinsTable = arc.inject(),
) -> None:
    """Таблица лидеров самых богатых участников сервера."""
    # guild = ctx.get_guild()
    # if guild is None or ctx.guild_id is None:
    #     logger.warning("Guild is None")
    #     return "Вам бы выполнять эту команду в гильдии."
    if group == "amount":
        header = "Наличные"
        color = hikari.Color(0xFFCC66)
    elif group == "deposit":
        header = "В банке"
        color = hikari.Color(0xFF9966)
    else:
        header = "Общее"
        color = hikari.Color(0x66CCFF)

    leaders = await coins.get_leaders(group)  # type: ignore
    leaderboard: list[str] = []
    for i, user_coins in enumerate(leaders):
        user = ctx.client.cache.get_user(
            user_coins.user_id
        ) or await ctx.client.rest.fetch_user(user_coins.user_id)

        pos = _pretty_pos(i + 1)
        nickname = user.display_name or user.global_name
        leaderboard.append(
            f"{pos}. {nickname}: {user_coins.amount} ({user_coins.deposit})"
        )

    emb = hikari.Embed(
        title=f"🚀 Богачи / {header}",
        description="\n".join(leaderboard),
        color=color,
    )
    pos = await coins.get_position(ctx.user.id)
    my_coins = await coins.get_or_create(ctx.user.id)
    if pos is not None:
        nick = ctx.user.display_name or ctx.user.global_name
        emb.add_field(
            "Ваше место", f"{_pretty_pos(pos)}. {nick}: {my_coins.deposit}"
        )
    await ctx.respond(emb)


# Загрузчики и выгрузчики плагина
# ===============================


@arc.loader
def loader(client: ChioClient) -> None:
    """Действия при загрузке плагина.

    Подключаем базу данных монетного хранилища.
    """
    plugin.add_table(CoinsTable)
    client.add_plugin(plugin)
