"""Позволяет взаимодействовать с инвентарём.

Предоставляет
-------------

- /index: Просмотр всех доступных прдеметов в базе данных.
- /index [item_id]: Просмотреть детальную информацию о предмете.
- /inventory: Лежащие в ваших карманах предметы.

Version: v0.1
Author: Milinuri Nirvalen
"""

from typing import NamedTuple
from pathlib import Path

import arc
import hikari

from libs import inventory

from loguru import logger

# Глобальные переменные
# =====================

DB_PATH = Path("bot_data/itemlib.db")
item_index = inventory.ItemIndex(DB_PATH)
inv = inventory.Inventory(DB_PATH, item_index)
plugin = arc.GatewayPlugin("Inventory")


# Вспомогательное определние редкости
# ===================================
# Можект после переехать в базу данных

class RareInfo(NamedTuple):
    name: str
    desc: str
    icon: str
    color: int

    def __str__(self) -> str:
        return self.icon

_RARE_GRADES = [
    RareInfo(
        name="Бесполезный",
        desc=(
            "Зачем вы только это подобрали? "
            "Абсюлютно бесполезные вещи, так и стоят копейки."
        ),
        icon="",
        color=0x333333
    ),
    RareInfo(
        name="Обычный",
        desc=(
            "Досаточно бытовые вещи, может запчасти, не составит труда найти "
            "такие вещи в магазинах."
        ),
        icon="⚪",
        color=0xcccccc
    ),
    RareInfo(
        name="Необычный",
        desc=(
            "Порой это не то, что ожидаешь встретить в подобных местах. ",
            "Может иногда мы просто не обращаем на них внимание."
        ),
        icon="🟢",
        color=0x00ffcc
    ),
    RareInfo(
        name="Редкий",
        desc=(
            "Хм, а вот это уже интересная вещица, Она уже будет стоящей. "
            "Мы с радостью её у вас купим."
        ),
        icon="🔵",
        color=0x00ccff
    )
]


# Вспомогательные функции для отображаения
# ========================================

def item_status(item: inventory.Item) -> str:
    return f"`{item.item_id}`: {_RARE_GRADES[item.rare]}{item.name}"


# Динамические сообщения
# ======================

def index_status(items: list[inventory.Item]) -> hikari.Embed:
    list_items = ""
    for item in items:
        list_items += f"\n- {item_status(item)}"

    return hikari.Embed(
        title="📦 Индекс предметов",
        description=list_items,
        color=hikari.colors.Color(0xff66cc)
    ).add_field(
        name="Подсказка",
        value=(
            "`/index [item_id]` - для подробной информации"
        )
    )

def item_info(item: inventory.Item) -> hikari.Embed:
    rare_info = _RARE_GRADES[item.rare]
    return hikari.Embed(
        title=item.name,
        description=item.description,
        color=hikari.colors.Color(rare_info.color)
    ).add_field(
        name="Редкость",
        value=f"{rare_info.name}\n> {rare_info.desc}"
    )


# Команды для работы с индексом предметов
# =======================================

@plugin.include
@arc.slash_command("index", description="Получить информациб о предмете.")
async def index_handler(
    ctx: arc.GatewayContext,
    item_id: arc.Option[
        int | None, arc.IntParams("ID прдемета из индекса предметов")
    ] = None,
    index: inventory.ItemIndex = arc.inject()
) -> None:
    if item_id is None:
        items = await index.get_index()
        return await ctx.respond(embed=index_status(items))

    item = await index.get(item_id)
    if item is None:
        await ctx.respond("👀 Прдемета с таким ID не существует")
    else:
        await ctx.respond(embed=item_info(item))


# Работа с инвентарём
# ===================

@plugin.include
@arc.slash_command("inventory", description="Содержимое вашего инвенторя.")
async def inv_handler(
    ctx: arc.GatewayContext,
    inv: inventory.Inventory = arc.inject()
) -> None:
    items = await inv.get_items(ctx.user.id)
    items_list = ""
    for item in items:
        items_list += f"\n- {item_status(item.index)} (x{item.amount})"
    embed = hikari.Embed(
        title="Ваш инвентарь",
        description=items_list
    )

    await ctx.respond(embed=embed)


# Загрузчики и выгрузчики плагина
# ===============================

@plugin.listen(arc.events.StartedEvent)
async def connect(event: arc.events.StartedEvent):
    """Подключаемся к базам данных при запуске бота."""
    logger.info("Connect to index/inventory DB")
    await item_index.connect()
    await inv.connect()

    logger.info("Create missing tables")
    await item_index.create_tanles()
    await inv.create_tanles()

@plugin.listen(arc.events.StoppingEvent)
async def disconnect(event: arc.events.StoppingEvent):
    """Время отключаться от баз данных, вместе с отключением бота."""
    logger.info("Close connect to index/inventory DB")
    await inv.commit()
    await inv.close()

    await item_index.commit()
    await item_index.close()


# ----------------------------------------------------------------------

@arc.loader
def loader(client: arc.GatewayClient) -> None:
    """Действия при загрузке плагина.

    Подключаем базу данных индекса предметов и инвенторя.
    """
    client.add_plugin(plugin)
    client.set_type_dependency(inventory.ItemIndex, item_index)
    client.set_type_dependency(inventory.Inventory, inv)

@arc.unloader
def unloader(client: arc.GatewayClient) -> None:
    """Действия при выгрузке плагина.

    Завершаем подключение к базе данных предметов и инвенторя.
    """
    client.remove_plugin(plugin)
