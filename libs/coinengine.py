"""Монетная система.

Часть экономической системы.
Предоставляет базу данных для работы с валютой пользователя.

Version: v2.1 (9)
Author: Milinuri Nirvalen
"""

from dataclasses import dataclass
from enum import Enum
from typing import Self

from asyncpg import Record

from chioricord.db import DBTable

# Будет капать на баланс каждый день
DEPOSIT_PERCENT = 0.05


@dataclass(slots=True, frozen=True)
class UserCoins:
    """Монеты пользователя.

    Содержит баланс пользователя.
    Сколько у него находится на руках и в банке.
    """

    user_id: int
    amount: int
    deposit: int

    @property
    def balance(self) -> int:
        """Считает полный баланс пользователя."""
        return self.amount + self.deposit

    @classmethod
    def from_row(cls, row: Record) -> Self:
        """Собирает значение из строки базы данных."""
        return cls(int(row[0]), int(row[1]), int(row[2]))


class OrderBy(Enum):
    """По каким значениям можно сортировать таблицу лидеров."""

    AMOUNT = "amount"
    deposit = "deposit"
    ALL = "amount+deposit"


class CoinsTable(DBTable):
    """Таблица монет пользователя."""

    __tablename__ = "coins"

    async def create_table(self) -> None:
        """Создаёт таблицу для базы данных."""
        await self.pool.execute(
            'CREATE TABLE IF NOT EXISTS "coins" ('
            '"user_id"	BIGINT UNIQUE,'
            '"amount"	INTEGER NOT NULL,'
            '"deposit"	INTEGER NOT NULL,'
            'PRIMARY KEY("user_id")'
            ");"
        )

    async def get_leaders(self, order_by: OrderBy) -> list[UserCoins]:
        """Собирает таблицу лидеров по количеству монет."""
        cur = await self.pool.fetch(
            f"SELECT * FROM coins ORDER BY {order_by.value} LIMIT 10"
        )
        return [UserCoins.from_row(row) for row in cur]

    async def get_user(self, user_id: int) -> UserCoins | None:
        """Получает пользователя по его id."""
        cur = await self.pool.fetchrow(
            "SELECT * FROM coins WHERE user_id=$1", user_id
        )
        if cur is None:
            return None
        return UserCoins.from_row(cur)

    async def get_or_create(self, user_id: int) -> UserCoins:
        """Получает пользователя или создаёт его."""
        user = await self.get_user(user_id)
        return user if user is not None else UserCoins(user_id, 0, 0)

    # Методы прямого изменения данных
    # ===============================

    async def create_user(self, coins: UserCoins) -> None:
        """Создаёт нового пользователя."""
        await self.pool.execute(
            "INSERT INTO coins VALUES($1,$2,$3)",
            coins.user_id,
            coins.amount,
            coins.deposit,
        )

    async def set_user(self, coins: UserCoins) -> None:
        """Обновляет данные пользователя."""
        user = await self.get_user(user_id=coins.user_id)
        if user is None:
            await self.create_user(coins)
        else:
            await self.pool.execute(
                "UPDATE coins SET amount=$1,deposit=$2 WHERE user_id=$3",
                coins.amount,
                coins.deposit,
                coins.user_id,
            )

    # Методы изменения данных
    # =======================

    async def _update_amount(self, user_id: int, amount: int) -> bool:
        await self.pool.execute(
            "UPDATE coins SET amount=$1 WHERE user_id=$2", amount, user_id
        )
        return True

    async def give(self, user_id: int, amount: int) -> None:
        """Выдаёт пользователю монеты."""
        user = await self.get_user(user_id)
        if user is None:
            await self.create_user(UserCoins(user_id, amount, 0))
            return None
        await self._update_amount(user_id, max(user.amount + amount, 0))

    async def take(self, user_id: int, amount: int) -> bool:
        """Вычитает монеты с баланса пользователя."""
        if amount < 0:
            return False

        user = await self.get_user(user_id)
        if user is None or user.amount < amount:
            return False

        return await self._update_amount(user_id, user.amount - amount)

    async def to_deposit(self, user_id: int, amount: int) -> bool:
        """Ложит монеты на депозит."""
        if amount < 0:
            return False

        user = await self.get_user(user_id)
        if user is None:
            return False
        if user.amount < amount:
            return False
        await self.pool.execute(
            "UPDATE coins SET amount=$1, deposit=$2 WHERE user_id=$3",
            user.amount - amount,
            user.deposit + amount,
            user_id,
        )
        return True

    async def from_deposit(self, user_id: int, amount: int) -> bool:
        """Забирает монеты с депозита."""
        if amount < 0:
            return False

        user = await self.get_user(user_id)
        if user is None:
            return False
        if user.deposit < amount:
            return False
        await self.pool.execute(
            "UPDATE coins SET amount=$1, deposit=$2 WHERE user_id=$3",
            user.amount + amount,
            user.deposit - amount,
            user_id,
        )
        return True

    async def move(self, amount: int, from_id: int, to_id: int) -> bool:
        """Перемещает монеты между двумя пользователями."""
        status = await self.take(from_id, amount)
        if status:
            await self.give(to_id, amount)
        return status
