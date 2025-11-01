"""Определение каналов на сервере.

На сервере вы можете устанавливать специальные каналы, куда боте будет
отправлять свои сообщения.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Self

import arc
from asyncpg import Record

from chioricord.api import ChioDB, DBTable

if TYPE_CHECKING:
    from chioricord.client import ChioContext


@dataclass(frozen=True, slots=True)
class GuildChannel:
    """Описание канала из базы данных."""

    guild_id: int
    name: str
    channel_id: int

    @classmethod
    def from_row(cls, row: Record) -> Self:
        """Собирает значение из строки базы данных."""
        return cls(row[0], row[1], row[2])


class GuildChannels:
    """Специальный объект для работы с коллекцией каналов."""

    def __init__(self, table: ChannelsTable, guild_id: int) -> None:
        self.table = table
        self.guild_id = guild_id

    async def prefer(self, names: list[str]) -> GuildChannel:
        """Получает один из ID каналов по имени."""
        channels = await self.table.select(self.guild_id)
        for name in names:
            chan = channels.get(name)
            if chan is not None:
                return chan
        raise KeyError(f"Channels {names} not found")

    async def channels(self) -> dict[str, GuildChannel]:
        """Словарь всех каналов сервера."""
        return await self.table.select(self.guild_id)

    async def from_name(self, name: str) -> GuildChannel | None:
        """Возвращает канал по имени для сервера."""
        return await self.table.get(self.guild_id, name)

    async def set(self, name: str, channel_id: int) -> GuildChannel:
        """Устанавливает новый ID для канал по имени."""
        return await self.table.set(self.guild_id, name, channel_id)

    async def unset(self, name: str) -> None:
        """Сбрасывает ID для канала."""
        await self.table.unset(self.guild_id, name)

    async def reset(self) -> None:
        """Сбрасывает ID для канала."""
        await self.table.reset(self.guild_id)


class ChannelsTable(DBTable, table="channels"):
    """Таблица каналов сервера.

    Позволяет связать ID канала на сервере с именем в базе.
    """

    def __init__(self, db: ChioDB) -> None:
        super().__init__(db)
        self._db.client.add_injection_hook(self._chan_injector)

    async def _chan_injector(
        self, ctx: ChioContext, inj_ctx: arc.InjectorOverridingContext
    ) -> None:
        if ctx.guild_id is None:
            return

        inj_ctx.set_type_dependency(
            GuildChannels, GuildChannels(self, ctx.guild_id)
        )

    async def create_table(self) -> None:
        """Создаёт таблицы для базы данных."""
        await self.pool.execute(
            "CREATE TABLE IF NOT EXISTS channels ("
            "guild_id BIGINT NOT NULL,"
            "name VARCHAR(32) NOT NULL,"
            "channel_id BIGINT NOT NULL,"
            "PRIMARY KEY (guild_id, name))"
        )

    async def get(self, guild_id: int, name: str) -> GuildChannel | None:
        """Возвращает информацию о канале из базы данных по имени."""
        cur = await self.pool.fetchrow(
            "SELECT * FROM channels WHERE guild_id=$1 AND name=$2",
            guild_id,
            name,
        )
        return None if cur is None else GuildChannel.from_row(cur)

    async def set(
        self, guild_id: int, name: str, channel_id: int
    ) -> GuildChannel:
        """Устанавливает новое значение для канала."""
        await self.pool.execute(
            "INSERT INTO channels (guild_id, name, channel_id) "
            "VALUES ($1, $2, $3) "
            "ON CONFLICT (guild_id, name) DO UPDATE "
            "SET channel_id = $3;",
            guild_id,
            name,
            channel_id,
        )
        return GuildChannel(guild_id, name, channel_id)

    async def unset(self, guild_id: int, name: str) -> None:
        """Сбрасывает канал по имени."""
        await self.pool.execute(
            "DELETE FROM channels WHERE guild_id=$1 AND name=$2", guild_id, name
        )

    async def select(self, guild_id: int) -> dict[str, GuildChannel]:
        """Возвращает информацию о канале из базы данных по имени."""
        cur = await self.pool.fetch(
            "SELECT * FROM channels WHERE guild_id=$1", guild_id
        )
        return {row[1]: GuildChannel.from_row(row) for row in cur}

    async def reset(self, guild_id: int) -> None:
        """Сбрасывает все каналы на сервере."""
        await self.pool.execute(
            "DELETE FROM channels WHERE guild_id=$1", guild_id
        )
