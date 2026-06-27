"""Клиент Chiori.

Надстройка поверх GatewayClient.
Предоставляет доступ к настройкам и хранилищам расширений.
"""

from collections.abc import Sequence

import aiohttp
import arc
from hikari import Permissions, Snowflake, UndefinedType
from hikari.guilds import PartialGuild
from hikari.locales import Locale
from hikari.traits import GatewayBotAware
from hikari.undefined import UNDEFINED
from loguru import logger

from chiori.api import ChioDB, ConfigRegistry, EmojiRegistry, PluginConfig
from chiori.internal.config import ChioConfig


# TODO: Provide miru client for views
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

        self._config = ConfigRegistry(self)
        self._db = ChioDB(self)
        self._emoji = EmojiRegistry(self)

        self._session: aiohttp.ClientSession | None = None

    @property
    def bot_config(self) -> ChioConfig:
        """Корневые настройки бота.

        Хранит в себе конфиденциальные данные и в будущем будет переработан.
        """
        logger.debug("Access to bot config")
        return self._bot_config

    @property
    def config(self) -> ConfigRegistry:
        """Регистр настроек расширений."""
        return self._config

    @property
    def db(self) -> ChioDB:
        """Хранилище базы данных Chiori."""
        return self._db

    @property
    def emoji(self) -> EmojiRegistry:
        """Регистр собственных наборов emoji."""
        return self._emoji

    @property
    def session(self) -> aiohttp.ClientSession:
        """Возвращает связанную с ботов сессию."""
        if self._session is None:
            raise ValueError("You need to start client first")
        return self._session

    async def start(self) -> None:
        """Запускает работа клиента.

        Это финальные метод, запускается после предварительной подготовки.
        """
        logger.info("Start Chiori!")
        await self._db.connect(str(self._bot_config.DB_DSN))
        await self._db.create_tables()

    async def stop(self) -> None:
        """Остановка работа клиента.."""
        logger.info("Stop Chiori!")
        await self._db.close()

        if self._session:
            await self._session.close()

    def preload_config[C: PluginConfig](self, config: type[C]) -> C:
        """Подгружает настройки расширения.

        Такие настройки загружаются СРАЗУ во время запуска расширения, не
        ожидая окончания загрузки всех расширений.
        От чего требуют прямого указания до файла настроек.

        Это может быть полезно чтобы сразу во время запуск расширения применить
        настройки.
        В остальном не рекомендуется к использованию без необходимости.
        """
        return self.config.preload(config, self._bot_config.CONFIG_PATH)


ChioContext = arc.Context[ChioClient]
"""A context using the default Chio client implementation."""
