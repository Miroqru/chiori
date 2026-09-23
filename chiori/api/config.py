"""Хранилище настроек расширений.

Позволяет расширения определять настройки.
Настройки хранятся в TOML файлах и загружаются при запуске Шиори.
Настройки как статичное хранилище за пределами кода.
"""

import logging
import tomllib
from pathlib import Path
from typing import Unpack

from pydantic import ConfigDict, ValidationError

from chiori.api.registry import RegisterModel, Registry, validation_error

logger = logging.getLogger(__name__)


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

    def _load_proto[C: PluginConfig](
        self, config_path: Path, name: str, proto: type[C]
    ) -> C:
        config_file = config_path / f"{name}.toml"
        if config_file.exists():
            logger.debug("Load config from %s", config_file)
            with config_file.open() as f:
                model = proto.model_validate(tomllib.loads(f.read()))
        else:
            logger.warning("Config file %s not found", config_file)
            model = proto()

        self.set(proto, model, name)
        return model

    def load(self, config_path: Path) -> None:
        """Загружает настройки из прототипов."""
        fail_load: list[str] = []
        for name, proto in self._protos.items():
            try:
                self._load_proto(config_path, name, proto)
            except ValidationError as e:
                validation_error(e)
                fail_load.append(name)

            except FileNotFoundError as e:
                logger.warning(e)
                fail_load.append(name)

        if len(fail_load) > 0:
            logger.error("Failed to load some config models:")
            for name in fail_load:
                logger.error("- %s => %s.toml", name, config_path)

            raise ValueError("Failed to load plugin config")
        self._protos = {}

    def preload[C: PluginConfig](self, proto: type[C], config_path: Path) -> C:
        """Предварительная загрузка настроек.

        Выполняется СРАЗУ во время загрузки расширения.
        Что позволяет заранее подготовить некоторые системы.
        Использовать только при необходимости.
        """
        name = proto.model_name()
        logger.info("Register: %s -> %s", name, proto)
        try:
            model = self._load_proto(config_path, name, proto)
        except ValidationError as e:
            validation_error(e)
            raise

        except FileNotFoundError as e:
            logger.warning(e)
            raise

        return model
