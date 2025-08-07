"""Клиент Chiori."""

from collections.abc import Sequence

import arc
from alluka.abc import Client
from hikari import Permissions, Snowflake, UndefinedType
from hikari.guilds import PartialGuild
from hikari.locales import Locale
from hikari.traits import GatewayBotAware
from hikari.undefined import UNDEFINED

from chioricord.api import BotConfig, ChioDB, PluginConfigManager

__all__ = ("ChioClient", "ChioContext")


class ChioClient(arc.GatewayClient):
    """Надстройка над GatewayClient.

    Предоставляет доступ к базе данных и настройкам плагинов.
    """

    def __init__(  # noqa: PLR0913
        self,
        app: GatewayBotAware,
        config: BotConfig,
        *,
        default_enabled_guilds: Sequence[Snowflake | int | PartialGuild]
        | UndefinedType = UNDEFINED,
        autosync: bool = True,
        autodefer: bool | arc.AutodeferMode = True,
        default_permissions: Permissions | UndefinedType = UNDEFINED,
        provided_locales: Sequence[Locale] | None = None,
        injector: Client | None = None,
    ) -> None:
        super().__init__(
            app,
            default_enabled_guilds=default_enabled_guilds,
            autosync=autosync,
            autodefer=autodefer,
            default_permissions=default_permissions,
            provided_locales=provided_locales,
            injector=injector,
        )

        self._bot_config = config
        self._config = PluginConfigManager(self)
        self._db = ChioDB(self)

    @property
    def bot_config(self) -> BotConfig:
        """настройки бота."""
        return self._bot_config

    @property
    def config(self) -> PluginConfigManager:
        """Настройки плагинов."""
        return self._config

    @property
    def db(self) -> ChioDB:
        """База данных Chiori."""
        return self._db


ChioContext = arc.Context[ChioClient]
"""A context using the default chio client implementation."""
