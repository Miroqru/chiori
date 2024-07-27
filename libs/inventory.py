"""Библиотека работы с инвентарём.

Предоставляем каждому пользователю инвернтарь.
Где он сможет хранить свои вещи.
Подразуемавается что эти вещи будут типовыми и стакающимися.

Пока что в инвентаре не будет каких-либо ограничений на предметы.

Version: 0.4 (10)
Author: Milinuri Nirvalen
"""

import json
from pathlib import Path
from typing import NamedTuple, Iterable

import aiosqlite

# Исключения в процессе работы с инвентарём
# =========================================

class ItemIndexError(Exception):
    """При неполадках в базе данных.

    Возникает в редких случаях, когда что-то в базе данных работает
    не так, как должно.
    К примеру если указан неправильный ID в индекс предметов.
    """
    pass


# Вспомогательные классы для хранения данных
# ==========================================

class Item(NamedTuple):
    item_id: int
    name: str
    description: str
    rare: int

    @classmethod
    def new(cls, name: str,
        description: str = "Без описания",
        rare: int = 0
    ):
        return Item(0, name, description, rare)

    @classmethod
    def from_row(cls, row: aiosqlite.Row):
        return Item(int(row[0]), row[1], row[2], int(row[3]))

class InventoryItem(NamedTuple):
    index: Item
    amount: int


# Индекс предметов
# ================

class ItemIndex:
    def __init__(self, index_path: Path):
        self.index_path = index_path
        self._index = None
        self._db: aiosqlite.Connection = None


    # Работа с базой данных
    # =====================

    async def connect(self) -> None:
        self._db = await aiosqlite.connect(self.index_path)

    async def close(self) -> None:
        if self._db is not None:
            await self._db.close()
            self._db = None

    async def create_tanles(self) -> None:
        await self._db.execute((
            'CREATE TABLE IF NOT EXISTS "index" ('
                '"id"	INTEGER,'
                '"name"	TEXT NOT NULL,'
                '"description"	TEXT NOT NULL,'
                '"rare"	INTEGER DEFAULT 0,'
                'PRIMARY KEY("id" AUTOINCREMENT)'
            ');'
        ))

    async def commit(self) -> None:
        await self._db.commit()


    # методы для получения данных
    # ===========================

    async def get_index(self, rare: int | None = None) -> list[Item]:
        res = []

        if rare is not None:
            cur =  await self._db.execute(
                "SELECT * FROM 'index' WHERE rare=?",
                (rare,)
            )
        else:
            cur =  await self._db.execute("SELECT * FROM 'index'")

        for row in await cur.fetchall():
            res.append(Item.from_row(row))
        return res

    async def get(self, item_id: int) -> Item | None:
        cur = await self._db.execute(
            "SELECT * FROM 'index' WHERE id=?",
            (item_id,)
        )
        row = await cur.fetchone()
        return None if row is None else Item.from_row(row)


    # Методы для работы с индексом предметов
    # ======================================

    async def add(self, item: Item) -> bool:
        await self._db.execute(
            "INSERT INTO 'index' (name,description,rare) VALUES(?,?,?)",
            (item.name, item.description, item.rare)
        )

    async def remove(self, item_id: int) -> bool:
        await self._db.execute(
            "DELETE FROM 'index' WHERE id=?", (item_id,)
        )


# классы для работы с инвентарём пользователя
# ===========================================

