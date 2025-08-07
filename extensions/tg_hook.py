"""Telegram хук для отправки сообщений.

Discord -> Telegram:

- [X] Отправка сообщений.
- [X] Пересылка сообщений.
- [ ] Форматирование сообщений.
- [ ] Отправка медиа.
- [ ] Кросс-ответы.

Telegram -> Discord:

- [ ] Отправка сообщений.
- [ ] Форматирование сообщений.
- [ ] Пересылка сообщений.
- [ ] Отправка медия.
- [ ] Кросс-ответы.

Version: v0.2.2 (6)
Author: Milinuri Nirvalen
"""

from typing import Any

import aiohttp
import arc
import hikari
from pydantic import BaseModel

from chioricord.api import PluginConfig
from chioricord.client import ChioClient, ChioContext
from chioricord.plugin import ChioPlugin

plugin = ChioPlugin("Telegram hook")


class Translator(BaseModel):
    """Правила пересылки сообщений в чатах."""

    from_channel: int
    to_chat: int
    from_users: list[int] | None = None


class TelegramHookConfig(PluginConfig, config="telegram"):
    """Настройки Telegram хука."""

    bot_token: str
    repeaters: list[Translator]

    def get_translator(self, channel_id: int) -> Translator | None:
        """Получает транслятор по id канала."""
        for translator in self.repeaters:
            if translator.from_channel == channel_id:
                return translator
        return None


class TelegramWebhook:
    """Реализация хука для отправки сообщений."""

    def __init__(self, token: str) -> None:
        self.token = token

    async def send_message(self, chat_id: int, message: str) -> dict[str, Any]:
        """Отправляет сообщения в Telegram чат."""
        url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        params = {"chat_id": chat_id, "text": message}
        async with aiohttp.ClientSession() as session:
            async with session.post(url, data=params) as response:
                response.raise_for_status()
                return await response.json()


@plugin.listen(hikari.MessageCreateEvent)
@plugin.inject_dependencies()
async def listener_name(
    event: hikari.MessageCreateEvent,
    hook: TelegramWebhook = arc.inject(),
    config: TelegramHookConfig = arc.inject(),
) -> None:
    """Пересылает сообщения в telegram."""
    if not event.is_human:
        return

    translator = config.get_translator(event.channel_id)
    if translator is None:
        return

    if translator.from_users is None:
        content = f"{event.author.display_name}: {event.message.content}"
    elif event.author.id in translator.from_users:
        content = event.message.content
    else:
        return

    if content is not None:
        await hook.send_message(translator.to_chat, content)


@plugin.include
@arc.slash_command("send", description="Отправляет сообщение в Telegram")
async def send_handler(
    ctx: ChioContext,
    chat_id: arc.Option[int, arc.IntParams("В какой чат отправить сообщение.")],
    message: arc.Option[str, arc.StrParams("Текст сообщения")],
    hook: TelegramWebhook = arc.inject(),
) -> None:
    """Отправляет сообщение в указанный чат."""
    res = await hook.send_message(
        chat_id, f"{ctx.user.display_name}: {message}"
    )
    emb = hikari.Embed(
        title="Отправка сообщения",
        description=message,
        color=hikari.Color(0x66CCFF),
    )
    emb.set_footer(f"chat: {chat_id}")
    emb.add_field("Результат", f"```{str(res)[:1024]}```")
    await ctx.respond(emb)


@plugin.listen(arc.StartedEvent)
async def on_start(event: arc.StartedEvent[ChioClient]) -> None:
    """Подключаемся к сессии."""
    config = event.client.config.get(TelegramHookConfig)
    hook = TelegramWebhook(config.bot_token)
    event.client.set_type_dependency(TelegramWebhook, hook)


@arc.loader
def loader(client: ChioClient) -> None:
    """Actions on plugin load."""
    plugin.set_config(TelegramHookConfig)
    client.add_plugin(plugin)
