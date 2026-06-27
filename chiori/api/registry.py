"""Регистры.

Определяет хранилище для расширений.
Так расширения смогут определять и использовать различные хранилища.
Как например настройки, таблицы, emoji и прочее.
"""

from __future__ import annotations

import re
import sys
from typing import TYPE_CHECKING

from loguru import logger
from pydantic import BaseModel, ConfigDict, ValidationError

if TYPE_CHECKING:
    from collections.abc import Mapping

    from chiori.client import ChioClient


_CTRL_RE = re.compile(r"[\x00-\x1f\x7f]")


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


def format_link(url: str, name: str) -> str:
    safe_url = _CTRL_RE.sub("", url)
    safe_name = _CTRL_RE.sub("", name)
    return f"\033]8;;{safe_url}\033\\{safe_name}\033]8;;\033\\"


def validation_error(e: ValidationError) -> None:
    f = sys.stderr

    f.write(f"\033[31mValidation error in: \033[91m{e.title}\033[31m {e.args}\033[0m:")
    for i in e.errors():
        f.write("\n\033[34m")
        f.write(".".join(str(x) for x in i["loc"]))
        f.write("\033[90m = \033[33m")
        f.write(str(i["input"]))
        f.write("\n\033[31m[\033[91m")
        if url := i.get("url"):
            f.write(format_link(url, i["type"]))
        else:
            f.write(i["type"])
        f.write("\033[31m]:\033[0m ")
        f.write(i["msg"])
    sys.stderr.write("\n")
