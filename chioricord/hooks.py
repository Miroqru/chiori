"""Встроенные хуки.

Хуки используются чтобы повесить условия на использования команд.
"""

from collections.abc import Callable

import arc

from chioricord.api import RoleLevel, UserRole
from chioricord.client import ChioContext


class MissingRoleError(arc.HookAbortError):
    """Если пользователь пытается выполнить команду без необходимых прав."""


class UserBannedError(arc.HookAbortError):
    """Если пользователь с блокировкой пытается использовать команду."""


def _role_hook(ctx: ChioContext, role: RoleLevel) -> None:
    user = ctx.get_type_dependency(UserRole)
    if user.role == RoleLevel.BANNED:
        raise UserBannedError("You are banned by administrator")

    if user.role < role:
        raise MissingRoleError(
            role, f"You need role {role} to use this command"
        )


def has_role(role: RoleLevel) -> Callable[[ChioContext], None]:
    """Проверяет есть ли у пользователя необходимая роль."""

    def _wrapper(ctx: ChioContext) -> None:
        return _role_hook(ctx, role)

    return _wrapper
