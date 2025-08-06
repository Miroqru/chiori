"""Хранилище коренных настроек.

Содержит в себе настройки, необходимые про запуске ядра.
Такие как токен discord бота и его владелец.

Для хранения настроек каждого плагина используется расширенное
хранилище.
"""

from pathlib import Path
from typing import TypeVar

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

    model_config = SettingsConfigDict(env_file=".env")


class PluginConfig(BaseModel):
    """Базовый класс для настроек плагина."""

    config_name: str | None = None
    """Имя настроек.

    Данное имя будет использоваться для пути к файлу настроек.
    если имя `foo`, тогда путь к настройкам `config/foo.toml`.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)


_C = TypeVar("_C", bound=PluginConfig)


class PluginConfigManager:
    """Динамические настройки плагинов."""

    def __init__(self, config_path: Path, client: GatewayClient) -> None:
        self._config_path = config_path
        self._client = client
        self._proto: list[type[PluginConfig]] = []
        self._config: dict[type[PluginConfig], PluginConfig] = {}

    def load(self) -> None:
        """Загружает настройки из прототипов."""
        name_lock: dict[str, type[PluginConfig]] = {}
        for proto in self._proto:
            if proto.config_name is None:
                raise ValueError(f"{proto} not provided config_name")

            used_name = name_lock.get(proto.config_name)
            if used_name is not None:
                raise ValueError(
                    f"{proto.config_name} already used by {used_name}"
                )

            with (self._config_path / f"{proto.config_name}.toml").open() as f:
                config = proto.model_validate(toml.load(f.read()))
                name_lock[proto.config_name] = proto

            self._config[proto] = config
            self._client.set_type_dependency(proto, config)
        self._proto = []

    def register(self, proto: type[PluginConfig]) -> None:
        """Регистрирует новые настройки для плагина."""
        logger.info("Setup config for {}", proto)
        if proto in self._proto:
            raise ValueError(f"{proto} already registered")
        self._proto.append(proto)

    def get(self, proto: type[_C]) -> _C:
        """Получает настройки для плагина."""
        key = self._config.get(proto)
        if key is None:
            raise ValueError(f"{proto} is not registered")
        return key  # type: ignore
