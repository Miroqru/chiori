"""Система репутации для Chioricord."""

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Literal, Self

from asyncpg import Record

from chioricord.db import DBTable

_REP_COOLDOWN = timedelta(minutes=10)


@dataclass
class UserReputation:
    """Репутация пользователя."""

    user_id: int
    positive: int
    negative: int
    next_rep: datetime

    @property
    def reputation(self) -> int:
        """Общая репутация пользователя."""
        return self.positive - self.negative

    @property
    def karma(self) -> float:
        """Карма пользователя. Процент репутации от позитивной."""
        return round((self.reputation / (self.positive or 1)) * 100, 2)

    @classmethod
    def from_row(cls, row: Record) -> Self:
        """Собирает значение из строки."""
        return cls(int(row[0]), int(row[1]), int(row[2]), row[3])


OrderBy = Literal["positive"] | Literal["negative"]


class ReputationTable(DBTable):
    """Репутация пользователя."""

    __tablename__ = "reputation"

    async def create_table(self) -> None:
        """Создаёт таблицу для базы данных."""
        await self.pool.execute(
            'CREATE TABLE IF NOT EXISTS "reputation" ('
            '"user_id"	BIGINT UNIQUE,'
            '"positive"	INTEGER NOT NULL,'
            '"negative"	INTEGER NOT NULL,'
            '"next_rep" TIMESTAMP NOT NULL DEFAULT NOW(),'
            'PRIMARY KEY("user_id"));'
        )

    async def get_leaders(self, order_by: OrderBy) -> list[UserReputation]:
        """Собирает таблицу лидеров по количеству монет."""
        cur = await self.pool.fetch(
            f"SELECT * FROM coins ORDER BY {order_by} LIMIT 10"
        )
        return [UserReputation.from_row(row) for row in cur]

    async def get_position(self, user_id: int) -> int | None:
        """Таблица лидеров по сообщениям."""
        cur = await self.pool.fetch(
            "SELECT COUNT(*) + 1 AS position FROM reputation "
            "WHERE positive > (SELECT positive FROM active "
            "WHERE user_id = $1)",
            user_id,
        )
        return int(cur[0][0]) if len(cur) > 0 else None

    async def get_user(self, user_id: int) -> UserReputation | None:
        """Получает пользователя по его id."""
        cur = await self.pool.fetchrow(
            "SELECT * FROM reputation WHERE user_id=$1", user_id
        )
        return None if cur is None else UserReputation.from_row(cur)

    async def get_or_create(self, user_id: int) -> UserReputation:
        """Получает пользователя или создаёт его."""
        user = await self.get_user(user_id)
        if user is not None:
            return user
        user = UserReputation(user_id, 0, 0, datetime.now())
        await self.create_user(user)
        return user

    async def create_user(self, user: UserReputation) -> None:
        """Создаёт нового пользователя."""
        await self.pool.execute(
            "INSERT INTO reputation VALUES($1,$2,$3)",
            user.user_id,
            user.positive,
            user.negative,
        )

    async def set_user(self, user: UserReputation) -> None:
        """Обновляет данные пользователя."""
        await self.pool.execute(
            "UPDATE reputation SET positive=$1,negative=$2,next_rep=$3 "
            "WHERE user_id=$4",
            user.positive,
            user.negative,
            user.next_rep,
            user.user_id,
        )

    async def add_positive(
        self, user_id: int, amount: int = 1
    ) -> UserReputation:
        """Добавляет позитивную репутацию пользователя."""
        user = await self.get_or_create(user_id)
        user.positive += amount
        await self.set_user(user)
        return user

    async def add_negative(
        self, user_id: int, amount: int = 1
    ) -> UserReputation:
        """Добавляет позитивную репутацию пользователя."""
        user = await self.get_or_create(user_id)
        user.negative += amount
        await self.set_user(user)
        return user

    async def bump_cooldown(self, user_id: int) -> None:
        """Обновляет счётчик перезарядки."""
        now = datetime.now()
        user = await self.get_or_create(user_id)
        user.next_rep = now + _REP_COOLDOWN
        await self.set_user(user)