class Inventory:
    def __init__(self, inventory_path: Path, index: ItemIndex):
        self.inventory_path = inventory_path
        self.index = index
        self._db: aiosqlite.Connection | None = None


    # Методы для работы с базой данных
    # ================================

    async def connect(self) -> None:
        self._db = await aiosqlite.connect(self.inventory_path)

    async def close(self) -> None:
        if self._db is not None:
            await self._db.close()
            self._db = None

    async def create_tanles(self) -> None:
        await self._db.execute((
            'CREATE TABLE IF NOT EXISTS "inventory" ('
                '"user_id"	INTEGER,'
                '"item_id"	INTEGER,'
                '"amount"   INTEGER,'
                'FOREIGN KEY("item_id") REFERENCES "index"("id")'
                'ON UPDATE CASCADE'
            ');'
        ))

    async def commit(self) -> None:
        await self._db.commit()


    # Методы получения данных из инвентаря
    # ====================================

    async def get_items(self, user_id: int) -> list[InventoryItem]:
        res = []
        cur = await self._db.execute(
            "SELECT item_id, amount FROM inventory WHERE user_id=?",
            (user_id,)
        )
        for row in await cur.fetchall():
            res.append(InventoryItem(
                await self.index.get(int(row[0])),
                int(row[1])
            ))
        return res

    async def get(self, user_id: int, item_id: int) -> InventoryItem | None:
        cur = await self._db.execute(
            "SELECT item_id, amount FROM inventory WHERE user_id=? AND item_id=?",
            (user_id, item_id)
        )
        row = await cur.fetchone()
        if row is None:
            return None

        index_item = await self.index.get(int(row[0]))
        if index_item is None:
            raise ItemIndexError(f"{row[0]} not found in Index DB.")
        return InventoryItem(index_item, int(row[1]))


    # Примитивные методы
    # ==================

    async def add(self, user_id: int, item_id: int, amount: int) -> None:
        await self._db.execute(
            "INSERT INTO inventory VALUES(?, ?, ?)",
            (user_id, item_id, amount)
        )

    async def remove(self, user_id: int, item_id: int) -> None:
        await self._db.execute(
            "DELETE FROM inventory WHERE user_id=? AND item_id=?",
            (user_id, item_id)
        )

    async def clear(self, user_id: int) -> None:
        await self._db.execute(
            "DELETE FROM inventory WHERE user_id=?", (user_id,)
        )


    # Более высокоуровневые методы
    # ============================

    async def give(self, user_id: int, item_id: int, amount: int) -> None:
        in_inventory = await self.get(user_id, item_id)
        if in_inventory is None:
            await self.add(user_id, item_id, amount)
        else:
            await self._db.execute(
                "UPDATE inventory SET amount=? WHERE user_id=? AND item_id=?",
                (in_inventory.amount+amount, user_id, item_id)
            )

    async def take(self, user_id: int, item_id: int, amount: int) -> InventoryItem | None:
        in_inventory = await self.get(user_id, item_id)
        if in_inventory is None:
            return None
        elif amount > in_inventory.amount:
            return None
        elif amount == in_inventory.amount:
            await self.remove(user_id, item_id)
            return in_inventory
        else:
            await self._db.execute(
                "UPDATE inventory SET amount=? WHERE user_id=? AND item_id=?",
                (in_inventory.amount-amount, user_id, item_id)
            )
            return InventoryItem(in_inventory.index, amount)


    # Работа с несколькими инвентарями
    # ================================

    async def move(self, item_id: int, amount: int, from_user: int, to_user: int) -> bool:
        take_item = await self.take(from_user, item_id, amount)
        if take_item is None:
            return False
        await self.give(to_user, item_id, amount)


class UserInventory:

    def __init__(self, user_id: int, inventory: Inventory):
        self.user_id = user_id
        self.inventory = inventory


    # Получение данных из инвентаря
    # =============================

    async def get_items(self) -> list[InventoryItem]:
        return await self.inventory.get_items(self.user_id)

    async def get(self, item_id: int) -> InventoryItem | None:
        return await self.inventory.get(self.user_id, item_id)


    # Работа с инвентарём пользователя
    # ================================

    async def give(self, item_id: int, amount: int) -> None:
        await self.inventory.give(self.user_id, item_id, amount)

    async def take(self, item_id: int, amount: int) -> InventoryItem | None:
        return await self.inventory.take(self.user_id, item_id, amount)


    # Работа с несколькими инвентарями
    # ================================

    async def move(self, to_user: int, item_id: int, amount: int) -> bool:
        return await self.inventory.move(item_id, amount, self.user_id, to_user)
