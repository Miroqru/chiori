"""Библиотека работы с инвентарём.

Предоставляем каждому пользователю инвернтарь.
Где он сможет хранить свои вещи.
Подразуемавается что эти вещи будут типовыми и стакающимися.

Пока что в инвентаре не будет каких-либо ограничений на предметы.

Version: 0.1 (1)
Author: Milinuri Nirvalen
"""

import json
from pathlib import Path
from typing import NamedTuple, Iterable

import aiosqlite


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


class ItemIndex:
    def __init__(self, index_path: Path):
        self.index_path = index_path
        self._index = None
        self._db: aiosqlite.Connection = None


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


    # Методы для работы с индексом
    # ============================

    async def add(self, item: Item) -> bool:
        await self._db.execute(
            "INSERT INTO 'index' (name,description,rare) VALUES(?,?,?)",
            (item.name, item.description, item.rare)
        )

    async def remove(self, item_id: int) -> bool:
        await self._db.execute(
            "DELETE FROM 'index' WHERE id=?", (item_id,)
        )


class Inventory:
    def __init__(self, index: ItemIndex, user_id: int):
        self.index = index
        self.user_id = user_id


    # Методы получения данных из инвенторя
    # ====================================

    def get_items(self) -> list[InventoryItem]:
        pass

    def get(self, item_id) -> InventoryItem | None:
        pass


    # Методы для работы с инвентарём
    # ==============================

    def give(self, item: Item, amount: int) -> bool:
        pass

    def take(self, item_id, amount: int) -> InventoryItem | None:
        pass
