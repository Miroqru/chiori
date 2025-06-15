"""Статические сообщения.

предоставляет собой команды для отправки статических embeds.
Список команд подгружается из файла настроек.

Version: v0.1 (1)
Author: Milinuri Nirvalen
"""

import json
from pathlib import Path

import arc
from loguru import logger

from libs.static_embeds import EmbedData, StaticCommand, StaticCommands

plugin = arc.GatewayPlugin("Static Embeds")
COMMANDS_PATh = Path("bot_data/static_embeds.json")
sc = StaticCommands()

emb = EmbedData.model_validate(
    {
        "author": {"name": "Info", "url": "https://example.com"},
        "title": "Example Title",
        "url": "https://example.com",
        "description": "This is an example description. Markdown works too!\n\nhttps://automatic.links\n> Block Quotes\n```\nCode Blocks\n```\n*Emphasis* or _emphasis_\n`Inline code` or ``inline code``\n[Links](https://example.com)\n<@123>, <@!123>, <#123>, <@&123>, @here, @everyone mentions\n||Spoilers||\n~~Strikethrough~~\n**Strong**\n__Underline__",
        "fields": [
            {"name": "Field Name", "value": "This is the field value."},
            {
                "name": "The first inline field.",
                "value": "This field is inline.",
                "inline": True,
            },
            {
                "name": "The second inline field.",
                "value": "Inline fields are stacked next to each other.",
                "inline": True,
            },
            {
                "name": "The third inline field.",
                "value": "You can have up to 3 inline fields in a row.",
                "inline": True,
            },
            {
                "name": "Even if the next field is inline...",
                "value": "It won't stack with the previous inline fields.",
                "inline": True,
            },
        ],
        "image": {
            "url": "https://cubedhuang.com/images/alex-knight-unsplash.webp"
        },
        "thumbnail": {"url": "https://dan.onl/images/emptysong.jpg"},
        "color": "#00b0f4",
        "footer": {
            "text": "Example Footer",
            "icon_url": "https://slate.dan.onl/slate.png",
        },
        "timestamp": 1749970578551,
    }
)
command = StaticCommand(
    name="test", desc="Тестируем сборку статических сообщений", embed=emb
)


def load_commands(path: Path) -> list[StaticCommand]:
    """Загружает статические команды из файла."""
    logger.info("Load static commands from {}", path)
    if not path.exists():
        logger.warning("{} not exists to load commands", path)
        return []

    with path.open() as f:
        data = json.loads(f.read())

    return [StaticCommand.model_validate(command) for command in data]


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
