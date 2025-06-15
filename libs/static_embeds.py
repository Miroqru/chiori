"""Статические сообщения.

Инструмент для создания статических команд с сообщениям.
Позволяет куда проще создавать новые команды без использования кода.

Для удобной сборки Embed: https://embed.dan.onl/

Version: v1.0 (1)
Author: Milinuri Nirvalen
"""

from datetime import UTC, datetime

import arc
import hikari
from arc import SlashCommand, SlashSubCommand
from pydantic import BaseModel


class EmbedAuthor(BaseModel):
    """Автор сообщения."""

    name: str
    url: str | None = None
    icon_url: str | None = None


class EmbedField(BaseModel):
    """Поле embed сообщения."""

    name: str | None = None
    value: str | None = None
    inline: bool = False


class EmbedImage(BaseModel):
    """Изображение для Embed."""

    url: str


class EmbedData(BaseModel):
    """Представление discord embed."""

    author: EmbedAuthor | None = None
    fields: list[EmbedField] = []
    image: EmbedImage | None = None
    thumbnail: EmbedImage | None = None

    # Основное содержимое сообщения
    title: str | None = None
    url: str | None = None
    description: str
    color: str | None = None
    timestamp: int | None = None


class StaticCommand(BaseModel):
    """представление статической команды для сборки."""

    name: str
    desc: str
    is_nsfw: bool = False
    embed: EmbedData


def build_embed(emb_data: EmbedData) -> hikari.Embed:
    """Собирает embed из его представления."""
    emb = hikari.Embed(
        title=emb_data.title,
        description=emb_data.description,
        url=emb_data.url,
        color=int(emb_data.color[1:], 16)
        if emb_data.color is not None
        else None,
        timestamp=datetime.fromtimestamp(float(emb_data.timestamp // 1000), UTC)
        if emb_data.timestamp is not None
        else None,
    )

    if emb_data.author is not None:
        emb.set_author(
            name=emb_data.author.name,
            url=emb_data.author.url,
            icon=emb_data.author.icon_url,
        )

    for field in emb_data.fields:
        emb.add_field(field.name, field.value, inline=field.inline)

    if emb_data.image is not None:
        emb.set_image(emb_data.image.url)

    if emb_data.thumbnail is not None:
        emb.set_thumbnail(emb_data.thumbnail.url)

    return emb


class StaticCommands:
    """Сборщик статических команд бота."""

    def __init__(self) -> None:
        self._embeds: dict[str, hikari.Embed] = {}

    def add_command(self, command: StaticCommand) -> SlashCommand:
        """Добавляет новую статическую команду."""
        self._embeds[command.name] = build_embed(command.embed)

        async def _handler(ctx: arc.GatewayContext) -> None:
            await ctx.respond(self._embeds[command.name])

        return SlashCommand(
            callback=_handler,
            name=command.name,
            description=command.desc,
            is_nsfw=command.is_nsfw,
        )

    def add_subcommand(self, command: StaticCommand) -> SlashSubCommand:
        """Добавляет новую статическую саб-команду."""
        self._embeds[command.name] = build_embed(command.embed)

        async def _handler(ctx: arc.GatewayContext) -> None:
            await ctx.respond(self._embeds[command.name])

        return SlashSubCommand(
            callback=_handler,
            name=command.name,
            description=command.desc,
        )
