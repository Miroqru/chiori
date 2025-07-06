"""Библиотека работы с инвентарём.

Предоставляем каждому пользователю инвентарь.
Где он сможет хранить свои вещи.
Подразумевается что эти вещи будут типовыми и исчисляемыми.

Пока что в инвентаре не будет каких-либо ограничений на предметы.

Version: 0.6 (12)
Author: Milinuri Nirvalen
"""

from dataclasses import dataclass
from random import choice
from typing import Self

from asyncpg import Record

from chioricord.db import ChioDatabase, DBTable, ItemTable


class ItemIndexError(Exception):
    """При неполадках в базе данных.

    Возникает в редких случаях, когда что-то в базе данных работает
    не так, как должно.
    К примеру если указан неправильный ID в индекс предметов.
    """

    pass


@dataclass(slots=True)
class Item:
    """Представление предмета в индексе.

    Содержит основную информацию о предмете:
    - item_id: Уникальный идентификатор предмета.
    - name: Название предмета.
    - description: Краткое описание.
    - rare: Редкость предмета.
    """

    item_id: int
    name: str
    description: str
    rare: int

    @classmethod
    def new(
        cls, name: str, description: str = "Без описания", rare: int = 0
    ) -> Self:
        """Возвращает предмет со значениями по умолчанию."""
        return cls(0, name, description, rare)

    @classmethod
    def from_row(cls, row: Record) -> Self:
        """Возвращает предмет из строки базы данных."""
        return cls(int(row[0]), row[1], row[2], int(row[3]))


@dataclass(slots=True)
class InventoryItem:
    """Представление предмета в инвентаре пользователя."""

    index: Item
    amount: int


# Определение таблиц базы данных
# ==============================


class ItemIndex(ItemTable[Item]):
    """Индекс предметов.

    Хранит сведения о всех существующих предметах.
    """

    async def create_table(self) -> None:
        """Создаёт таблицы для базы данных."""
        await self.conn.execute(
            'CREATE TABLE IF NOT EXISTS "index" ('
            '"id"	SERIAL PRIMARY KEY,'
            '"name"	TEXT NOT NULL,'
            '"description"	TEXT NOT NULL,'
            '"rare"	INTEGER DEFAULT 0)'
        )

    async def get_index(self, rare: int | None = None) -> list[Item]:
        """Возвращает список предметов из индекса.

        Дополнительно можно указать редкость, для которой подобрать
        необходимо собрать список предметов.
        """
        if rare is not None:
            items = await self.conn.fetch(
                "SELECT * FROM 'index' WHERE rare=?", (rare,)
            )
        else:
            items = await self.conn.fetch("SELECT * FROM 'index'")
        return [Item.from_row(row) for row in items]

    async def get(self, id: int) -> Item | None:
        """Получает информацию о предмете по его id.

        Если такого предмета нет. вернёт None.
        """
        cur = await self.conn.fetchrow("SELECT * FROM 'index' WHERE id=$1", id)
        return None if cur is None else Item.from_row(cur)

    async def get_or_create(self, id: int) -> Item:
        """Получает информацию о предмете по его id.

        Если такого предмета нет. вернёт None.
        """
        item = await self.get(id)
        return Item.new("???") if item is None else item

    async def get_random(self, rare: int) -> Item | None:
        """Получает случайные предметы по их редкости."""
        cur = await self.conn.fetch("SELECT * FROM 'index' WHERE rare=$1", rare)
        if len(cur) == 0:
            return None
        return Item.from_row(choice(cur))

    async def add(self, item: Item) -> None:
        """Добавляет новый предмет в индекс."""
        await self.conn.execute(
            "INSERT INTO 'index' (name,description,rare) VALUES($1,$2,$3)",
            item.name,
            item.description,
            item.rare,
        )

    async def remove(self, item_id: int) -> None:
        """удаляет предмет из индекса по его id."""
        await self.conn.execute("DELETE FROM 'index' WHERE id=$1", item_id)


