from enum import Enum

from pathlib import Path
from typing import NamedTuple, Self

import aiosqlite


class CoinsData(NamedTuple):
    user_id: int
    amount: int
    deposite: int

    @property
    def balance(self) -> int:
        return self.amount + self.deposite

    @classmethod
    def from_row(cls, row: aiosqlite.Row) -> Self:
        return CoinsData(int(row[0]), int(row[1]), int(row[2]))


class OrderBy(Enum):
    AMOUNT = "amount"
    DEPOSITE = "deposite"
    ALL = "amount+deposite"


# Будет капать на баланс каждый день
DEPOSITE_PERCENT = 0.05


class CoinDB:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._db: aiosqlite.Connection | None = None

    # Методы для работы с файлом базы данных
    # ======================================

    async def connect(self) -> None:
        self._db = await aiosqlite.connect(self.db_path)

    async def close(self) -> None:
        if self._db is not None:
            await self._db.close()
            self._db = None

    async def create_tables(self) -> None:
        await self._db.execute((
            'CREATE TABLE IF NOT EXISTS "coins" ('
            '"user_id"	INTEGER UNIQUE,'
            '"amount"	INTEGER NOT NULL,'
            '"deposite"	INTEGER NOT NULL,'
            'PRIMARY KEY("user_id")'
            ');'
            ))

    async def commit(self) -> None:
        await self._db.commit()


    # методы получения данных из базы
    # ===============================

    async def get_leaderboard(self, order_by: OrderBy) -> list[CoinsData]:
        cur: aiosqlite.Cursor = await self._db.execute(
            f"SELECT * FROM coins ORDER BY {order_by.value} DESC",
        )
        res = []
        for row in await cur.fetchall():
            res.append(CoinsData.from_row(row))
        return res

    async def get(self, user_id: int) -> CoinsData | None:
        cur: aiosqlite.Cursor = await self._db.execute(
            "SELECT * FROM coins WHERE user_id=?", (user_id,)
        )
        row = await cur.fetchone()
        if row is not None:
            return CoinsData.from_row(row)
        return None

    async def get_or_create(self, user_id: int) -> CoinsData:
        coin_data = await self.get(user_id)
        return coin_data if coin_data is not None else CoinsData(user_id, 0, 0)


    # Методы прямого изменения данных
    # ===============================

    async def create(self, coins: CoinsData) -> None:
        await self._db.execute(
            "INSERT INTO coins VALUES(?,?,?)",
            (coins.user_id, coins.amount, coins.deposite)
        )

    async def delete(self, user_id: int) -> None:
        await self._db.execute(
            "DELETE FROM coins WHERE user_id=?", (user_id,)
        )


    async def set(self, coins: CoinsData) -> None:
        user_data = await self.get(user_id=coins.user_id)
        if user_data is None:
           await self.create(coins)
        else:
            await self._db.execute(
                "UPDATE coins SET amount=?,deposite=? WHERE user_id=?",
                (coins.amount, coins.deposite, coins.user_id)
            )


    # Методы изменения данных
    # =======================

    async def give(self, user_id: int, amount: int) -> None:
        user_data = await self.get(user_id)
        if user_data is None:
            await self.create(CoinsData(user_id, amount, 0))
        else:
            await self._db.execute(
                "UPDATE coins SET amount=? WHERE user_id=?",
                (
                    max(user_data.amount + amount, 0),
                    user_id
                )
            )

    async def take(self, user_id: int, amount: int) -> bool:
        if amount < 0:
            return False

        user_data = await self.get(user_id)
        if user_data is None:
            return False
        if user_data.amount < amount:
            return False
        await self._db.execute(
            "UPDATE coins SET amount=? WHERE user_id=?",
            (user_data.amount-amount, user_id)
        )
        return True

    async def to_deposite(self, user_id: int, amount: int) -> bool:
        if amount < 0:
            return False

        user_data = await self.get(user_id)
        if user_data is None:
            return False
        if user_data.amount < amount:
            return False
        await self._db.execute(
            "UPDATE coins SET amount=?, deposite=? WHERE user_id=?",
            (user_data.amount-amount, user_data.deposite+amount, user_id)
        )
        return True

    async def from_deposite(self, user_id: int, amount: int) -> bool:
        if amount < 0:
            return False

        user_data = await self.get(user_id)
        if user_data is None:
            return False
        if user_data.deposite < amount:
            return False
        await self._db.execute(
            "UPDATE coins SET amount=?, deposite=? WHERE user_id=?",
            (user_data.amount+amount, user_data.deposite-amount, user_id)
        )
        return True

    async def move(self, amount: int, from_id: int, to_id: int) -> bool:
        status = await self.take(from_id, amount)
        if status:
            await self.give(to_id, amount)
        return status
