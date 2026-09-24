"""База данных Postgres.

Позволяет расширения определять хранилище данных.
Хранилище используется для хранения изменяющейся информации.
Вместо того чтобы использоваться для этого файлы.

Предоставляет модель, таблицу и базу данных Chiori.
"""

from __future__ import annotations

import logging
import time
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Self

import asyncpg
import pypika

from chiori.api.registry import RegistryError

if TYPE_CHECKING:
    from chiori.client import ChioClient

logger = logging.getLogger(__name__)


# TODO: Перейти на использование pydantic
class DBModel:
    """Базовый класс модели.

    В этот класс после будут превращаться строки базы данных.
    """

    @classmethod
    def from_row(cls, row: asyncpg.Record) -> Self:
        """Собирает значение зи строки базы данных."""
        return cls(**dict(row.items()))


class ModelTable(ABC):
    """Базовый класс для всех таблиц базы данных."""

    __table_name__: str
    """Имя таблицы.

    Используется для идентификации таблиц в базе данных.
    Должно быть уникальным.
    """

    def __init__(self, db: ModelRegistry) -> None:
        self._db = db

    @property
    def table(self) -> pypika.Table:
        """Возвращает таблицу для создания запросов."""
        return pypika.Table(self.__table_name__)

    @property
    def table_name(self) -> str:
        """Возвращает уникальное имя таблицы."""
        return self.__table_name__

    @abstractmethod
    async def create_table(self) -> None:
        """Создаёт таблицу в базе данных, если ещё не была создана.

        Обязательный метод для определения.
        """

    @property
    def pool(self) -> asyncpg.Pool:
        """Возвращает пул подключений к базе данных.

        Его можно использовать только когда база данных активна.
        Позволяет выполнять запросы к базе данных.
        """
        return self._db.pool

    def __init_subclass__(cls, table: str | None = None) -> None:
        """Предоставляет имя таблицы для подкласса.

        В будущем может быть удалено.
        """
        super().__init_subclass__()
        if not table:
            raise RegistryError(f"You need to specify table name for {cls.__name__!r}")

        cls.__table_name__ = table


class ModelRegistry:
    """Регистр моделей.

    Она же база данных Шиори.
    Работает поверх Postgres пула подключений и взаимодействует со всеми таблицами
    базы данных и их моделями.
    """

    __slots__ = ("_client", "_models", "_pool", "app")

    def __init__(self, client: ChioClient) -> None:
        self._client = client
        self.app = client.app

        self._pool: asyncpg.Pool | None = None
        self._models: dict[str, ModelTable] = {}

    @property
    def client(self) -> ChioClient:
        """Клиент, к которому привязана база данных."""
        return self._client

    async def ping(self) -> float:
        """Просчитывает пинг до базы данных.

        Выполняет простой запрос к базе данных.
        Время рассчитывается при помощи `monotonic`.
        """
        start = time.monotonic()
        await self.pool.execute("SELECT 1")
        return (time.monotonic() - start) * 1000

    @property
    def pool(self) -> asyncpg.Pool:
        """Возвращает пул подключений к базе данных.

        Его можно использовать только когда база данных активна.
        Иначе вернёт исключение с ошибкой подключения.
        """
        if self._pool is None:
            raise ValueError("You need to connect to database pool before")
        return self._pool

    async def connect(self, dsn: str) -> None:
        """Подключается к базе данных.

        Принимает параметры для подключения к базе.
        """
        logger.info("Connect to Chio database")
        self._pool = await asyncpg.create_pool(dsn)

    async def close(self) -> None:
        """Закрывает соединение с базой данных, если активно."""
        logger.info("Close Chio database connection")
        if self._pool is None:
            logger.warning("No active connection to close")
            return
        await self._pool.close()

    def register(self, table: type[ModelTable]) -> None:
        """Регистрирует модель в базу данных.

        Действие выполняется до подключения к базе данных.
        Создаёт экземпляр модели и помещает его в хранилище.
        Также добавляет модель в DI клиента.
        """
        logger.debug("Register table %s", table.__table_name__)
        if table.__table_name__ in self._models:
            raise ValueError(f"Table {table.__table_name__} already registered")

        table_i = table(self)
        self._models[table.__table_name__] = table_i
        self._client.set_type_dependency(table, table_i)

    async def create_models(self) -> None:
        """Создаёт таблицы для базы данных на основе моделей.

        Должно выполнять после подключения к базе данных.
        """
        logger.info("Create tables from models")
        for name, model in self._models.items():
            logger.debug("Create table %s", name)
            await model.create_table()
