"""База данных активности участников.

Version: v2.0 (5)
Author: Milinuri Nirvalen
"""

from collections.abc import Awaitable
from dataclasses import dataclass
from typing import Self

from asyncpg import Record
from loguru import logger

from chioricord.db import ChioDatabase, DBTable


@dataclass(slots=True)
class UserActive:
    """Описание модели активности пользователя.

    - messages: Активность в сообщениях.
    - words: Активность по словам.
    - voice: Сколько минут проведено в голосовом канале.
    - level: Текущий уровень участника.
    - xp: Сколько опыта накоплено в текущем уровне.
    """

    messages: int
    words: int
    voice: int
    bumps: int
    level: int
    xp: int

    @classmethod
    def from_row(cls, row: Record) -> Self:
        """Собирает значение из строки базы данных."""
        return cls(
            messages=int(row[1]),
            words=int(row[2]),
            voice=int(row[3]),
            bumps=int(row[4]),
            level=int(row[5]),
            xp=int(row[6]),
        )

    def count_xp(self) -> int:
        """Сколько xp надо для достижения следующего уровня."""
        return (self.level**2 * 15) + (self.level * 5) + 10


Handler = Awaitable


class ActiveTable(DBTable):
    """База данных активности пользователе.

    Сохраняет данные об активности участников.
    Поддерживает текстовую и голосовую активность.
    За определённую активность может выдаваться опыт.
    за накопленный опыт будут выдаваться уровни.
    Это будет стимулом для участников больше заниматься активностям.
    """

    def __init__(self, db: ChioDatabase) -> None:
        super().__init__(db)
        self._level_up_handlers: list[Handler] = []

    def add_level_up_handler(self, func: Handler) -> None:
        """Добавляет обработчик на событие поднятия уровня."""
        self._level_up_handlers.append(func)

    async def dispatch_level_up(self, user_id: int, user: UserActive) -> None:
        """Вызывает событие поднятия уровня."""
        logger.info("Dispatch level up handlers {} {}", user_id, user)
        for handler in self._level_up_handlers:
            await handler(self._db, user_id, user)

    # Работа с базой данных
    # =====================

    async def create_table(self) -> None:
        """Создаёт недостающие таблицы для базы данных."""
        await self.conn.execute(
            "CREATE TABLE IF NOT EXISTS active ("
            "user_id	BIGINT NOT NULL,"
            "messages	INTEGER NOT NULL DEFAULT 0,"
            "words	INTEGER NOT NULL DEFAULT 0,"
            "voice	INTEGER NOT NULL DEFAULT 0,"
            "bumps	INTEGER NOT NULL DEFAULT 0,"
            "level	INTEGER NOT NULL DEFAULT 0,"
            "xp	INTEGER NOT NULL DEFAULT 0,"
            "PRIMARY KEY(user_id));"
        )

    async def get_top(self, active: str) -> list[tuple[int, UserActive]]:
        """Таблица лидеров по сообщениям."""
        cur = await self.conn.fetch(
            f"SELECT * FROM active ORDER BY {active} DESC LIMIT 10"
        )
        return [(row[0], UserActive.from_row(row)) for row in cur]

    async def get_user(self, user_id: int) -> UserActive | None:
        """Получает пользователя по ID."""
        cur = await self.conn.fetch(
            "SELECT * FROM active WHERE user_id=$1", user_id
        )
        if len(cur) == 0:
            return None
        return UserActive.from_row(cur[0])

    async def set_user(
        self, user_id: int, user: UserActive
    ) -> UserActive | None:
        """Получает пользователя по ID."""
        cur = await self.conn.fetch(
            "SELECT * FROM active WHERE user_id=$1", user_id
        )
        if len(cur) == 0:
            await self.conn.execute(
                "INSERT INTO active VALUES($1, $2, $3, $4, $5, $6, $7)",
                user_id,
                user.messages,
                user.words,
                user.voice,
                user.bumps,
                user.level,
                user.xp,
            )
            return await self.get_user(user_id)
        else:
            await self.conn.execute(
                "UPDATE active SET messages=$1, words=$2, voice=$3, "
                "bumps=$4, level=$5, xp=$6 WHERE user_id=$7",
                user.messages,
                user.words,
                user.voice,
                user.bumps,
                user.level,
                user.xp,
                user_id,
            )
            return user

    async def get_or_default(self, user_id: int) -> UserActive:
        """Получает пользователя или значение по умолчанию."""
        user = await self.get_user(user_id)
        if user is not None:
            return user
        return UserActive(0, 0, 0, 0, 0, 0)

    # Высокоуровневое обновление данных
    # =================================

    async def add_xp(
        self, user_id: int, user: UserActive, xp: int
    ) -> UserActive:
        """Добавляет опыт пользователю."""
        user.xp += xp

        start_level = user.level
        next_level = user.count_xp()
        while user.xp >= next_level:
            user.level += 1
            user.xp -= next_level
            next_level = user.count_xp()

        if user.level != start_level:
            await self.dispatch_level_up(user_id, user)
        return user

    async def add_messages(self, user_id: int, amount: int) -> UserActive:
        """Обновляет счётчик сообщений.

        Прибавляет равноценное количество xp.
        """
        user = await self.get_or_default(user_id)
        user.messages += 1
        user.words += amount
        user = await self.add_xp(user_id, user, amount)
        await self.set_user(user_id, user)
        return user

    async def add_voice(
        self, user_id: int, amount: int, xp: int
    ) -> UserActive | None:
        """Обновляет счётчик голосового канала.

        Также прибавляет 2*amount xp.
        """
        user = await self.get_or_default(user_id)
        user.voice += amount
        user = await self.add_xp(user_id, user, xp * 5)
        await self.set_user(user_id, user)
        return user

    async def add_bump(self, user_id: int, amount: int) -> UserActive | None:
        """ТОбновляет список бампов сервера.

        Также прибавляет 5*amount xp.
        """
        user = await self.get_or_default(user_id)
        user.bumps += amount
        user = await self.add_xp(user_id, user, amount * 5)
        await self.set_user(user_id, user)
        return user
