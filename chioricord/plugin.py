"""Надстройка над GatewayPlugin для упрощения работы с Chio API."""

from collections.abc import Sequence

import arc
from hikari import Permissions, Snowflake, UndefinedType
from hikari.applications import (
    ApplicationContextType,
    ApplicationIntegrationType,
)
from hikari.guilds import PartialGuild
from hikari.undefined import UNDEFINED

from chioricord.config import PluginConfig, PluginConfigManager
from chioricord.db import ChioDB, DBTable


class ChioPlugin(arc.GatewayPlugin):
    """Надстройка над GatewayPlugin с дополнительными методами."""

    def __init__(  # noqa: PLR0913
        self,
        name: str,
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

    def _client_include_hook(self, client: arc.GatewayClient) -> None:
        super()._client_include_hook(client)

        db = client.get_type_dependency(ChioDB)
        for table in self._tables:
            db.register(table)

        if self._config is not None:
            cm = client.get_type_dependency(PluginConfigManager)
            cm.register(self._config)
