"""Статические сообщения.

предоставляет собой команды для отправки статических embeds.
Список команд подгружается из файла настроек.

Version: v1.0.1 (3)
Author: Milinuri Nirvalen
"""

from pathlib import Path

import arc
from loguru import logger

from chioricord.client import ChioClient
from chioricord.plugin import ChioPlugin
from libs.static_embeds import StaticCommands, load_commands

plugin = ChioPlugin("Static Embeds")
# TODO: Начать использовать конфиг
COMMANDS_PATh = Path("bot_data/static_embeds.json")


@arc.loader
def loader(client: ChioClient) -> None:
    """Действия при загрузке плагина."""
    sc = StaticCommands()
    commands = load_commands(COMMANDS_PATh)
    for command in commands:
        logger.info("Add command: {}: {}", command.name, command.desc)
        plugin.include(sc.add_command(command))

    client.add_plugin(plugin)
