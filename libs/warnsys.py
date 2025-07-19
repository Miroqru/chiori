"""Система предупреждения для бота.

Version: 0.2a1 (3)
Author: Milinuri Nirvalen
"""

from dataclasses import dataclass
from pathlib import Path

import aiosqlite

from chioricord.db import DBTable


@dataclass(slots=True)
class WarnInfo:
    """Информация о предупреждении для пользователя."""

    id: int
    guild_id: int
    from_user: int
    to_user: int
    start_time: int
    end_time: int
    reason: str


class WarnSys(DBTable):
    """Глобальная система предупреждений участником сервера."""

    async def create_tables(self) -> None:
        """Создаёт таблицы для базы данных."""
        await self.pool.execute(
            'CREATE TABLE "warns" ('
            '"id"	SERIAL PRIMARY KEY,'
            '"guild_id"	BIGINT,'
            '"from_user"	BIGINT,'
            '"to_user"	BIGINT,'
            '"start_time"	TIMESTAMP NOT NULL,'
            '"end_time"	TIMESTAMP NOT NULL,'
            '"reason"	TEXT,'
        )
