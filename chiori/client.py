"""Клиент Chiori.

Надстройка поверх GatewayClient.
Предоставляет доступ к настройкам и хранилищам расширений.
"""

from collections.abc import Sequence

import arc
from hikari import Permissions, Snowflake, UndefinedType
from hikari.guilds import PartialGuild
from hikari.locales import Locale
from hikari.traits import GatewayBotAware
from hikari.undefined import UNDEFINED
from loguru import logger

from chiori.api import ChioDB, PluginConfigManager
from chiori.internal.config import ChioConfig


class ChioClient(arc.GatewayClient):
    """Надстройка над GatewayClient.

    Предоставляет доступ к настройкам и хранилищам расширений.
    """

    def __init__(  # noqa: PLR0913
        self,
        app: GatewayBotAware,
        config: ChioConfig,
        *,
        default_enabled_guilds: Sequence[Snowflake | int | PartialGuild]
        | UndefinedType = UNDEFINED,
        autosync: bool = True,
        autodefer: bool | arc.AutodeferMode = True,
        default_permissions: Permissions | UndefinedType = UNDEFINED,
        provided_locales: Sequence[Locale] | None = None,
    ) -> None:
        super().__init__(
            app,
            default_enabled_guilds=default_enabled_guilds,
            autosync=autosync,
            autodefer=autodefer,
            default_permissions=default_permissions,
            provided_locales=provided_locales,
        )

        self._bot_config = config
        self.set_type_dependency(ChioConfig, config)

        self._config = PluginConfigManager(self)
        self._db = ChioDB(self)

    @property
    def bot_config(self) -> ChioConfig:
        """Корневые настройки бота.

        Хранит в себе конфиденциальные данные и в будущем будет переработан.
        """
        logger.debug("Access to bot config")
        return self._bot_config

    @property
    def config(self) -> PluginConfigManager:
        """Хранилище настроек расширений."""
        return self._config

    @property
    def db(self) -> ChioDB:
        """Хранилище базы данных Chiori."""
        return self._db


ChioContext = arc.Context[ChioClient]
"""A context using the default Chio client implementation."""
