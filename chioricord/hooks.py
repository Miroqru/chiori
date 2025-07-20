"""Встроенные хуки.

Хуки используются чтобы повесить условия на использования команд.
"""

from collections.abc import Callable

import arc

from chioricord.config import config
from chioricord.roles import RoleLevel, UserRole


class NotOwnerError(arc.HookAbortError):
    """Если другой пользователь пытается получить доступ к командам."""


class MissingRoleError(arc.HookAbortError):
    """Если пользователь пытается выполнить команду без необходимых прав."""


class UserBannedError(arc.HookAbortError):
    """Если пользователь с блокировкой пытается использовать команду."""


def owner_hook(ctx: arc.GatewayContext) -> None:
    """Проверка на администратора бота."""
    if config.BOT_OWNER != ctx.author.id:
        raise NotOwnerError("This command can use only bot owner,")


def _role_hook(ctx: arc.GatewayContext, role: RoleLevel) -> None:
    user = ctx.get_type_dependency(UserRole)
    if user.role == RoleLevel.BANNED:
        raise UserBannedError("You are banned by administrator")

    if user.role < role:
        raise MissingRoleError(
            role, f"You need role {role} to use this command"
        )


def has_role(role: RoleLevel) -> Callable[[arc.GatewayContext], None]:
    """Проверяет есть ли у пользователя необходимая роль."""

    def _wrapper(ctx: arc.GatewayContext) -> None:
        return _role_hook(ctx, role)

    return _wrapper
