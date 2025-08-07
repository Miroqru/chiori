"""таблица с чатами для общения ии.

До тех пор, пока не появится нормальная поддержка хранилища сервера.

Version: v1.0 (8)
Author: Milinuri Nirvalen
"""

from collections import Counter
from collections.abc import AsyncIterator
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Literal, Self

import arc
import hikari
from asyncpg import Record
from loguru import logger

from chioricord.api import ChioDB, DBTable
from chioricord.client import ChioClient, ChioContext

RoleT = Literal["user", "system", "assistant", "imagine"]


@dataclass(frozen=True, slots=True)
class ChatGuild:
    """Настройки для серверов.

    Пользователь может выбрать чат, в котором будет общаться ИИ.
    """

    guild_id: int
    chat_channel: int | None

    @classmethod
    def from_row(cls, row: Record) -> Self:
        """Собирает контекст чата из базы данных."""
        return cls(row[0], row[1])


@dataclass(frozen=True, slots=True)
class UserContext:
    """Контекст пользователя для переписки с ИИ."""

    user_id: int
    reg_date: datetime
    model: str | None

    @classmethod
    def from_row(cls, row: Record) -> Self:
        """Собирает контекст пользователя из базы данных."""
        return cls(row[0], row[1], row[2])


@dataclass(frozen=True, slots=True)
class UserMessage:
    """Сообщение пользователя из истории."""

    user_id: int
    guild_id: int | None
    channel_id: int | None
    message: str
    role: RoleT
    attachment_url: str | None
    created_at: datetime

    @classmethod
    def from_row(cls, row: Record) -> Self:
        """Собирает сообщение пользователя из базы данных."""
        return cls(row[1], row[2], row[3], row[4], row[5], row[6], row[7])


@dataclass(frozen=True, slots=True)
class MessageStats:
    """Статистика истории сообщений.

    Содержит счётчик количества сообщений, ролей, серверов.
    """

    users: Counter[int]
    roles: Counter[RoleT]
    guilds: Counter[int]


# События
# =======


class CreateUserEvent(hikari.Event):
    """Когда пользователь создаёт учётную запись."""

    def __init__(self, db: ChioDB, user: UserContext) -> None:
        self._db = db
        self._user = user

    @property
    def app(self) -> hikari.RESTAware:
        """App instance for this application."""
        return self._db.client.app

    @property
    def client(self) -> ChioClient:
        """App instance for this application."""
        return self._db.client

    @property
    def db(self) -> ChioDB:
        """Возвращает подключение к базе данных."""
        return self._db

    @property
    def user_id(self) -> int:
        """Возвращает пользователя, получившего повышение."""
        return self._user.user_id

    @property
    def user(self) -> UserContext:
        """Возвращает статистику активности пользователя."""
        return self._user


# Таблицы для базы данных
# =======================


class ChatTable(DBTable):
    """Таблица чатов с ии для гильдии."""

    __tablename__ = "chat"

    def __init__(self, db: ChioDB) -> None:
        super().__init__(db)
        self._db.client.add_injection_hook(self.chat_injector)

    async def chat_injector(
        self, ctx: ChioContext, inj_ctx: arc.InjectorOverridingContext
    ) -> None:
        """Предоставляет роль пользователя в arc inject."""
        logger.debug("Try to get user with id {}", ctx.user.id)
        chat = await self.get_or_create(ctx.user.id)
        inj_ctx.set_type_dependency(ChatGuild, chat)

    async def create_table(self) -> None:
        """Создаёт таблицы для базы данных."""
        await self.pool.execute(
            "CREATE TABLE IF NOT EXISTS chat ("
            "guild_id BIGINT PRIMARY KEY NOT NULL,"
            "chat_channel BIGINT)"
        )

    async def _create_chat(self, chat: ChatGuild) -> None:
        """Create a new user record in the database."""
        await self.pool.execute(
            f"INSERT INTO {self.__tablename__} VALUES($1,$2)",
            chat.guild_id,
            chat.chat_channel,
        )

    async def _set_chat(self, chat: ChatGuild) -> None:
        """Update user record in the database."""
        await self.pool.execute(
            f"UPDATE {self.__tablename__} SET chat_channel=$1 "
            "WHERE guild_id=$2",
            chat.chat_channel,
            chat.guild_id,
        )

    async def get_chats(self) -> list[ChatGuild]:
        """Retrieve items by parameter from the database."""
        cur = await self.pool.fetch(f"SELECT * FROM {self.__tablename__}")
        return [ChatGuild.from_row(row) for row in cur]

    async def get_chat(self, guild_id: int) -> ChatGuild | None:
        """Retrieve user by ID from the database."""
        cur = await self.pool.fetchrow(
            f"SELECT * FROM {self.__tablename__} WHERE guild_id=$1", guild_id
        )
        return None if cur is None else ChatGuild.from_row(cur)

    async def get_or_create(self, guild_id: int) -> ChatGuild:
        """Retrieve user or return default instance."""
        chat = await self.get_chat(guild_id)
        if chat is not None:
            return chat
        return ChatGuild(guild_id, None)

    async def set_chat(
        self, guild_id: int, chat_channel: int | None = None
    ) -> ChatGuild:
        """Устанавливает чат для общения."""
        chat = await self.get_chat(guild_id)
        new_chat = ChatGuild(guild_id, chat_channel)
        if chat is None:
            await self._create_chat(new_chat)
        else:
            await self._set_chat(new_chat)
        return new_chat


