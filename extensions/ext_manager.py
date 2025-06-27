"""Управляет плагинами Chiori.

Его задача управлять загруженными в клиент плагинами во время работы
бота.

Предоставляет
-------------

- /ext list: Список всех доступных расширений.
- /ext load <ext>: Загружает расширение из файла.
- /ext unload <ext>: Выгружает расширение из шиори.
- /ext reload <ext>: Перезагружает расширение.
- /ext sync: Синхронизирует список команд с Discord.

Version: v1.0.1 (7)
Author: Milinuri Nirvalen
"""

from pathlib import Path

import arc
import hikari

from chioricord.config import config

plugin = arc.GatewayPlugin("Extension manager")

cmd_group = plugin.include_slash_group(
    name="ext", description="Управление загруженными расширениями."
)


class NotOwnerError(arc.HookAbortError):
    """Если другой пользователь пытается получить доступ к командам."""


def owner_hook(ctx: arc.GatewayContext) -> None:
    """Проверка на администратора бота."""
    if config.BOT_OWNER != ctx.author.id:
        raise NotOwnerError("This command can use only bot owner,")


# Определение команд
# ==================


@cmd_group.include
@arc.with_hook(owner_hook)
@arc.slash_subcommand("list", description="Список всех доступных расширений.")
async def list_extension(ctx: arc.GatewayContext) -> None:
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
@arc.with_hook(owner_hook)
@arc.slash_subcommand("load", description="Загружает расширение по имени.")
async def load_extension(
    ctx: arc.GatewayContext,
    extension: arc.Option[str, arc.StrParams("Путь до расширения")],  # type: ignore
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
@arc.with_hook(owner_hook)
@arc.slash_subcommand("unload", description="Выгружает расширение по имени.")
async def unload_extension(
    ctx: arc.GatewayContext,
    extension: arc.Option[str, arc.StrParams("Путь до расширения")],  # type: ignore
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
@arc.with_hook(owner_hook)
@arc.slash_subcommand("reload", description="Выгружает расширение по имени.")
async def reload_extension(
    ctx: arc.GatewayContext,
    extension: arc.Option[str, arc.StrParams("Путь до расширения")],  # type: ignore
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
@arc.with_hook(owner_hook)
@arc.slash_subcommand("sync", description="Синхронизация список команд.")
async def sync_commands(ctx: arc.GatewayContext) -> None:
    """Обновляет список команд на стороне Discord.

    это дорогая операция, чтобы выполнять её при каждом действии с расширением.
    """
    res = await ctx.respond("⏳ Синхронизация команд ...")
    await ctx.client.resync_commands()
    await res.edit("🧩 Список команд синхронизирован.")


# Загрузчики и выгрузчики плагина
# ===============================


@arc.loader
def loader(client: arc.GatewayClient) -> None:
    """Действия при загрузке плагина."""
    client.add_plugin(plugin)


@arc.unloader
def unloader(client: arc.GatewayClient) -> None:
    """Действия при выгрузке плагина."""
    client.remove_plugin(plugin)
