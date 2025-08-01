"""Встроенные хуки.

Хуки используются чтобы повесить условия на использования команд.
"""

from collections.abc import Callable

import arc

from chioricord.roles import RoleLevel, UserRole


class MissingRoleError(arc.HookAbortError):
    """Если пользователь пытается выполнить команду без необходимых прав."""


class UserBannedError(arc.HookAbortError):
    """Если пользователь с блокировкой пытается использовать команду."""


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