class UsersTable(DBTable):
    """Таблица пользователей ии."""

    __tablename__ = "lingua_users"

    async def create_table(self) -> None:
        """Создаёт таблицы для базы данных."""
        await self.pool.execute(
            "CREATE TABLE IF NOT EXISTS lingua_users ("
            "user_id BIGINT PRIMARY KEY NOT NULL,"
            "reg_date TIMESTAMP NOT NULL DEFAULT NOW(),"
            "model TEXT)"
        )

    async def _create_user(self, user: UserContext) -> None:
        """Create a new user record in the database."""
        await self.pool.execute(
            f"INSERT INTO {self.__tablename__} VALUES($1,$2,$3)",
            user.user_id,
            user.reg_date,
            user.model,
        )
        self._db.client.app.event_manager.dispatch(
            CreateUserEvent(self._db, user)
        )

    async def _set_user(self, user: UserContext) -> None:
        """Update user record in the database."""
        await self.pool.execute(
            f"UPDATE {self.__tablename__} SET model=$1 WHERE user_id=$2",
            user.model,
            user.user_id,
        )

    async def get_user(self, user_id: int) -> UserContext | None:
        """Retrieve user by ID from the database."""
        cur = await self.pool.fetchrow(
            f"SELECT * FROM {self.__tablename__} WHERE user_id=$1", user_id
        )
        return None if cur is None else UserContext.from_row(cur)

    async def get_or_create(self, user_id: int) -> UserContext:
        """Retrieve user or return default instance."""
        user = await self.get_user(user_id)
        if user is not None:
            return user
        return UserContext(user_id, datetime.now(), None)

    async def set_model(
        self, user_id: int, model: str | None = None
    ) -> UserContext:
        """Устанавливает новую AI модель."""
        user = await self.get_user(user_id)
        new_user = UserContext(user_id, datetime.now(), model)
        if user is None:
            await self._create_user(new_user)
        else:
            await self._set_user(new_user)
        return new_user


class MessagesTable(DBTable):
    """Таблица сообщений в ии чатах."""

    __tablename__ = "lingua_messages"

    async def create_table(self) -> None:
        """Создаёт таблицы для базы данных."""
        await self.pool.execute(
            "CREATE TABLE IF NOT EXISTS lingua_messages ("
            "id SERIAL NOT NULL PRIMARY KEY,"
            "user_id BIGINT NOT NULL,"
            "guild_id BIGINT,"
            "channel_id BIGINT,"
            "message TEXT NOT NULL,"
            "role TEXT NOT NULL,"
            "attachment_url TEXT,"
            "created_at TIMESTAMP NOT NULL DEFAULT NOW())"
        )

    async def get_history(self, user_id: int) -> list[UserMessage]:
        """Retrieve user by ID from the database."""
        cur = await self.pool.fetch(
            f"SELECT * FROM {self.__tablename__} WHERE user_id=$1", user_id
        )
        return [UserMessage.from_row(row) for row in cur]

    async def _iter_messages(self) -> AsyncIterator[UserMessage]:
        cur = await self.pool.fetch(f"SELECT * FROM {self.__tablename__}")
        for row in cur:
            yield UserMessage.from_row(row)

    async def last_week_messages(self) -> AsyncIterator[UserMessage]:
        """Возвращает сообщения пользователей за последнюю неделю."""
        now = datetime.now() - timedelta(days=7)
        cur = await self.pool.fetch(
            f"SELECT * FROM {self.__tablename__} "
            "WHERE role='user' and created_at > $1",
            now,
        )
        for row in cur:
            yield UserMessage.from_row(row)

    async def get_stats(self) -> MessageStats:
        """Статистика сообщений."""
        user_counter: Counter[int] = Counter()
        guild_counter: Counter[int] = Counter()
        role_counter: Counter[RoleT] = Counter()

        async for message in self._iter_messages():
            role_counter[message.role] += 1

            if message.role != "user":
                continue

            user_counter[message.user_id] += 1
            if message.guild_id is not None:
                guild_counter[message.guild_id] += 1

        return MessageStats(user_counter, role_counter, guild_counter)

    async def _create_message(self, message: UserMessage) -> None:
        """Create a new user record in the database."""
        await self.pool.execute(
            f"INSERT INTO {self.__tablename__}"
            "(user_id,guild_id,channel_id,message,role,attachment_url) "
            "VALUES($1,$2,$3,$4,$5,$6)",
            message.user_id,
            message.guild_id,
            message.channel_id,
            message.message,
            message.role,
            message.attachment_url,
        )

    async def add_message(
        self,
        user_id: int,
        guild_id: int | None,
        channel_id: int | None,
        message: str,
        role: RoleT = "user",
        attachment_url: str | None = None,
    ) -> None:
        """Добавляет новое сообщение в историю."""
        user_message = UserMessage(
            user_id,
            guild_id,
            channel_id,
            message,
            role,
            attachment_url,
            datetime.now(),
        )
        await self._create_message(user_message)

    async def get_last_messages(
        self,
        user_id: int,
        guild_id: int | None,
        channel_id: int | None,
    ) -> list[UserMessage]:
        """получает последние несколько сообщений для формирования контекста."""
        if guild_id is not None and channel_id is not None:
            cur = await self.pool.fetch(
                f"SELECT * FROM {self.__tablename__} WHERE user_id=$1 "
                "ORDER BY create_at DESC LIMIT 10",
                user_id,
            )
        else:
            cur = await self.pool.fetch(
                f"SELECT * FROM {self.__tablename__} "
                "WHERE user_id=$1, guild_id=$2, channel_id=$5 "
                "ORDER BY create_at DESC LIMIT 10",
                user_id,
                guild_id,
                channel_id,
            )

        return [UserMessage.from_row(row) for row in cur]
