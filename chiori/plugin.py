"""Шиори плагин.

Надстройка над GatewayPlugin для упрощения работы с Chiori API.
Предоставляет метаданные для плагина, с дополнительными сведениями.
"""

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal

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

    Используется для предоставления дополнительной информации.
    После она используется при индексации расширений.
    """

    description: str | None = None
    """Краткое описание в одном предложении для чего оно."""

    author: str = "Unknown"
    """Главный разработчик расширения."""

    maintainer: str | None = None
    """Сопровождающий, если расширение было портировано."""

    version: str = "0.0.1"
    """Версия расширения в формате SemVer."""

    build: int = 0
    """Номер сборки расширения. Увеличивается при каждом изменении."""

    tags: Sequence[str] | None = None
    """К каким группам принадлежит расширения."""


PluginScope = Literal["all", "main", "admin"]
"""Область действия расширения.

- all: Для всех серверов.
- main: Только для главного + разработчиков.
- admin: Только для сервера разработчиков.
"""


# TODO: Сделать метаданные обязательными
class ChioPlugin(arc.GatewayPluginBase[ChioClient]):
    """Надстройка над GatewayPlugin.

    Args:
        name: Имя расширениями. Должно быть уникальным. С большой буквы.
        meta: Дополнительные сведения о расширении.
        scope: Область действия расширения, на каких серверах.

    """

    def __init__(  # noqa: PLR0913
        self,
        name: str,
        meta: PluginMeta | None = None,
        *,
        scope: PluginScope | None = None,
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
        self._scope = scope
        self._config: type[PluginConfig] | None = None
        self._tables: list[type[DBTable]] = []

    @property
    def meta(self) -> PluginMeta:
        """Дополнительные сведения о плагине.

        Если не указано, вернётся значение по умолчанию.
        """
        if self._meta is None:
            logger.warning("{} don`t have metadata", self._name)
            return PluginMeta()

        return self._meta

    def _set_scope(self, client: ChioClient) -> None:
        if self._scope is None or self._scope == "all":
            return

        if self._scope == "main":
            self._default_enabled_guilds = [
                client.bot_config.MAIN_GUILD,
                client.bot_config.ADMIN_GUILD,
            ]

        if self._scope == "admin":
            self._default_enabled_guilds = [client.bot_config.ADMIN_GUILD]

    def _client_include_hook(self, client: ChioClient) -> None:
        super()._client_include_hook(client)

        if self._meta is None:
            logger.warning("Plugin {} not provided meta. ", self.name)

        self._set_scope(client)

        for table in self._tables:
            client.db.register(table)

        if self._config is not None:
            client.config.register(self._config)
