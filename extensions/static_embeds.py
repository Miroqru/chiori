"""Статические сообщения.

предоставляет собой команды для отправки статических embeds.
Список команд подгружается из файла настроек.

Version: v1.0 (2)
Author: Milinuri Nirvalen
"""

from pathlib import Path

import arc
from loguru import logger

from libs.static_embeds import StaticCommands, load_commands

plugin = arc.GatewayPlugin("Static Embeds")
COMMANDS_PATh = Path("bot_data/static_embeds.json")
sc = StaticCommands()


@arc.loader
def loader(client: arc.GatewayClient) -> None:
    """Действия при загрузке плагина."""
    commands = load_commands(COMMANDS_PATh)
    for command in commands:
        logger.info("Add command: {}: {}", command.name, command.desc)
        plugin.include(sc.add_command(command))

    client.add_plugin(plugin)


@arc.unloader
def unloader(client: arc.GatewayClient) -> None:
    """Действия при выгрузке плагина."""
    client.remove_plugin(plugin)
