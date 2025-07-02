"""База данных активности участников."""

from dataclasses import dataclass
from pathlib import Path
from typing import Self

import aiosqlite


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
    def from_row(cls, row: aiosqlite.Row) -> Self:
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


class ActiveDatabase:
    """База данных активности пользователе.

    Сохраняет данные об активности участников.
    Поддерживает текстовую и голосовую активность.
    За определённую активность может выдаваться опыт.
    за накопленный опыт будут выдаваться уровни.
    Это будет стимулом для участников больше заниматься активностям.
    """

    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self._conn: aiosqlite.Connection | None = None

    @property
    def conn(self) -> aiosqlite.Connection:
        """Получает подключение к базе данных."""
        if self._conn is None:
            raise ValueError("You need to connect active database")
        return self._conn

    async def _create_tables(self) -> None:
        """Создаёт недостающие таблицы для базы данных."""
        await self.conn.execute(
            "CREATE TABLE IF NOT EXISTS 'active' ("
            "'user_id'	INTEGER NOT NULL,"
            "'messages'	INTEGER NOT NULL DEFAULT 0,"
            "'words'	INTEGER NOT NULL DEFAULT 0,"
            "'voice'	INTEGER NOT NULL DEFAULT 0,"
            "'bumps'	INTEGER NOT NULL DEFAULT 0,"
            "'level'	INTEGER NOT NULL DEFAULT 0,"
            "'xp'	INTEGER NOT NULL DEFAULT 0,"
            "PRIMARY KEY('user_id'));"
        )

    async def connect(self) -> None:
        """Подключается к базе данных."""
        self._conn = await aiosqlite.connect(self.db_path)
        await self._create_tables()

    async def close(self) -> None:
        """Закрывает соединение с базой данных."""
        if self._conn is None:
            return
        await self._conn.close()

    async def commit(self) -> None:
        """Записывает изменения в базу данных."""
        await self.conn.commit()

    # Таблица лидеров
    # ===============

    async def get_top(self, active: str) -> list[tuple[int, UserActive]]:
        """Таблица лидеров по сообщениям."""
        cur = await self.conn.execute(
            f"SELECT * FROM active ORDER BY {active} DESC LIMIT 10"
        )
        return [
            (row[0], UserActive.from_row(row)) for row in await cur.fetchall()
        ]

    async def get_user(self, user_id: int) -> UserActive | None:
        """Получает пользователя по ID."""
        cur = await self.conn.execute(
            "SELECT * FROM active WHERE user_id=?", (user_id,)
        )
        row = await cur.fetchone()
        if row is None:
            return None
        return UserActive.from_row(row)

    async def set_user(
        self, user_id: int, user: UserActive
    ) -> UserActive | None:
        """Получает пользователя по ID."""
        cur = await self.conn.execute(
            "SELECT * FROM active WHERE user_id=?", (user_id,)
        )
        row = await cur.fetchone()
        if row is None:
            await self.conn.execute(
                "INSERT INTO active VALUES(?, ?, ?, ?, ?, ?, ?)",
                (
                    user_id,
                    user.messages,
                    user.words,
                    user.voice,
                    user.bumps,
                    user.level,
                    user.xp,
                ),
            )
            return await self.get_user(user_id)
        else:
            await self.conn.execute(
                "UPDATE active "
                "SET messages=?, words=?, voice=?, bumps=?, level=?, xp=? "
                "WHERE user_id=?",
                (
                    user.messages,
                    user.words,
                    user.voice,
                    user.bumps,
                    user.level,
                    user.xp,
                    user_id,
                ),
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

    async def add_messages(self, user_id: int, amount: int) -> UserActive:
        """Обновляет счётчик сообщений.

        Прибавляет равноценное количество xp.
        """
        user = await self.get_or_default(user_id)
        user.messages += 1
        user.words += amount
        user.xp += amount
        next_level = user.count_xp()
        if user.xp >= next_level:
            user.level += 1
            user.xp -= next_level
        await self.set_user(user_id, user)
        return user

    async def add_voice(self, user_id: int, amount: int) -> UserActive | None:
        """Обновляет счётчик голосового канала.

        Также прибавляет 2*amount xp.
        """
        user = await self.get_or_default(user_id)
        user.voice += amount
        user.xp += amount * 2
        next_level = user.count_xp()
        if user.xp >= next_level:
            user.level += 1
            user.xp -= next_level
        await self.set_user(user_id, user)
        return user

    async def add_bump(self, user_id: int, amount: int) -> UserActive | None:
        """ТОбновляет список бампов сервера.

        Также прибавляет 5*amount xp.
        """
        user = await self.get_or_default(user_id)
        user.bumps += amount
        user.xp += amount * 5
        next_level = user.count_xp()
        if user.xp >= next_level:
            user.level += 1
            user.xp -= next_level
        await self.set_user(user_id, user)
        return user
