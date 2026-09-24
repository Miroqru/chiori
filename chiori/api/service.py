"""Сервисы шиори.

Сервис это специальный класс, связанный с клиентом.
Он предоставляет интерфейс высокого уровня для управления данными.
"""

import logging
from typing import TYPE_CHECKING

from chiori.api.registry import RegisterModel, Registry

if TYPE_CHECKING:
    from chiori.client import ChioClient

logger = logging.getLogger(__name__)


class Service(RegisterModel):
    """Базовый класс сервис.

    Сервис это специальный класс для взаимодействия с данными.
    Он предоставляет интерфейс высокого уровня для библиотек.
    Сервис привязывается к клиенту.
    """

    def __init__(self, client: "ChioClient") -> None:
        self._client = client

    @property
    def client(self) -> "ChioClient":
        """Возвращает привязанный к сервису клиент."""
        return self._client

    def on_load(self) -> None:
        """Действия при загрузке сервиса.

        Выполняет действие при запуске клиента, после подготовки.
        Может использоваться например для регистрации модели базы данных.
        """


class ServiceRegistry(Registry[Service]):
    """Регистр сервисов.

    Управляет всеми сервисами Шиори.
    """

    def _load_proto(self, name: str, proto: type[Service]) -> None:
        logger.debug("Load emoji set %s", name)
        model = proto(self._client)
        model.on_load()
        self._models[name] = model
        self._client.set_type_dependency(proto, model)

    def load(self) -> None:
        """Загружает модели из их прототипов."""
        logger.info("Load services")
        for name, proto in self._protos.items():
            self._load_proto(name, proto)

        self._protos = {}
