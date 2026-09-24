"""Шиори - Многофункциональный бот для нашего сервера.

В проекте преимущественно применяется модульная архитектура.
Потому весь дополнительный функционал реализуется в `libs` и `extensions`.
А само ядро служит чтобы предоставлять общий функционал между всеми
библиотеками и расширениями.

Version: v0.12.0 (85)
Author: Milinuri Nirvalen
"""

# Re use components from arc
from arc import loader, unloader

# Shortcuts for public Chio components
from chiori.client import ChioClient, ChioContext
from chiori.events import ChioEvent
from chiori.meta import __author__, __version__
from chiori.plugin import ChioPlugin, PluginMeta

__all__ = (
    "ChioClient",
    "ChioContext",
    "ChioEvent",
    "ChioPlugin",
    "PluginMeta",
    "__author__",
    "__version__",
    "loader",
    "unloader",
)
