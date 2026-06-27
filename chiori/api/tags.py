"""Система тегов для участников и серверов.

Каждому участнику или серверу можно будет выдавать теги.
Этими тегами смогут воспользоваться другие расширения.
"""

from collections.abc import Awaitable, Callable, Iterable
from dataclasses import dataclass
from datetime import datetime
from typing import Literal

import arc

from chiori.api import DBModel, DBTable
from chiori.client import ChioContext
from chiori.events import ChioEvent


@dataclass(frozen=True, slots=True)
class TagUpdateEvent(ChioEvent):
    """Изменение тега пользователя."""

    tag: "UserTag"


@dataclass(frozen=True, slots=True)
class TagRemoveEvent(ChioEvent):
    """Удаление тега пользователя."""

    tag: "UserTag"
    expired: bool = False


@dataclass(frozen=True, slots=True)
class UserTag(DBModel):
    """Тег пользователя."""

    user_id: int
    tag: str
    from_id: int | None
    created_at: datetime
    expired_at: datetime | None
    reason: str | None


class TagsTable(DBTable, table="user_tags"):
    """Таблица тегов для пользователей и серверов."""

    async def create_table(self) -> None:
        """Создаёт таблицы для базы данных."""
        await self.pool.execute(
            "CREATE TABLE IF NOT EXISTS user_tags ("
            "user_id BIGINT NOT NULL,"
            "tag VARCHAR(64) NOT NULL,"
            "from_id BIGINT,"
            "created_at TIMESTAMP NOT NULL DEFAULT NOW(),"
            "expired_at TIMESTAMP,"
            "reason VARCHAR(256),"
            "PRIMARY KEY (user_id, tag))"
        )

    async def get(self, user_id: int, tag: str) -> UserTag | None:
        """Получает тег пользователя."""
        cur = await self.pool.fetchrow(
            "SELECT * FROM user_tags WHERE user_id=$1 AND tag=$2",
            user_id,
            tag,
        )
        if cur is None:
            return None

        user_tag = UserTag.from_row(cur)
        now = datetime.now()
        if user_tag.expired_at is not None and now > user_tag.expired_at:
            await self.remove(user_tag, expired=True)
            return None

        return user_tag

    async def select(self, tag: str) -> list[UserTag]:
        """Получает всех пользователей, у которых есть нужный тег."""
        cur = await self.pool.fetch("SELECT * FROM user_tags WHERE tag=$1", tag)
        now = datetime.now()
        res: list[UserTag] = []
        remove: list[UserTag] = []

        for row in cur:
            user_tag = UserTag.from_row(row)
            if user_tag.expired_at is not None and now > user_tag.expired_at:
                remove.append(user_tag)
            else:
                res.append(user_tag)

        if len(remove) > 0:
            await self.remove_from(remove, expired=True)
        return res

    async def set(self, tag: UserTag) -> None:
        """Устанавливает/обновляет тег для пользователя."""
        await self.pool.execute(
            "INSERT INTO user_tags VALUES($1,$2,$3,$4,$5,$6) "
            "ON CONFLICT (user_id, tag) DO UPDATE SET "
            "from_id=$3, expired_at=$5, reason=$6",
            tag.user_id,
            tag.tag,
            tag.from_id,
            tag.created_at,
            tag.expired_at,
            tag.reason,
        )
        self._db.app.event_manager.dispatch(TagUpdateEvent(self._db.client, tag))

    async def remove(self, tag: UserTag, expired: bool = False) -> None:
        """Удаляет тег пользователя."""
        await self.pool.execute(
            "DELETE FROM user_tags WHERE user_id=$1 AND tag=$2",
            tag.user_id,
            tag.tag,
        )
        self._db.app.event_manager.dispatch(
            TagRemoveEvent(self._db.client, tag, expired)
        )

    async def remove_from(self, tags: list[UserTag], expired: bool = False) -> None:
        """Удаляет тег для нескольких пользователей."""
        placeholders = ",".join(f"${i + 1}" for i in range(len(tags)))
        sql = f"DELETE FROM user_tags WHERE user_id IN ({placeholders})"
        await self.pool.execute(
            sql,
            *(tag.user_id for tag in tags),
        )
        for tag in tags:
            self._db.app.event_manager.dispatch(
                TagRemoveEvent(self._db.client, tag, expired)
            )

    async def user_tags(self, user_id: int) -> list[str]:
        """Возвращает список тегов пользователя."""
        cur = await self.pool.fetch(
            "SELECT tag FROM user_tags WHERE user_id=$1", user_id
        )
        return [row[0] for row in cur]

    async def select_user(self, user_id: int) -> dict[str, UserTag]:
        """Получает все теги пользователя."""
        cur = await self.pool.fetch("SELECT * FROM user_tags WHERE user_id=$1", user_id)
        now = datetime.now()
        res: dict[str, UserTag] = {}
        remove: list[UserTag] = []

        for row in cur:
            tag = UserTag.from_row(row)
            if tag.expired_at is not None and now > tag.expired_at:
                remove.append(tag)
            else:
                res[tag.tag] = tag

        if len(remove) > 0:
            await self.remove_from(remove)

        return res

    async def clear_user(self, user_id: int) -> None:
        """Удаляет все теги пользователя."""
        await self.pool.execute("DELETE FROM user_tags WHERE user_id=$1", user_id)

    async def clear_tag(self, tag: str) -> None:
        """удаляет тег у всех пользователей."""
        await self.pool.execute("DELETE FROM user_tags WHERE tag=$1", tag)


