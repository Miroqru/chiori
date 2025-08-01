"""Хранилище коренных настроек.

Содержит в себе настройки, необходимые про запуске ядра.
Такие как токен discord бота и его владелец.

Для хранения настроек каждого плагина используется расширенное
хранилище.
"""

from collections.abc import Iterable
from pathlib import Path
from typing import Any, TypeVar, overload

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

    model_config = SettingsConfigDict(env_file=".env")


class PluginConfig(BaseModel):
    """Базовый класс для настроек плагина."""

    model_config = ConfigDict(extra="forbid", frozen=True)


_C = TypeVar("_C", bound=PluginConfig)


class PluginConfigManager:
    """Динамические настройки плагинов."""

    def __init__(self, config_path: Path, client: GatewayClient) -> None:
        self._config_path = config_path
        self._config: dict[str, dict[str, Any]] | None = None
        self._groups: dict[str, type[PluginConfig]] = {}
        self._client = client

    @property
    def config(self) -> dict[str, dict[str, Any]]:
        """Настройки приложения."""
        if self._config is None:
            self._config = self._load_file()
        return self._config

    @property
    def groups(self) -> Iterable[str]:
        """Возвращает список групп настроек."""
        return self._groups.keys()

    def dump_config(self) -> None:
        """Сохраняет настройки плагинов в файл."""
        logger.info("Dump config to file")
        self._write_file()

    # Работа с файлом конфига
    # =======================

    def _load_file(self) -> dict[str, dict[str, Any]]:
        logger.info(self._config_path.absolute())
        with self._config_path.open() as f:
            return toml.loads(f.read())

    def _write_file(self) -> None:
        if self._config is None:
            return
        with self._config_path.open("w") as f:
            f.write(toml.dumps(self._config))

    # Настройка подгрупп
    # ==================

    def register(self, key: str, proto: type[PluginConfig]) -> None:
        """Регистрирует новые настройки для плагина."""
        logger.info("Setup config for {}", key)
        self._groups[key] = proto
        config = self.get_group(key)
        self._client.set_type_dependency(proto, config)

    def get_proto(self, key: str) -> type[PluginConfig]:
        """получает прототип настроек для группы."""
        proto = self._groups.get(key)
        if proto is None:
            raise KeyError(f"Config {key} not registered")
        return proto

    @overload
    def get_group(self, key: str, type_: type[_C]) -> _C:
        pass

    @overload
    def get_group(self, key: str) -> PluginConfig:
        pass

    def get_group(
        self, key: str, type_: type[_C] | None = None
    ) -> _C | PluginConfig:
        """Получает настройки для плагина."""
        proto = self.get_proto(key)
        plugin_data = self.config.get(key)
        if plugin_data is None:
            return proto()
        return proto.model_validate(plugin_data)

    def save_group(self, key: str, data: PluginConfig) -> None:
        """Сохраняет настройки группы в конфиг."""
        if self._config is None:
            raise ValueError("You must load config before use it")
        self._config[key] = data.model_dump()
