"""Статистика использования бота.

Version: v0.1.2 (3)
Author: Milinuri Nirvalen
"""

import arc
from loguru import logger

from chioricord.client import ChioClient, ChioContext
from chioricord.plugin import ChioPlugin
from libs.use_stat import CommandsTable

plugin = ChioPlugin("Use stat")


@plugin.inject_dependencies()
async def on_command(
    ctx: ChioContext, table: CommandsTable = arc.inject()
) -> None:
    """Записывает использование команд для статистики."""
    logger.debug(
        "Use {} in {} by {}", ctx.command.name, ctx.guild_id, ctx.user.id
    )
    await table.add_command(ctx.user.id, ctx.guild_id, ctx.command.name)


@arc.loader
def loader(client: ChioClient) -> None:
    """Actions on plugin load."""
    plugin.add_table(CommandsTable)
    client.add_post_hook(on_command)
    client.add_plugin(plugin)