class Inventory(DBTable):
    """Представление инвентаря пользователя.

    Каждый пользователь может хранить несколько одинаковых предметов.
    """

    def __init__(self, db: ChioDatabase) -> None:
        super().__init__(db)
        self._index: ItemIndex | None = None

    def set_index(self, index: ItemIndex) -> None:
        """Устанавливает индекс для предметов."""
        self._index = index

    @property
    def index(self) -> ItemIndex:
        """Возвращает индекс предметов, если установлен."""
        if self._index is None:
            raise ValueError("You need to connect index before use it")
        return self._index

    async def create_table(self) -> None:
        """Создаёт таблицы для базы данных."""
        await self.conn.execute(
            'CREATE TABLE IF NOT EXISTS "inventory" ('
            '"user_id"	BIGINT,'
            '"item_id"	INTEGER,'
            '"amount"   INTEGER,'
            'FOREIGN KEY("item_id") REFERENCES "index"("id")'
            "ON UPDATE CASCADE)"
        )

    # Методы получения данных из инвентаря
    # ====================================

    async def get(self, user_id: int) -> list[InventoryItem]:
        """Получает инвентарь пользователя."""
        items = await self.conn.fetch(
            "SELECT item_id, amount FROM inventory WHERE user_id=$1", user_id
        )
        return [
            InventoryItem(
                await self.index.get_or_create(int(item[0])), int(item[1])
            )
            for item in items
        ]

    async def get_item(
        self, user_id: int, item_id: int
    ) -> InventoryItem | None:
        """получает информацию о предмете из инвентаря пользователя."""
        cur = await self.conn.fetchrow(
            "SELECT item_id, amount FROM inventory "
            "WHERE user_id=$1 AND item_id=$2",
            user_id,
            item_id,
        )
        if cur is None:
            return None

        index_item = await self.index.get(int(cur[0]))
        if index_item is None:
            raise ItemIndexError(f"{cur[0]} not found in Index DB.")
        return InventoryItem(index_item, int(cur[1]))

    # Примитивные методы
    # ==================

    async def add(self, user_id: int, item_id: int, amount: int) -> None:
        """Добавляет предметы в инвентарь пользователю."""
        await self.conn.execute(
            "INSERT INTO inventory VALUES($1, $2, $3)", user_id, item_id, amount
        )

    async def remove(self, user_id: int, item_id: int) -> None:
        """удаляет предметы из инвентаря пользователя."""
        await self.conn.execute(
            "DELETE FROM inventory WHERE user_id=$1 AND item_id=$2",
            user_id,
            item_id,
        )

    async def clear(self, user_id: int) -> None:
        """Очищает инвентарь пользователя."""
        await self.conn.execute(
            "DELETE FROM inventory WHERE user_id=$1", user_id
        )

    # Более высокоуровневые методы
    # ============================

    async def give(self, user_id: int, item_id: int, amount: int) -> None:
        """Выдаёт пользователю предметы."""
        in_inventory = await self.get_item(user_id, item_id)
        if in_inventory is None:
            await self.add(user_id, item_id, amount)
        else:
            await self.conn.execute(
                "UPDATE inventory SET amount=$1 "
                "WHERE user_id=$2 AND item_id=$3",
                in_inventory.amount + amount,
                user_id,
                item_id,
            )

    async def take(
        self, user_id: int, item_id: int, amount: int
    ) -> InventoryItem | None:
        """Забирает предметы из инвентаря пользователя."""
        in_inventory = await self.get_item(user_id, item_id)
        if in_inventory is None:
            return None
        elif amount > in_inventory.amount:
            return None
        elif amount == in_inventory.amount:
            await self.remove(user_id, item_id)
            return in_inventory
        else:
            await self.conn.execute(
                "UPDATE inventory SET amount=$1 "
                "WHERE user_id=$2 AND item_id=$3",
                in_inventory.amount - amount,
                user_id,
                item_id,
            )
            return InventoryItem(in_inventory.index, amount)

    async def move(
        self, item_id: int, amount: int, from_user: int, to_user: int
    ) -> bool:
        """Передаёт предметы между инвентарями."""
        take_item = await self.take(from_user, item_id, amount)
        if take_item is None:
            return False
        await self.give(to_user, item_id, amount)
        return True
