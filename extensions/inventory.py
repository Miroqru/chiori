"""Позволяет взаимодействовать с инвентарём.

Предоставляет
-------------

- /index: Все доступных предметов в базе данных.
- /index [item_id]: Детальную информацию о предмете.
- /inventory: Предметы в ваших карманах.

Version: v0.1.1 (4)
Author: Milinuri Nirvalen
"""

from pathlib import Path
from typing import NamedTuple

import arc
import hikari
from loguru import logger

from libs import inventory

# Глобальные переменные
# =====================

DB_PATH = Path("bot_data/items.db")
item_index = inventory.ItemIndex(DB_PATH)
inv = inventory.Inventory(DB_PATH, item_index)
plugin = arc.GatewayPlugin("Inventory")


# Вспомогательное определение редкости
# ===================================


class RareInfo(NamedTuple):
    """Информация о редкости предмета.

    - tier: Какого класса предмет.
    - icon: Иконочка для представления предмета.
    - chance: С каким шансом может выпасть предмет.
    - max_count: Максимальное количество предметов, которое может выпасть.
    """

    name: str
    desc: str
    icon: str
    color: int

    def __str__(self) -> str:
        """Преобразовать в строку."""
        return self.icon


_RARE_GRADES = [
    RareInfo(
        name="Бесполезный",
        desc=(
            "Зачем вы только это подобрали? "
            "Абсолютно бесполезные вещи, так и стоят копейки."
        ),
        icon="",
        color=0x333333,
    ),
    RareInfo(
        name="Обычный",
        desc=(
            "Достаточно бытовые вещи, может запчасти, не составит труда найти "
            "такие вещи в магазинах."
        ),
        icon="⚪",
        color=0xCCCCCC,
    ),
    RareInfo(
        name="Необычный",
        desc=(
            "Порой это не то, что ожидаешь встретить в подобных местах. "
            "Может иногда мы просто не обращаем на них внимание."
        ),
        icon="🟢",
        color=0x00FFCC,
    ),
    RareInfo(
        name="Редкий",
        desc=(
            "Хм, а вот это уже интересная вещица, Она уже будет стоящей. "
            "Мы с радостью её у вас купим."
        ),
        icon="🔵",
        color=0x00CCFF,
    ),
]


# Вспомогательные функции для отображения
# =======================================


def item_status(item: inventory.Item) -> str:
    """Собирает краткую информацию о предмете."""
    return f"`{item.item_id}`: {_RARE_GRADES[item.rare]}{item.name}"


def index_status(items: list[inventory.Item]) -> hikari.Embed:
    """Собирает информацию о всех предметах."""
    list_items = ""
    for item in items:
        list_items += f"\n- {item_status(item)}"

    return hikari.Embed(
        title="📦 Индекс предметов",
        description=list_items,
        color=hikari.colors.Color(0xFF66CC),
    ).add_field(
        name="Подсказка", value="`/index [item_id]` - для подробной информации"
    )


def item_info(item: inventory.Item) -> hikari.Embed:
    """Собирает информацию о предмете."""
    rare_info = _RARE_GRADES[item.rare]
    return hikari.Embed(
        title=item.name,
        description=item.description,
        color=hikari.colors.Color(rare_info.color),
    ).add_field(name="Редкость", value=f"{rare_info.name}\n> {rare_info.desc}")


@plugin.include
@arc.slash_command("index", description="Информацию о предмете.")
async def index_handler(
    ctx: arc.GatewayContext,
    item_id: arc.Option[
        int | None, arc.IntParams("ID предмета из индекса предметов")
    ] = None,
    index: inventory.ItemIndex = arc.inject(),
) -> None:
    """Просмотр всех предметов и информации о конкретном предмете."""
    if item_id is None:
        items = await index.get_index()
        await ctx.respond(embed=index_status(items))
        return

    item = await index.get(item_id)
    if item is None:
        await ctx.respond("👀 Предмета с таким ID не существует")
    else:
        await ctx.respond(embed=item_info(item))


@plugin.include
@arc.slash_command("inventory", description="Содержимое ваших карманов.")
async def user_inventory(
    ctx: arc.GatewayContext, inv: inventory.Inventory = arc.inject()
) -> None:
    """Содержимое инвентаря пользователя."""
    items = await inv.get_items(ctx.user.id)
    items_list = ""
    for item in items:
        items_list += f"\n- {item_status(item.index)} (x{item.amount})"
    emb = hikari.Embed(title="📦 Ваш инвентарь", description=items_list)
    await ctx.respond(emb)


# Загрузчики и выгрузчики плагина
# ===============================


@plugin.listen(arc.events.StartedEvent)
async def start_plugin(event: arc.events.StartedEvent) -> None:
    """Подключаемся к базам данных при запуске бота."""
    logger.info("Connect to index/inventory DB")
    await item_index.connect()
    await inv.connect()

    logger.info("Create missing tables")
    await item_index.create_tables()
    await inv.create_tables()


@plugin.listen(arc.events.StoppingEvent)
async def stop_plugin(event: arc.events.StoppingEvent) -> None:
    """Время отключаться от баз данных, вместе с отключением бота."""
    logger.info("Close connect to index/inventory DB")
    await inv.commit()
    await inv.close()

    await item_index.commit()
    await item_index.close()


@arc.loader
def loader(client: arc.GatewayClient) -> None:
    """Действия при загрузке плагина.

    Подключаем базу данных индекса предметов и инвентаря.
    """
    client.add_plugin(plugin)
    client.set_type_dependency(inventory.ItemIndex, item_index)
    client.set_type_dependency(inventory.Inventory, inv)


@arc.unloader
def unloader(client: arc.GatewayClient) -> None:
    """Действия при выгрузке плагина.

    Завершаем подключение к базе данных предметов и инвентаря.
    """
    client.remove_plugin(plugin)
