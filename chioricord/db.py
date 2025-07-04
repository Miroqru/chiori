"""База данных.

предоставляет методы для работы с общей базой данных Postgres.
"""

from abc import ABC, abstractmethod
from typing import Generic, TypeVar

import arc
import asyncpg
from loguru import logger


class ChioDatabase:
    """База данных Chiori.

    Глобальное хранилище для хранение данных бота.
    """

    def __init__(self, dsn: str, client: arc.GatewayClient) -> None:
        self.dsn = dsn
        self.client = client

        self._conn: asyncpg.Connection | None = None
        self._tables: dict[str, DBTable] = {}

    # Управление базой данных
    # =======================

    @property
    def conn(self) -> asyncpg.Connection:
        """Возвращает подключение к базе данных."""
        if self._conn is None:
            raise ValueError("You need to connect database")
        return self._conn

    async def connect(self) -> None:
        """Подключение к базе данных."""
        logger.info("Connect to Chio database")
        self._conn = await asyncpg.connect(self.dsn)

    async def close(self) -> None:
        """Закрывает подключение к базе данных."""
        logger.info("Shutdown Chio database")
        if self._conn is None:
            logger.warning("No active connection to close")
            return
        await self._conn.close()

    # Управление таблицами базы данных
    # ================================

    async def create_tables(self) -> None:
        """Создаёт таблицы для базы данных."""
        logger.info("Create tables")
        for name, table in self._tables.items():
            logger.debug("Create table {}", name)
            await table.create_table()

    def register(self, name: str, proto: type["DBTable"]) -> None:
        """Регистрирует таблицу в базу данных."""
        logger.info("Register table {}", name)
        if name in self._tables:
            raise ValueError(f"Table {name} already registered")

        table = proto(self)
        self._tables[name] = table
        self.client.set_type_dependency(proto, table)


class DBTable(ABC):
    """Таблица в базе данных."""

    def __init__(self, db: ChioDatabase) -> None:
        self._db = db

    @property
    def conn(self) -> asyncpg.Connection:
        """Возвращает подключение к базе данных."""
        return self._db.conn

    @abstractmethod
    async def create_table(self) -> None:
        """Создаёт таблицу в базе данных, если ещё не была создана."""


_I = TypeVar("_I")


class ItemTable(DBTable, Generic[_I]):
    @abstractmethod
    async def get(self, id: int) -> _I | None:
        """Создаёт таблицу в базе данных, если ещё не была создана."""

    @abstractmethod
    async def get_or_create(self, id: int) -> _I:
        """Создаёт таблицу в базе данных, если ещё не была создана."""
