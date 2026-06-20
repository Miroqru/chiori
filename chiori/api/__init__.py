"""Предоставляемый корневой функционал бота.

Доступен библиотекам и плагинам.
"""

from chiori.api.config import PluginConfig, PluginConfigManager
from chiori.api.db import ChioDB, DBModel, DBTable

__all__ = (
    "ChioDB",
    "DBModel",
    "DBTable",
    "PluginConfig",
    "PluginConfigManager",
)
