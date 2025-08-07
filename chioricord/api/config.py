"""Хранилище коренных настроек.

Содержит в себе настройки, необходимые про запуске ядра.
Такие как токен discord бота и его владелец.

Для хранения настроек каждого плагина используется расширенное
хранилище.
"""

from pathlib import Path
from typing import TypeVar, Unpack

import toml
from arc import GatewayClient
from loguru import logger
from pydantic import BaseModel, ConfigDict, PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class BotConfig(BaseSettings):
    """Общие настройки бота.

    Загружаются один раз во время запуска и после не изменяются.
    """

    BOT_TOKEN: str
    """Токен от дискорд бота.

    Обязателен для запуска бота, поскольку благодаря токену дискорд понимает
    что к нему хочет обратиться нужный бот.
    """

    BOT_OWNER: int
    """ Владелец бота.

    Используется для настройки ядра.
    На владельца не накладываются ограничения бота.
    Указывать владельца бота не обязательно, но желательно.
    """

    ADMIN_GUILD: int
    """Сервер администраторов.

    на этом сервере администраторы смогут пользоваться административными
    командами, которые не доступны на обычных серверах.
    """

    MAIN_GUILD: int
    """Главный сервер.

    Это главный сервер бота, где происходит основное общение с участниками.
    """

    # TODO: Начать использовать составной подход
    PLUGINS_CONFIG: Path = Path("plugins.toml")
    """Путь к настройкам плагинов.

    Здесь хранятся динамические настройки для плагинов, которые
    загружаются вместе с загрузкой бота.
    """

    DB_DSN: PostgresDsn | str
    """DSN для подключения к базе данных.

    Используется чтобы подключиться к главной базе данных Chiori.
    """

    DEBUG: bool = False
    """Режим отладки.

    В режиме отладки бот сообщает больше логов о происходящем.
    """

    EXTENSIONS_PATH: Path = Path("extensions/")
    """Путь до расширений.

    Откуда боту загружать необходимые расширения.
    """

    DATA_PATH: Path = Path("bot_data/")
    """Путь до хранилища данных плагинов.

    Плагины смогут записывать или читать данные зи данный директории.
    """

    CONFIG_PATH: Path = Path("config/")
    """Путь до настроек бота.

    Отсюда плагины загружают свои настройки.
    """

    model_config = SettingsConfigDict(
        env_file=".env", extra="forbid", frozen=True
    )


class PluginConfig(BaseModel):
    """Базовый класс для настроек плагина."""

    __config_name__: str | None = None
    """Имя настроек.

    Данное имя будет использоваться для пути к файлу настроек.
    если имя `foo`, тогда путь к настройкам `config/foo.toml`.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    def __init_subclass__(
        cls, config: str, **kwargs: Unpack[ConfigDict]
    ) -> None:
        """Позволяет передать имя настроек."""
        super().__init_subclass__(**kwargs)
        cls.__config_name__ = config


_C = TypeVar("_C", bound=PluginConfig)


class PluginConfigManager:
    """Динамические настройки плагинов."""

    __slots__ = ("_client", "_proto", "_config", "_name_lock", "_failed_load")

    def __init__(self, client: GatewayClient) -> None:
        self._client = client
        self._proto: list[type[PluginConfig]] = []
        self._config: dict[type[PluginConfig], PluginConfig] = {}

        self._name_lock: dict[str, type[PluginConfig]] = {}
        self._failed_load: list[str] = []

    def _load_proto(self, config_path: Path, proto: type[PluginConfig]) -> None:
        logger.debug("Load config {}", proto.__config_name__)
        if proto.__config_name__ is None:
            raise ValueError(f"{proto} not provided config_name")

        used_name = self._name_lock.get(proto.__config_name__)
        if used_name is not None:
            raise ValueError(
                f"{proto.__config_name__} already used by {used_name}"
            )

        config_file = config_path / f"{proto.__config_name__}.toml"
        if config_file.exists():
            with config_file.open() as f:
                config = proto.model_validate(toml.loads(f.read()))
                self._name_lock[proto.__config_name__] = proto
        else:
            logger.warning("{} not found", config_file)
            config = proto()

        self._config[proto] = config
        self._client.set_type_dependency(proto, config)

    def load(self, config_path: Path) -> None:
        """Загружает настройки из прототипов."""
        for proto in self._proto:
            try:
                self._load_proto(config_path, proto)
            except Exception as e:
                logger.warning(e)
                self._failed_load.append(proto.__config_name__)  # type: ignore

        if len(self._failed_load) > 0:
            logger.error("Failed to load some configs:")
            for name in self._failed_load:
                logger.error(
                    "- {name} => {config}/{name}.toml",
                    name=name,
                    config=config_path,
                )

            raise ValueError("Failed to load plugin config")

        # clear
        self._proto = []
        self._name_lock = {}
        self._failed_load = []

    def register(self, proto: type[PluginConfig]) -> None:
        """Регистрирует новые настройки для плагина."""
        logger.info("Register config {}", proto.__config_name__)
        if proto in self._proto:
            raise ValueError(f"{proto} already registered")
        self._proto.append(proto)

    def get(self, proto: type[_C]) -> _C:
        """Получает настройки для плагина."""
        key = self._config.get(proto)
        if key is None:
            raise ValueError(f"{proto} is not registered")
        return key  # type: ignore
