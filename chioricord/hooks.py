"""Встроенные хуки.

Хуки используются чтобы повесить условия на использования команд.
"""

import arc

from chioricord.config import config


class NotOwnerError(arc.HookAbortError):
    """Если другой пользователь пытается получить доступ к командам."""


def owner_hook(ctx: arc.GatewayContext) -> None:
    """Проверка на администратора бота."""
    if config.BOT_OWNER != ctx.author.id:
        raise NotOwnerError("This command can use only bot owner,")
