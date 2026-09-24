"""Клиент Chiori.

Надстройка поверх GatewayClient.
Предоставляет доступ к настройкам и хранилищам расширений.
"""

import logging
from collections.abc import Callable, Mapping, Sequence
from typing import TYPE_CHECKING, Any

import aiohttp
import arc
import hikari
import miru
from hikari import Permissions, Snowflake, UndefinedType
from hikari.guilds import PartialGuild
from hikari.locales import Locale
from hikari.traits import GatewayBotAware
from hikari.undefined import UNDEFINED

from chiori.api import (
    ConfigRegistry,
    Custom,
    EmojiRegistry,
    ModelRegistry,
    PluginConfig,
)
from chiori.internal.config import ChioConfig, PathConfig

if TYPE_CHECKING:
    from chiori.plugin import ChioPlugin

logger = logging.getLogger(__name__)
_Formatter = Callable[[Any], hikari.Embed]
_Errors = dict[type[Exception], _Formatter]


class ChioClient(arc.GatewayClient):
    """Надстройка над GatewayClient.

    Предоставляет доступ к настройкам и хранилищам расширений.
    """

    # Расширения отдают только расширения Шиори
    plugins: Mapping[str, "ChioPlugin"]  # pyright: ignore[reportIncompatibleMethodOverride]

    __slots__ = (
        "_admin_guild",
        "_bot_config",
        "_config",
        "_db",
        "_emoji",
        "_errors",
        "_main_guild",
        "_miru",
        "_session",
    )

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
        self._owner_ids = [hikari.Snowflake(u_id) for u_id in config.BOT_OWNERS]
        self._main_guild = hikari.Snowflake(config.MAIN_GUILD)
        self._admin_guild = hikari.Snowflake(config.ADMIN_GUILD)

        self._miru = miru.Client.from_arc(self)

        self._config = ConfigRegistry(self)
        self._db = ModelRegistry(self)
        self._emoji = EmojiRegistry(self)

        self._session: aiohttp.ClientSession | None = None
        self._errors: _Errors = {}

    @property
    def path_config(self) -> PathConfig:
        """Настройки путей к файлам.

        Можно использовать чтобы получить используемые пути.
        Где лежат расширения, настройки и общие данные.
        Пришло на замену общим настройкам для повышения безопасности.
        """
        return self._bot_config.path

    @property
    def custom(self) -> Custom:
        """Настройки оформления.

        Позволяют более гибко настроить оформление Шиори.
        Указать имя. краткое описание, палитру цветов, активность и emoji.
        """
        return self._bot_config.custom

    @property
    def main_guild(self) -> hikari.Snowflake:
        """Главный сервер Шиори.

        Домашний сервер где происходит общение между участниками.
        Там же работают специальные расширения.
        """
        return self._main_guild

    @property
    def admin_guild(self) -> hikari.Snowflake:
        """Сервер для администраторов.

        Особый сервер где можно проводить настройку ядра.
        Здесь же работают особенные расширения.
        """
        return self._admin_guild

    @property
    def miru(self) -> miru.Client:
        """Возвращает активный miru клиента для управления View."""
        return self._miru

    @property
    def config(self) -> ConfigRegistry:
        """Регистр настроек расширений.

        Здесь расширения хранят свои настройки.
        Настройки становятся доступны только после запуска клиента.
        Для начала таблица должны быть зарегистрирована.
        """
        return self._config

    @property
    def db(self) -> ModelRegistry:
        """Хранилище базы данных Chiori.

        Здесь хранятся используемые таблицы для базы данных.
        Работа с базой данных становится доступна после запуска клиента.
        Для начала таблица должны быть зарегистрирована.
        """
        return self._db

    @property
    def emoji(self) -> EmojiRegistry:
        """Регистр собственных наборов emoji.

        Все emoji определяются в настройках custom.
        Расширения могут запрашивать собственный наборы emoji.
        """
        return self._emoji

    @property
    def session(self) -> aiohttp.ClientSession:
        """Возвращает связанную с ботов aiohttp сессию.

        Сессия становится доступна только после запуска клиента.
        И остаётся активной до его остановки.
        Используется в API обработчиках.
        """
        if self._session is None:
            raise ValueError("You need to start client first")
        return self._session

    async def start(self) -> None:
        """Запускает работа клиента.

        Запускается последним перед запуском обработки событий.
        Запускает сессию, подключается к базе данных и создаёт таблицы.
        """
        logger.info("Start Chiori!")
        self._session = aiohttp.ClientSession()
        await self._db.connect(str(self._bot_config.DB_DSN))
        await self._db.create_tables()

    async def stop(self) -> None:
        """Остановка работа клиента.

        Закрывает соединение с http сессией и базой данных.
        """
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
        return self.config.preload(config, self._bot_config.path.CONFIG_PATH)

    def register_error(self, exc: type[Exception], func: _Formatter) -> None:
        """Регистрирует ошибку для обработчика клиента.

        Позволяет обрабатывать ошибки на уровне клиента.
        Регистрируется пара: ошибка - функция отправки Embed сообщения.
        """
        logger.debug("Register handler for %s", exc.__name__)
        if exc in self._errors:
            raise ValueError(f"Erorr {exc} already registered")
        self._errors[exc] = func


ChioContext = arc.Context[ChioClient]
"""A context using the default Chio client implementation."""
