"""События бота."""

from dataclasses import dataclass
from typing import TYPE_CHECKING

import hikari

from chioricord.api import ChioDB

if TYPE_CHECKING:
    from chioricord.client import ChioClient


@dataclass(frozen=True, slots=True)
class DBEvent(hikari.Event):
    """Событие базы данных."""

    db: ChioDB

    @property
    def app(self) -> hikari.RESTAware:
        """App instance for this application."""
        return self.db.client.app

    @property
    def client(self) -> "ChioClient":
        """Client instance for this application."""
        return self.db.client
