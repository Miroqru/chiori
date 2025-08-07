"""Предоставляемый корневой функционал бота.

Доступен библиотекам и плагинам.
"""

from chioricord.api.config import BotConfig, PluginConfig
from chioricord.api.db import ChioDB, DBTable

# from chioricord.api.roles import ChangeRoleEvent, RoleLevel, RoleTable, UserRole

__all__ = (
    "BotConfig",
    "PluginConfig",
    "ChioDB",
    "DBTable",
    # "ChangeRoleEvent",
    # "RoleLevel",
    # "RoleTable",
    # "UserRole",
)
