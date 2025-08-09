"""Магазин ролей для сервера."""

from dataclasses import dataclass
from typing import Self

from asyncpg import Record

from chioricord.api import DBTable


@dataclass(frozen=True, slots=True)
class GuildRole:
    """Продаваемая на сервере."""

    guild_id: int
    role: int
    price: int
    require_role: int | None

    @classmethod
    def from_row(cls, row: Record) -> Self:
        """Собирает GuildRole из базы данных."""
        return cls(row[1], row[2], row[3], row[4])


class RoleShopTable(DBTable, table="roles_shop"):
    """Таблица магазина ролей для гильдии."""

    async def create_table(self) -> None:
        """Создаёт таблицы для базы данных."""
        await self.pool.execute(
            "CREATE TABLE IF NOT EXISTS roles_shop ("
            "id SERIAL NOT NULL PRIMARY KEY,"
            "guild_id BIGINT NOT NULL,"
            "role_id BIGINT NOT NULL,"
            "price INTEGER NOT NULL,"
            "require_role BIGINT)"
        )

    async def get_shop(self, guild_id: int) -> list[GuildRole]:
        """Возвращает все роли для г."""
        cur = await self.pool.fetch(
            f"SELECT * FROM {self.__tablename__} WHERE guild_id=$1", guild_id
        )
        return [GuildRole.from_row(row) for row in cur]

    async def get_role(self, guild_id: int, role_id: int) -> GuildRole | None:
        """Retrieve guild by ID from the database."""
        cur = await self.pool.fetchrow(
            f"SELECT * FROM {self.__tablename__} "
            "WHERE guild_id=$1 AND role_id=$2",
            guild_id,
            role_id,
        )
        return None if cur is None else GuildRole.from_row(cur)

    async def add_role(self, role: GuildRole) -> None:
        """Create a new role record in the database."""
        await self.pool.execute(
            f"INSERT INTO {self.__tablename__}"
            "(guild_id,role_id,price,require_role) VALUES($1,$2,$3,$4)",
            role.guild_id,
            role.role,
            role.price,
            role.require_role,
        )

    async def remove_role(self, guild_id: int, role_id: int) -> None:
        """удаляет роль из магазина."""
        await self.pool.execute(
            f"DELETE FROM {self.__tablename__} "
            "WHERE guild_id=$1 AND role_id=$2",
            guild_id,
            role_id,
        )

    async def set_require(
        self, guild_id: int, role_id: int, required_role: int | None
    ) -> GuildRole:
        """Устанавливает требуемую роль перед покупкой."""
        role = await self.get_role(guild_id, role_id)
        if role is None:
            new_role = GuildRole(guild_id, role_id, 1000, required_role)
            await self.add_role(new_role)
        else:
            new_role = GuildRole(guild_id, role_id, role.price, required_role)
            await self.pool.execute(
                f"UPDATE {self.__tablename__} SET require_role=$1 "
                "WHERE guild_id=$2 AND role_id=$3",
                required_role,
                guild_id,
                role_id,
            )
        return new_role

    async def set_price(
        self, guild_id: int, role_id: int, price: int
    ) -> GuildRole:
        """Устанавливает требуемую роль перед покупкой."""
        role = await self.get_role(guild_id, role_id)
        if role is None:
            new_role = GuildRole(guild_id, role_id, price, None)
            await self.add_role(new_role)
        else:
            new_role = GuildRole(
                guild_id, role_id, role.price, role.require_role
            )
            await self.pool.execute(
                f"UPDATE {self.__tablename__} SET price=$1 "
                "WHERE guild_id=$2 AND role_id=$3",
                price,
                guild_id,
                role_id,
            )
        return new_role
