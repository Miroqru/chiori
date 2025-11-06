"""Управляет расширениями Chiori.

Управляет загруженными в клиент плагинами во время работы бота.
Позволяет загружать/выгружать/перезагружать плагины.
просматривать их общий список.
Выполнять синхронизацию команд.

Version: v1.1.2 (11)
Author: Milinuri Nirvalen
"""

from pathlib import Path

import arc
import hikari

from chioricord.client import ChioClient, ChioContext
from chioricord.hooks import has_role
from chioricord.plugin import ChioPlugin
from chioricord.roles import RoleLevel

plugin = ChioPlugin("Extension manager")
cmd_group = plugin.include_slash_group(
    name="ext", description="Управление загруженными расширениями."
)


def get_extensions() -> list[str]:
    """Получает список всех расширений."""
    ext_list: list[str] = []
    for file in Path("extensions/").iterdir():
        if file.is_dir():
            continue
        ext_list.append(file.name.split(".")[0])
    return ext_list


async def ext_opts(
    data: arc.AutocompleteData[ChioClient, str],
) -> list[str]:
    """Авто дополнение для списка расширений."""
    extensions = get_extensions()
    if data.focused_value is None:
        return extensions[:25]

    res: list[str] = []
    for ext in extensions:
        if ext.startswith(data.focused_value):
            res.append(ext)
    return res[:25]


# Определение команд
# ==================


@cmd_group.include
@arc.slash_subcommand("list", description="Список всех доступных расширений.")
async def list_extension(ctx: ChioContext) -> None:
    """Список всех доступных расширений.

    Просматривает список файлов в папке `extensions/`.
    """
    ext_list: list[str] = []
    for file in Path("extensions/").iterdir():
        if file.is_dir():
            continue
        ext_list.append(file.name.split(".")[0])

    ext_desc = ""
    for i, ext in enumerate(sorted(ext_list)):
        ext_desc += f"`{ext}`"
        if i <= len(ext_list):
            ext_desc += ", "

    emb = hikari.Embed(
        title=f"📦 Доступные расширения ({len(ext_list)})",
        description=ext_desc,
        color=0xCC66FF,
    )
    await ctx.respond(emb)


@cmd_group.include
@arc.slash_subcommand("load", description="Загрузить расширение по имени.")
async def load_extension(
    ctx: ChioContext,
    extension: arc.Option[  # type: ignore
        str, arc.StrParams("Путь до расширения", autocomplete_with=ext_opts)
    ],
) -> None:
    """Загружает расширение по пути модуля.

    Загрузка происходит начиная с пути extensions/.
    """
    ext_module = f"extensions.{extension}"
    ctx.client.load_extension(ext_module)
    await ctx.respond(
        f"🧩 Расширение `{ext_module}` загружено.\n"
        "⏳ Пожалуйста синхронизируйте список команд если это необходимо."
    )


@cmd_group.include
@arc.slash_subcommand("unload", description="Выгрузить расширение по имени.")
async def unload_extension(
    ctx: ChioContext,
    extension: arc.Option[  # type: ignore
        str, arc.StrParams("Путь до расширения", autocomplete_with=ext_opts)
    ],
) -> None:
    """Загружает расширение по пути модуля.

    Загрузка происходит начиная с пути extensions/.
    """
    ext_module = f"extensions.{extension}"
    ctx.client.unload_extension(ext_module)
    await ctx.respond(
        f"🧩 Расширение `{ext_module}` выгружено.\n"
        "⏳ Пожалуйста синхронизируйте список команд если это необходимо."
    )


@cmd_group.include
@arc.slash_subcommand("reload", description="Перезагрузить расширение по имени.")
async def reload_extension(
    ctx: ChioContext,
    extension: arc.Option[  # type: ignore
        str, arc.StrParams("Путь до расширения", autocomplete_with=ext_opts)
    ],
) -> None:
    """Загружает расширение по пути модуля.

    Загрузка происходит начиная с пути extensions/.
    """
    ext_module = f"extensions.{extension}"
    ctx.client.unload_extension(ext_module)
    ctx.client.load_extension(ext_module)
    await ctx.respond(
        f"🧩 Расширение `{ext_module}` перезагружено.\n"
        "⏳ Пожалуйста синхронизируйте список команд если это необходимо."
    )


@cmd_group.include
@arc.slash_subcommand("sync", description="Синхронизировать список команд.")
async def sync_commands(ctx: ChioContext) -> None:
    """Обновляет список команд на стороне Discord.

    это дорогая операция, чтобы выполнять её при каждом действии с расширением.
    """
    res = await ctx.respond("⏳ Синхронизация команд ...")
    await ctx.client.resync_commands()
    await res.edit("🧩 Список команд синхронизирован.")


# Загрузчики и выгрузчики плагина
# ===============================


@arc.loader
def loader(client: ChioClient) -> None:
    """Действия при загрузке плагина."""
    plugin.add_hook(has_role(RoleLevel.ADMINISTRATOR))
    client.add_plugin(plugin)
