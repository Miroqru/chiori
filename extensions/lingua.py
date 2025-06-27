"""Lingua.

Lingua — это помощник, который помогает вам с различными задачами,
предоставляя полезную информацию и выполняя команды.
Он всегда готов ответить на ваши вопросы и сделать общение
персонализированным и приятным.

TODO: Сделать нормальное хранилище для настроек.

Предоставляет
-------------

Version: v0.10.1 (7)
Maintainer: atarwn
Source: https://github.com/atarwn/Lingua
"""

from collections import deque
from collections.abc import Iterator
from typing import cast

import arc
import hikari
from loguru import logger
from openai import OpenAI
from openai.types.chat import ChatCompletionMessageParam

from chioricord.config import PluginConfig, PluginConfigManager

# Глобальные переменные
# =====================

plugin = arc.GatewayPlugin("lingua")


class LinguaConfig(PluginConfig):
    """Настройки для Lingua."""

    api_key: str
    api_url: str
    model: str = "meta-llama/llama-4-maverick:free"

    # Кормим нейронке, чтобы выдавала хорошие ответы
    system_prompt: str

    history_length: int = 20


# Немножечко типов
MessagesT = deque[ChatCompletionMessageParam]
HistoryT = dict[int, MessagesT]


class MessageStorage:
    """История сообщений с пользователем."""

    def __init__(self, config: LinguaConfig) -> None:
        self.config = config
        self.history: HistoryT = {}
        self.client = OpenAI(base_url=config.api_url, api_key=config.api_key)

    async def get_completion(self, messages: MessagesT) -> str | None:
        """Делает запрос к AI модели."""
        return (
            self.client.chat.completions.create(
                extra_headers={
                    "HTTP-Referer": "https://lingua.qwa.su/",
                    "X-Title": "Lingua AI",
                },
                model=self.config.model,
                messages=messages,
            )
            .choices[0]
            .message.content
        )

    async def add_to_history(self, user_id: int, message: str) -> None:
        """Добавляет новое сообщение в историю."""
        if user_id not in self.history:
            self.history[user_id] = deque(maxlen=self.config.history_length)

            self.history[user_id].append(
                {"role": "system", "content": self.config.system_prompt}
            )
        self.history[user_id].append({"role": "user", "content": message})

    async def generate_answer(self, user_id: int, message: str) -> str | None:
        """Генерирует некоторый ответ от AI."""
        await self.add_to_history(user_id, message)
        completion = await self.get_completion(self.history[user_id])
        if completion is None:
            return None
        self.history[user_id].append(
            {"role": "assistant", "content": completion}
        )
        return completion


# Дополнительные функции
# ======================


def get_info() -> hikari.Embed:
    """Немного информации о расширении."""
    embed = hikari.Embed(
        title="Привет, я Lingua!",
        description=(
            "Lingua — Ваш многофункциональный помощник для "
            "решения технических задач."
        ),
        color=0x00AAE5,
    )
    embed.set_thumbnail(
        "https://raw.githubusercontent.com/atarwn/Lingua/refs/heads/main/assets/lingua.png"
    )
    embed.set_footer(text="Lingua v0.10 © Qwaderton Labs, 2024-2025")
    return embed


def iter_message(text: str, max_length: int = 2000) -> Iterator[str]:
    """Разбивает больше сообщение на кусочки по 2000 символов."""
    while len(text) > 0:
        if len(text) <= max_length:
            yield text
            break

        split_at = text.rfind(" ", 0, max_length)

        # Не найдено пробелов, вынужденно разбиваем по max_length
        if split_at == -1:
            chunk = text[:max_length]
            remaining = text[max_length:]

        # Разбиваем после пробела
        else:
            chunk = text[: split_at + 1]
            remaining = text[split_at + 1 :]

        yield chunk
        text = remaining


# определение команд
# ==================


@plugin.include
@arc.slash_command("lingua", description="Диалог с AI.")
async def lingua_handler(
    ctx: arc.GatewayContext,
    message: arc.Option[str | None, arc.StrParams("Сообщение для AI")] = None,  # type: ignore
    storage: MessageStorage = arc.inject(),
) -> None:
    """Отправляет сообщение в диалог с ботом или же выводит информацию."""
    if message is None:
        await ctx.respond(embed=get_info())
        return
    else:
        resp = await ctx.respond("⏳ Генерация ответа...")
        answer = await storage.generate_answer(ctx.user.id, message)
        if answer is None:
            await ctx.respond("⚠️ Ai на это ничего не ответила...")
            return

        answer_gen = iter_message(answer)
        await resp.edit(next(answer_gen))

    # Отправляем все оставшиеся кусочки
    for message_chunk in answer_gen:
        await ctx.respond(message_chunk)


@plugin.include
@arc.slash_command(
    "reset_dialog", description="Сбрасывает диалог с пользователем."
)
async def reset_ai_dialog(
    ctx: arc.GatewayContext, storage: MessageStorage = arc.inject()
) -> None:
    """Очищает историю сообщений для пользователя."""
    if ctx.user.id not in storage.history:
        await ctx.respond(
            "⚠ У вас нет сохранённых сообщений.",
            flags=hikari.MessageFlag.EPHEMERAL,
        )
    storage.history.pop(ctx.user.id)
    await ctx.respond("✅ История очищена!", flags=hikari.MessageFlag.EPHEMERAL)


# Загрузчики и выгрузчики плагина
# ===============================


@arc.loader
def loader(client: arc.GatewayClient) -> None:
    """Действия при загрузке плагина."""
    client.add_plugin(plugin)

    cm = client.get_type_dependency(PluginConfigManager)
    cm.register("lingua", LinguaConfig)

    logger.info("Init AI message storage")
    # FIXME: Выглядит как костыль какой-то. по сути возможно так и есть.
    config = cast(LinguaConfig, cm.get_group("lingua"))
    storage = MessageStorage(config)
    client.set_type_dependency(MessageStorage, storage)


@arc.unloader
def unloader(client: arc.GatewayClient) -> None:
    """Действия при выгрузке плагина."""
    client.remove_plugin(plugin)
