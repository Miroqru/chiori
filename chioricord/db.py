"""База данных.

предоставляет методы для работы с общей базой данных Postgres.
"""

import time
from abc import ABC, abstractmethod

import arc
import asyncpg
from loguru import logger


class DBTable(ABC):
    """Базовый класс для всех таблиц базы данных."""

    __tablename__: str

    def __init__(self, db: "ChioDB") -> None:
        self._db = db

    @abstractmethod
    async def create_table(self) -> None:
        """Создаёт таблицу в базе данных, если ещё не была создана."""

    @property
    def pool(self) -> asyncpg.Pool:
        """Возвращает подключение к базе данных."""
        return self._db.pool


class ChioDB:
    """База данных Chiori.

    Глобальное хранилище для хранение данных бота.
    Работает поверх Postgres пула подключений.
    """

    def __init__(self, dsn: str, client: arc.GatewayClient) -> None:
        self.dsn = dsn
        self.client = client
        self.app = client.app

        self._pool: asyncpg.Pool | None = None
        self._tables: dict[str, DBTable] = {}

    async def ping(self) -> float:
        """просчитывает пинг до базы данных."""
        start = time.monotonic()
        await self.pool.execute("SELECT 1")
        ping = (time.monotonic() - start) * 1000
        return ping

    @property
    def pool(self) -> asyncpg.Pool:
        """Возвращает подключение к базе данных."""
        if self._pool is None:
            raise ValueError("You need to connect to database pool before")
        return self._pool

    async def connect(self) -> None:
        """Подключение к базе данных."""
        self._pool = await asyncpg.create_pool(self.dsn)

    async def close(self) -> None:
        """Закрывает подключение к базе данных."""
        logger.info("Shutdown Chio database")
        if self._pool is None:
            logger.warning("No active connection to close")
            return
        await self._pool.close()

    def register(self, table: type[DBTable]) -> None:
        """Регистрирует таблицу в базу данных."""
        logger.info("Register table {}", table)
        if table.__tablename__ in self._tables:
            raise ValueError(f"Table {table.__tablename__} already registered")

        table_i = table(self)
        self._tables[table.__tablename__] = table_i
        self.client.set_type_dependency(table, table_i)

    async def create_tables(self) -> None:
        """Создаёт таблицы для базы данных."""
        logger.info("Create tables")
        for name, model in self._tables.items():
            logger.debug("Create table for model {}", name)
            await model.create_table()
