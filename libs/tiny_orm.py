"""Крошечная ORM для упрощения жизни."""

from abc import ABC, abstractmethod
from collections.abc import Iterable
from typing import Any, Self, TypeVar

from asyncpg import Connection, Record


class TableItem(ABC):
    """Базовый класс для всех элементов базы данных."""

    @abstractmethod
    @classmethod
    def from_rom(cls, row: Record) -> Self:
        """Собирает класс из."""


_I = TypeVar("_I", bound=TableItem)


class TableQuery:
    """Вспомогательный сборщик SQL запросов."""

    def __init__(self, table_name: str) -> None:
        self._table_name = table_name
        self._query: str | None = None
        self._args: list[Any] = []

    @property
    def query(self) -> str:
        """Текст SQL запроса."""
        if self._query is None:
            raise ValueError("You teen to create query")
        return self._query

    @property
    def args(self) -> list[Any]:
        """Переданные в запрос параметры."""
        return self._args

    # Начало запросов
    # ===============

    def create_table(self, params: Iterable[str]) -> Self:
        """Создаёт таблицу с заданным именем и параметрами."""
        self._query = f"CREATE TABLE IF NOT EXISTS {self._table_name} ("
        self._query += ",".join(params)
        self._query += ")"
        return self

    def select(self, selectors: Iterable[str] | None = None) -> Self:
        """Select {selectors} FROM {table} operator."""
        selectors = selectors or ["*"]
        self._query = f"SELECT {', '.join(selectors)} FROM {self._table_name}"
        return self

    def insert(self, values: Iterable[Any]) -> Self:
        """INSERT INTO operator."""
        self._query = f"INSERT INTO {self._table_name} VALUES("

        items = iter(values)
        v = next(items)
        self._args.append(v)
        self._query += f"${len(self._args)}"

        for v in items:
            self._args.append(v)
            self._query += f", ${len(self._args)}"

        self._query += ")"

        return self

    def update(self) -> Self:
        """UPDATE operator."""
        self._query = f"UPDATE {self._table_name}"
        return self

    # операторы запросов
    # ==================

    def order_by(self, name: str, asc: bool = True) -> Self:
        """ORDER BY {name} ASC | DESC operator."""
        if self._query is None:
            raise ValueError("You need to use SELECT before ORDER")

        self._query += f" ORDER BY {name} {'ASC' if asc else 'DESC'}"
        return self

    def limit(self, count: int) -> Self:
        """LIMIT {count} operator."""
        if self._query is None:
            raise ValueError("You need to use SELECT before LIMIT")

        self._query += f" LIMIT {count}"
        return self

    def where(self, **kwargs: object) -> Self:
        """WHERE operator."""
        if self._query is None:
            raise ValueError("You need to use SELECT before WHERE")

        self._query += " WHERE"

        items = iter(kwargs.items())
        k, v = next(items)
        self._args.append(v)
        self._query += f"{k}=${len(self._args)}"

        for k, v in items:
            self._args.append(v)
            self._query += f", {k}=${len(self._args)}"

        return self

    def set(self, **kwargs: object) -> Self:
        """SET operator."""
        if self._query is None:
            raise ValueError("You need to use SELECT before SET")

        self._query += " SET"

        items = iter(kwargs.items())
        k, v = next(items)
        self._args.append(v)
        self._query += f"{k}=${len(self._args)}"

        for k, v in items:
            self._args.append(v)
            self._query += f", {k}=${len(self._args)}"

        return self

    # получение данных
    # ================

    async def execute(self, conn: Connection[Record]) -> str:
        """Выполняет запрос."""
        return await conn.execute(self.query, *self._args)

    async def fetch(self, conn: Connection[Record], to: type[_I]) -> list[_I]:
        """Получает результаты из базы данных."""
        cur = await conn.fetch(self.query, *self._args)
        return [to.from_rom(row) for row in cur]
