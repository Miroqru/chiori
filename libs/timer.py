"""Таймеры пользователя.

Предоставляет общий API для работы с таймерами.
Таймеры используются чтобы блокировать выполнение операций.
Рекомендуется использовать более длительные таймеры.

Version: v1.0 (1)
Author: Milinuri Nirvalen
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Self

from asyncpg import Record

from chioricord.api import DBTable


@dataclass(frozen=True, slots=True)
class UserTimer:
    """Описание пользовательского таймера."""

    user_id: int
    name: str
    reset_time: datetime

    @classmethod
    def from_row(cls, row: Record) -> Self:
        """Собирает значение из строки базы данных."""
        return cls(row[0], row[1], row[2])


class ChannelsTable(DBTable, table="timers"):
    """Таблица таймеров пользователя.

    Пользователь может задавать таймеры на определённое действие.
    Часто используется в других библиотеках.
    """

    async def create_table(self) -> None:
        """Создаёт таблицы для базы данных."""
        await self.pool.execute(
            "CREATE TABLE IF NOT EXISTS timers ("
            "user_id BIGINT NOT NULL,"
            "name VARCHAR(32) NOT NULL,"
            "reset_tome TIMESTAMP NOT NULL,"
            "PRIMARY KEY (user_id, name))"
        )

    async def get(self, user_id: int, name: str) -> UserTimer | None:
        """Возвращает таймер пользователя по имени."""
        cur = await self.pool.fetchrow(
            "SELECT * FROM timers WHERE user_id=$1 AND name=$2",
            user_id,
            name,
        )
        if cur is None:
            return None

        timer = UserTimer.from_row(cur)
        if timer.reset_time <= datetime.now():
            await self.reset(timer.user_id, timer.name)
            return None

        return timer

    async def set(self, timer: UserTimer) -> None:
        """Устанавливает новое значение для таймера."""
        await self.pool.execute(
            "INSERT INTO timers (user_id, name, reset_time) "
            "VALUES ($1, $2, $3) "
            "ON CONFLICT (user_id, name) DO UPDATE "
            "SET reset_time = $3;",
            timer.user_id,
            timer.name,
            timer.reset_time,
        )

    async def reset(self, user_id: int, name: str) -> None:
        """Сбрасывает таймер по имени."""
        await self.pool.execute(
            "DELETE FROM timers WHERE user_id=$1 AND name=$2", user_id, name
        )

    async def select(self, user_id: int) -> dict[str, datetime]:
        """Возвращает все таймеры пользователя."""
        cur = await self.pool.fetch(
            "SELECT * FROM timers WHERE user_id=$1", user_id
        )
        timers: dict[str, datetime] = {}
        for row in cur:
            timer = UserTimer.from_row(row)
            if timer.reset_time <= datetime.now():
                await self.reset(timer.user_id, timer.name)
                continue

            timers[timer.name] = timer.reset_time
        return timers

    async def clear(self, user_id: int) -> None:
        """Сбрасывает все таймеры пользователя."""
        await self.pool.execute("DELETE FROM timers WHERE user_id=$1", user_id)
