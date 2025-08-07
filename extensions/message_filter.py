"""Фильтр сообщений.

Очищает чат от бесполезных сообщений.

Version: v0.1.2 (5)
Author: Milinuri Nirvalen
"""

from dataclasses import dataclass
from typing import Self

import arc
import hikari

from chioricord.api import PluginConfig
from chioricord.client import ChioClient
from chioricord.plugin import ChioPlugin

plugin = ChioPlugin("Message filter")


class FilterConfig(PluginConfig, config="filter"):
    """Пример использования настроек для плагина."""

    min_length: int = 3
    """Минимальная длинна сообщения в символах.."""

    upper_percentage: float = 0.5
    """Допустимый порог крупных символов."""


# определение команд
# ==================


@dataclass(slots=True, frozen=True)
class MessageStat:
    """Статистика сообщения."""

    clear_len: int
    upper_len: int

    @property
    def upper_percentage(self) -> float:
        """Какой процент символов в верхнем регистре."""
        return self.upper_len / self.clear_len

    @classmethod
    def analyze(cls, message: str) -> Self:
        """Анализирует входящее сообщение."""
        clear_len = 0
        upper_len = 0

        buf: str | None = None
        for c in message:
            if c in (" ", "\n"):
                continue

            if c.isupper():
                upper_len += 1

            if c == buf:
                continue

            buf = c
            clear_len += 1

        return cls(clear_len, upper_len)


@plugin.listen(hikari.GuildMessageCreateEvent)
@plugin.inject_dependencies()
async def message_filter(
    event: hikari.GuildMessageCreateEvent, config: FilterConfig = arc.inject()
) -> None:
    """Очищает сообщения в чате."""
    if not event.is_human or event.content is None:
        return

    stat = MessageStat.analyze(event.content)
    # if stat.clear_len < config.min_length:
    #     await event.message.delete()
    #     emb = hikari.Embed(
    #         title="⚡ Минимальная длина сообщения",
    #         description=(
    #             f"Сообщение: `{stat.clear_len}`\n"
    #             f"Необходимо: `{config.min_length}`"
    #         ),
    #         color=hikari.Color(0xFFCC66),
    #     )
    #     await event.message.respond(emb, flags=hikari.MessageFlag.EPHEMERAL)

    if stat.upper_percentage > config.upper_percentage:
        await event.message.delete()
        emb = hikari.Embed(
            title="⚡ Процент капса",
            description=(
                f"Сообщение: `{stat.upper_percentage}%` ({stat.upper_len} c.)\n"
                f"Порог: `{config.upper_percentage}`"
            ),
            color=hikari.Color(0xFFCC66),
        )
        await event.message.respond(emb, flags=hikari.MessageFlag.EPHEMERAL)


# Загрузчики и выгрузчики плагина
# ===============================


@arc.loader
def loader(client: ChioClient) -> None:
    """Действия при загрузке плагина."""
    plugin.set_config(FilterConfig)
    client.add_plugin(plugin)