@dataclass(slots=True, frozen=True)
class MissingTagsError(arc.HookAbortError):
    """Если пользователь пытается выполнить команду без необходимых прав."""

    missing: Iterable[str]
    mode: Literal["any", "all", "not"]


async def _has_tags(ctx: ChioContext, tags: Iterable[str]) -> None:
    if ctx.author.id == ctx.client.bot_config.BOT_OWNER:
        return

    table = ctx.client.get_type_dependency(TagsTable)
    user_tags = await table.user_tags(ctx.author.id)
    missing: list[str] = [tag for tag in tags if tag not in user_tags]

    if len(missing) > 0:
        raise MissingTagsError(missing, "all")


async def _not_tags(ctx: ChioContext, tags: Iterable[str]) -> None:
    if ctx.author.id == ctx.client.bot_config.BOT_OWNER:
        return

    table = ctx.client.get_type_dependency(TagsTable)
    user_tags = await table.user_tags(ctx.author.id)
    missing: list[str] = [tag for tag in tags if tag in user_tags]

    if len(missing) > 0:
        raise MissingTagsError(missing, "not")


async def _any_tags(ctx: ChioContext, tags: Iterable[str]) -> None:
    if ctx.author.id == ctx.client.bot_config.BOT_OWNER:
        return

    table = ctx.client.get_type_dependency(TagsTable)
    user_tags = await table.user_tags(ctx.author.id)
    for tag in tags:
        if tag in user_tags:
            return

    raise MissingTagsError(tags, "any")


def has_tags(*tags: str) -> Callable[[ChioContext], Awaitable[None]]:
    """Проверяет что у пользователя есть все необходимые теги."""

    async def _wrapper(ctx: ChioContext) -> None:
        return await _has_tags(ctx, tags)

    return _wrapper


def any_tags(*tags: str) -> Callable[[ChioContext], Awaitable[None]]:
    """Проверяет есть ли у пользователя хоть один нужный тег."""

    async def _wrapper(ctx: ChioContext) -> None:
        return await _any_tags(ctx, tags)

    return _wrapper


def not_tags(*tags: str) -> Callable[[ChioContext], Awaitable[None]]:
    """Проверяет что у пользователя нету указанных тегов."""

    async def _wrapper(ctx: ChioContext) -> None:
        return await _not_tags(ctx, tags)

    return _wrapper
