"""Регистры.

Определяет хранилище для расширений.
Так расширения смогут определять и использовать различные хранилища.
Как например настройки, таблицы, emoji и прочее.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from loguru import logger
from pydantic import BaseModel, ConfigDict

if TYPE_CHECKING:
    from collections.abc import Mapping

    from chiori.client import ChioClient


class RegisterModel(BaseModel):
    """Базовая модель для регистра.

    Используется чтобы определить хранимую информацию в регистре.
    У такой модели есть уникальное имя, по которому её можно отличить.
    По умолчанию данные в модели не изменяемые после определения и побочные
    атрибуты.
    """

    __model_name__: str | None = None
    """Уникальное имя модели.

    Оно будет использоваться для блокировки имён.
    Чтобы не допустить повторной регистрации модели.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    @classmethod
    def model_name(cls) -> str:
        """Возвращает имя модели."""
        # Может быть пустым, только если использовать базовый класс модели
        return cls.__model_name__  # pyright: ignore[reportReturnType]


class Registry[M: RegisterModel]:
    """Базовый регистр.

    Базовый функционал хранилища для расширений на основе моделей.
    """

    __slots__ = ("_client", "_models", "_protos")

    def __init__(self, client: ChioClient) -> None:
        self._client = client
        self._protos: dict[str, type[M]] = {}
        self._models: dict[str, M] = {}

    @property
    def models(self) -> Mapping[str, M]:
        """Возвращает полный словарь всех моделей."""
        return self._models

    def register(self, proto: type[M]) -> None:
        """Регистрирует нового прототипа.

        Он будет загружен при запуске метода `load`.
        Если прототип с таким именем уже существует - выдаст ошибку.
        """
        name = proto.model_name()
        logger.info("Register: {} -> {}", name, proto)
        if name in self._protos:
            raise ValueError(f"{name} (proto {proto}) already registered")
        self._protos[name] = proto

    def get(self, proto: type[M]) -> M:
        """Получает модель по её прототипу.

        Загрузка происходит по имени, а прототип нужен для типизации.
        """
        key = proto.model_name()
        model = self._models.get(key)
        if model is None:
            raise ValueError(f"Model with {key} is not registered")

        if not isinstance(model, proto):
            raise TypeError(f"Model is not instance of {proto}")

        return model

    def set(self, proto: type[M], model: M, name: str | None = None) -> None:
        """Напрямую устанавливает значение регистра."""
        name = name or model.model_name()
        logger.debug("Set {} -> {}", name, proto)
        self._models[name] = model
        self._client.set_type_dependency(proto, model)
