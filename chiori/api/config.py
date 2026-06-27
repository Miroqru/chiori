"""Хранилище настроек расширений.

Позволяет расширения определять настройки.
Настройки хранятся в TOML файлах и загружаются при запуске Шиори.
Настройки как статичное хранилище за пределами кода.
"""

from pathlib import Path
from typing import Unpack

import toml
from loguru import logger
from pydantic import ConfigDict

from chiori.api.registry import RegisterModel, Registry


class PluginConfig(RegisterModel):
    """Базовый класс для настроек расширения."""

    def __init_subclass__(cls, config: str, **kwargs: Unpack[ConfigDict]) -> None:
        """Позволяет указать имя настроек при определении модели."""
        super().__init_subclass__(**kwargs)
        if not config:
            raise ValueError("Model must have unique name")
        cls.__model_name__ = config


class ConfigRegistry(Registry[PluginConfig]):
    """Динамические настройки плагинов."""

    __slots__ = ("_client", "_models", "_protos")

    def _load_proto(
        self, config_path: Path, name: str, proto: type[PluginConfig]
    ) -> None:
        config_file = config_path / f"{name}.toml"
        if config_file.exists():
            logger.debug("Load config {}", name)
            with config_file.open() as f:
                model = proto.model_validate(toml.loads(f.read()))
        else:
            logger.warning("Config file {} not found", config_file)
            model = proto()

        self.set(proto, model, name)

    def load(self, config_path: Path) -> None:
        """Загружает настройки из прототипов."""
        fail_load: list[str] = []
        for name, proto in self._protos.items():
            try:
                self._load_proto(config_path, name, proto)
            except Exception as e:
                logger.warning(e)
                fail_load.append(name)

        if len(fail_load) > 0:
            logger.error("Failed to load some configs:")
            for name in fail_load:
                logger.error(
                    "- {name} => {config}/{name}.toml",
                    name=name,
                    config=config_path,
                )

            raise ValueError("Failed to load plugin config")
        self._protos = {}
