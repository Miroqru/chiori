"""Статистика использования команд в боте."""

from dataclasses import dataclass
from datetime import datetime
from typing import Self

from asyncpg import Record

from chioricord.db import DBTable


@dataclass(frozen=True, slots=True)
class CommandUsage:
    """Кто использовал команду."""

    user_id: int
    guild_id: int | None
    command: str
    used_at: datetime

    @classmethod
    def from_row(cls, row: Record) -> Self:
        """Собирает команду из базы данных."""
        return cls(row[0], row[1], row[2], row[3])


class CommandsTable(DBTable):
    """Таблица использования команд пользователями."""

    __tablename__ = "commands_stat"

    async def create_table(self) -> None:
        """Создаёт таблицы для базы данных."""
        await self.pool.execute(
            "CREATE TABLE IF NOT EXISTS commands_stat ("
            "id SERIAL NOT NULL PRIMARY KEY,"
            "user_id BIGINT NOT NULL,"
            "guild_id BIGINT,"
            "command TEXT NOT NULL,"
            "used_at TIMESTAMP NOT NULL DEFAULT NOW())"
        )

    async def add_command(
        self, user_id: int, guild_id: int | None, command: str
    ) -> None:
        """Create a new user record in the database."""
        await self.pool.execute(
            f"INSERT INTO {self.__tablename__}(user_id, guild_id, command) VALUES($1,$2,$3)",
            user_id,
            guild_id,
            command,
        )
