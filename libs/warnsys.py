"""Система предупреждения для бота.

Version: 0.1 (2)
Author: Milinuri Nirvalen
"""

from pathlib import Path
from typing import NamedTuple

import aiosqlite


class WarnInfo(NamedTuple):
    """Информация о предупреждении для пользователя."""

    id: int
    guild_id: int
    from_user: int
    to_user: int
    start_time: int
    end_time: int
    reason: str


class WarnSys:
    """Глобальная система предупреждений участником сервера."""

    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self._db: aiosqlite.Connection = None

    # Работа с файлом базы данных
    # ===========================

    async def connect(self) -> None:
        """Подключается к базе данных."""
        self._db = await aiosqlite.connect(self.db_path)

    async def close(self) -> None:
        """Закрывает соединение с базой данных."""
        if self._db is not None:
            await self._db.close()
            self._db = None

    async def create_tables(self) -> None:
        """Создаёт таблицы для базы данных."""
        await self._db.execute(
            'CREATE TABLE "warns" ('
            '"id"	INTEGER,'
            '"guild_id"	INTEGER,'
            '"from_user"	INTEGER,'
            '"to_user"	INTEGER,'
            '"start_time"	INTEGER NOT NULL,'
            '"end_time"	INTEGER NOT NULL,'
            '"reason"	TEXT,'
            'PRIMARY KEY("id" AUTOINCREMENT)'
            ");"
        )

    # Работа с предупреждениями пользователей
    # =======================================
