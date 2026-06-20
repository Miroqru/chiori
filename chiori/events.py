"""События бота."""

from dataclasses import dataclass
from typing import TYPE_CHECKING

import hikari

if TYPE_CHECKING:
    from chiori.client import ChioClient, ChioContext


@dataclass(frozen=True, slots=True)
class ChioEvent(hikari.Event):
    """Базовое событие клиента.

    Основа для всех событий.
    Предоставляет экземпляр клиента.
    """

    client: "ChioClient"

    @property
    def app(self) -> hikari.RESTAware:
        """App instance for this application."""
        return self.client.app


@dataclass(slots=True, frozen=True)
class UnexpectedError(hikari.Event):
    """Необработанная ошибка во время выполнения команды.

    Может быть поймана расширениями для отладки или оповещения.
    Исключает ошибки, которые могут быть обработаны на уровне ядра.
    """

    ctx: "ChioContext"
    exc: Exception

    @property
    def app(self) -> hikari.RESTAware:
        """App instance for this application."""
        return self.ctx.client.app

    @property
    def client(self) -> "ChioClient":
        """Экземпляр клиента, для которого получена ошибка."""
        return self.ctx.client
