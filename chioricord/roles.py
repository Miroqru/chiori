"""Глобальная система ролей пользователей."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import IntEnum
from typing import TYPE_CHECKING, Self

import arc
from asyncpg import Record
from loguru import logger

from chioricord.api import ChioDB, DBTable
from chioricord.events import DBEvent

if TYPE_CHECKING:
    from chioricord.client import ChioContext


class RoleLevel(IntEnum):
    """Поле пользователей."""

    BANNED = 0
    USER = 1
    VIP = 2
    MODERATOR = 3
    ADMINISTRATOR = 4
    OWNER = 5


@dataclass(frozen=True, slots=True)
class UserRole:
    """Информация о заблокированном пользователе."""

    user_id: int
    from_id: int | None
    role: RoleLevel
    start_time: datetime | None
    reason: str | None

    @classmethod
    def from_row(cls, row: Record) -> Self:
        """Собирает значение базы данных из строки."""
        return cls(row[0], row[1], RoleLevel(row[2]), row[3], row[4])


@dataclass(frozen=True, slots=True)
class ChangeRoleEvent(DBEvent):
    """Когда изменяется роль пользователя.."""

    old_role: UserRole | None
    new_role: UserRole


class RoleTable(DBTable, table="roles"):
    """Таблица ролей пользователей."""

    def __init__(self, db: ChioDB) -> None:
        super().__init__(db)
        self._db.client.add_injection_hook(self.role_injector)

    async def role_injector(
        self, ctx: ChioContext, inj_ctx: arc.InjectorOverridingContext
    ) -> None:
        """Предоставляет роль пользователя в arc inject."""
        logger.debug("Try to get user from {}", ctx)
        if ctx.user.id == ctx.client.bot_config.BOT_OWNER:
            user = UserRole(
                ctx.user.id, None, RoleLevel.OWNER, None, "From core config"
            )
        else:
            user = await self.get_or_create(ctx.user.id)
        logger.debug(user)
        inj_ctx.set_type_dependency(UserRole, user)

    async def create_table(self) -> None:
        """Создаёт таблицы для базы данных."""
        await self.pool.execute(
            'CREATE TABLE IF NOT EXISTS "roles" ('
            '"user_id"	BIGINT UNIQUE PRIMARY KEY,'
            '"from_id"	BIGINT,'
            '"role"	INTEGER,'
            '"start_time"	TIMESTAMP NOT NULL DEFAULT NOW(),'
            '"reason"	TEXT)'
        )

    async def get_roles(self, role: RoleLevel) -> list[UserRole]:
        """Получает всех заблокированных пользователей."""
        cur = await self.pool.fetch(
            "SELECT * FROM roles WHERE role=$1", role.value
        )
        return [UserRole.from_row(row) for row in cur]

    async def get_user(self, user_id: int) -> UserRole | None:
        """Retrieve user by ID from the database."""
        cur = await self.pool.fetchrow(
            "SELECT * FROM roles WHERE user_id=$1", user_id
        )
        return None if cur is None else UserRole.from_row(cur)

    async def get_or_create(self, user_id: int) -> UserRole:
        """Retrieve user or return default instance."""
        user = await self.get_user(user_id)
        if user is not None:
            return user
        return UserRole(user_id, None, RoleLevel.USER, datetime.now(), None)

    async def _create_user(self, user: UserRole) -> None:
        """Create a new user record in the database."""
        await self.pool.execute(
            f"INSERT INTO {self.__tablename__} VALUES($1,$2,$3,$4,$5)",
            user.user_id,
            user.from_id,
            user.role.value,
            user.start_time,
            user.reason,
        )

    async def _set_user(self, user: UserRole) -> None:
        """Update user record in the database."""
        await self.pool.execute(
            f"UPDATE {self.__tablename__} SET from_id=$1, start_time=$2, "
            "role=$3, reason=$4 WHERE user_id=$5",
            user.from_id,
            user.start_time,
            user.role,
            user.reason,
            user.user_id,
        )

    # Высокоуровневые функции работы с ролями
    # =======================================

    async def remove_role(self, user_id: int) -> None:
        """Remove record from database by ID."""
        await self.pool.execute(
            f"DELETE FROM {self.__tablename__} WHERE user_id=$1", user_id
        )

    async def set_role(
        self,
        user_id: int,
        from_id: int,
        role: RoleLevel,
        reason: str | None = None,
    ) -> UserRole:
        """Remove record from database by ID."""
        now = datetime.now()
        db_user = await self.get_user(user_id)
        user = UserRole(user_id, from_id, role, now, reason)
        if db_user is None:
            await self._create_user(user)
        else:
            await self._set_user(user)

        self._db.app.event_manager.dispatch(
            ChangeRoleEvent(self._db, db_user, user)
        )
        return user

    # Role aliases
    # ============

    async def set_banned(
        self, user_id: int, from_id: int, reason: str | None = None
    ) -> UserRole:
        """Устанавливает роль BANNED пользователю."""
        return await self.set_role(user_id, from_id, RoleLevel.BANNED, reason)

    async def set_user(
        self, user_id: int, from_id: int, reason: str | None = None
    ) -> UserRole:
        """Устанавливает роль USER пользователю."""
        return await self.set_role(user_id, from_id, RoleLevel.USER, reason)

    async def set_vip(
        self, user_id: int, from_id: int, reason: str | None = None
    ) -> UserRole:
        """Устанавливает роль VIP пользователю."""
        return await self.set_role(user_id, from_id, RoleLevel.VIP, reason)

    async def set_moderator(
        self, user_id: int, from_id: int, reason: str | None = None
    ) -> UserRole:
        """Устанавливает роль MODERATOR пользователю."""
        return await self.set_role(
            user_id, from_id, RoleLevel.MODERATOR, reason
        )

    async def set_administrator(
        self, user_id: int, from_id: int, reason: str | None = None
    ) -> UserRole:
        """Устанавливает роль ADMINISTRATOR пользователю."""
        return await self.set_role(
            user_id, from_id, RoleLevel.ADMINISTRATOR, reason
        )
