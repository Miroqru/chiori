"""Надстройка над GatewayPlugin для упрощения работы с Chio API."""

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Self

import arc
from hikari import Permissions, Snowflake, UndefinedType
from hikari.applications import ApplicationContextType, ApplicationIntegrationType
from hikari.guilds import PartialGuild
from hikari.undefined import UNDEFINED
from loguru import logger

from chiori.api import DBTable, PluginConfig
from chiori.client import ChioClient


@dataclass(slots=True, frozen=True)
class PluginMeta:
    """Метаданные плагина.

    Используется для предоставления дополинтельной информации о плагине.
    Помимо обязательного имени.
    """

    description: str | None = None
    """Краткое описание для плагина."""

    author: str = "Unknown"
    """Главный автор плагина."""

    maintainer: str | None = None
    """Сопровождающий проекта."""

    version: str = "0.0.1"
    """Версия плагина в формате SemVer."""

    build: int = 0
    """Номер сборки расширения."""

    tags: Sequence[str] | None = None
    """К каким группам принадлежит плагина."""


# TODO: Сделать метаданные обязаельными
class ChioPlugin(arc.GatewayPluginBase[ChioClient]):
    """Надстройка над GatewayPlugin с дополнительными методами."""

    def __init__(  # noqa: PLR0913
        self,
        name: str,
        meta: PluginMeta | None = None,
        *,
        default_enabled_guilds: Sequence[Snowflake | int | PartialGuild]
        | UndefinedType = UNDEFINED,
        autodefer: bool | arc.AutodeferMode | UndefinedType = UNDEFINED,
        integration_types: Sequence[ApplicationIntegrationType]
        | UndefinedType = UNDEFINED,
        invocation_contexts: Sequence[ApplicationContextType]
        | UndefinedType = UNDEFINED,
        default_permissions: Permissions | UndefinedType = UNDEFINED,
        is_nsfw: bool | UndefinedType = UNDEFINED,
    ) -> None:
        super().__init__(
            name,
            default_enabled_guilds=default_enabled_guilds,
            autodefer=autodefer,
            integration_types=integration_types,
            invocation_contexts=invocation_contexts,
            default_permissions=default_permissions,
            is_nsfw=is_nsfw,
        )

        self._meta = meta
        self._config: type[PluginConfig] | None = None
        self._tables: list[type[DBTable]] = []

    def set_config(self, config: type[PluginConfig]) -> None:
        """Устанавливает настройки для плагина.

        Настройки плагина можно использовать только после загрузки
        плагина и завершения запуска бота.
        """
        self._config = config

    def add_table(self, table: type[DBTable]) -> None:
        """Добавляет таблицу базы данных.

        Во время подключения плагина таблица регистрируется в базе данных.
        """
        self._tables.append(table)

    @property
    def meta(self) -> PluginMeta:
        """Дополнительные сведения о плагине.

        Если не указано, вернётся значение по умолчанию.
        """
        if self._meta is None:
            logger.warning("{} don`t have metadata", self._name)
            return PluginMeta()

        return self._meta

    def _client_include_hook(self, client: ChioClient) -> None:
        super()._client_include_hook(client)

        if self._meta is None:
            logger.warning("Plugin {} not provided meta. ", self.name)

        for table in self._tables:
            client.db.register(table)

        if self._config is not None:
            client.config.register(self._config)


class AdminPlugin(ChioPlugin):
    """Подкласс GatewayPlugin.

    Автоматически предоставляет `default_enabled_guilds`
    на основе настройки `ADMIN_GUILD`.
    """

    def _client_include_hook(self, client: ChioClient) -> None:
        super()._client_include_hook(client)
        self._default_enabled_guilds = [client.bot_config.ADMIN_GUILD]
