"""События Шиори.

Предоставляет базовые события, которые после будут использоваться.
"""

from dataclasses import dataclass
from typing import TYPE_CHECKING

import hikari

if TYPE_CHECKING:
    from chiori.client import ChioClient


# TODO: Перейти на использование attr для канона.
@dataclass(frozen=True, slots=True)
class ChioEvent(hikari.Event):
    """Базовое событие клиента.

    Основа для всех событий.
    Предоставляет экземпляр клиента в события.
    """

    client: "ChioClient"
    """Клиент, для которого вызвано событие."""

    @property
    def app(self) -> hikari.RESTAware:
        """App instance for this application."""
        return self.client.app
