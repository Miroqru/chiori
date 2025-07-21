"""Статистика использования бота.

Author: Milinuri Nirvalen
Version: v0.1 (1)
"""

import arc
from loguru import logger

from chioricord.db import ChioDB
from libs.use_stat import CommandsTable

plugin = arc.GatewayPlugin("Use stat")


@plugin.inject_dependencies()
async def on_command(
    ctx: arc.GatewayContext, table: CommandsTable = arc.inject()
) -> None:
    """Записывает использование команд для статистики."""
    logger.debug("Use {} in {} by {}", ctx.command.name, ctx.guild_id, ctx.user.id)
    await table.add_command(ctx.user.id, ctx.guild_id, ctx.command.name)


@arc.loader
def loader(client: arc.GatewayClient) -> None:
    """Actions on plugin load."""
    client.add_post_hook(on_command)
    client.add_plugin(plugin)
    cm = client.get_type_dependency(ChioDB)
    cm.register(CommandsTable)


@arc.unloader
def unloader(client: arc.GatewayClient) -> None:
    """Actions on plugin unload."""
    client.remove_plugin(plugin)
