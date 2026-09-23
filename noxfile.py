import typing as t
from pathlib import Path

import nox
from nox import options

PATH_TO_PROJECT = Path()
SCRIPT_PATHS = [PATH_TO_PROJECT, "noxfile.py"]

options.sessions = ["format_fix", "pyright"]


def uv_sync(
    session: nox.Session,
    /,
    *,
    include_self: bool = False,
    extras: t.Sequence[str] = (),
    groups: t.Sequence[str] = (),
) -> None:
    """Синхронизирует зависимости при помощи Uv."""
    if extras and not include_self:
        raise RuntimeError("When specifying extras, set `include_self=True`.")

    args: list[str] = []
    for extra in extras:
        args.extend(("--extra", extra))

    group_flag = "--group" if include_self else "--only-group"
    for group in groups:
        args.extend((group_flag, group))

    session.run_install(
        "uv",
        "sync",
        "--frozen",
        *args,
        silent=True,
        env={"UV_PROJECT_ENVIRONMENT": session.virtualenv.location},
    )


@nox.session()
def format_fix(session: nox.Session) -> None:
    """Форматирует код и автоматически исправляет ошибки линтера."""
    session.install("-U", "ruff")
    session.run("python", "-m", "ruff", "format", *SCRIPT_PATHS)
    session.run("python", "-m", "ruff", "check", *SCRIPT_PATHS, "--fix")


@nox.session()
def format(session: nox.Session) -> None:  # noqa: A001
    """Форматирует код под единый стандарт."""
    session.install("-U", "ruff")
    session.run("python", "-m", "ruff", "format", *SCRIPT_PATHS, "--check")
    session.run("python", "-m", "ruff", "check", *SCRIPT_PATHS)


@nox.session()
def pyright(session: nox.Session) -> None:
    """Проверяет код на ошибки типизации."""
    uv_sync(session, include_self=True, groups=["dev"])
    session.run("pyright", *SCRIPT_PATHS)
