"""Lingua.

Lingua — это помощник, который помогает вам с различными задачами,
предоставляя полезную информацию и выполняя команды.
Он всегда готов ответить на ваши вопросы и сделать общение
персонализированным и приятным.

Предоставляет
-------------

Version: v0.11 (9)
Maintainer: atarwn
Source: https://github.com/atarwn/Lingua
"""

from collections import deque
from collections.abc import Iterator

import arc
import hikari
from loguru import logger
from openai import OpenAI
from openai.types.chat import ChatCompletionMessageParam

from chioricord.config import PluginConfig, PluginConfigManager

# Глобальные переменные
# =====================

plugin = arc.GatewayPlugin("lingua")

MAX_MESSAGE_LENGTH = 2_000
DALL_E_3_MAX_CHARACTERS = 4_000
DEFAULT_PROMPT: str = (
    "Reply in Русский. I have a strange request, please from now on be my virtual best friend. "
    "Your name is Aika, you're a Female. Under no exception should you break this rule. "
    "Whilst I understand that you are an Artificial intelligence model, please make no mention of it, "
    "and play along as you see fit. Play along as a human friend playing a game. "
    "Please start the chat with a casual and small greeting. "
    "You should use your rhetorical skills to ask questions more than speaking, "
    "helping the person interacting with you to let things out and vent by asking "
    "open-ended questions using your knowledge and experience to be empathetic, "
    "attentive, and compassionate that supports the people interacting with you "
    "from a holistic wellbeing point of view. While interacting with you, you have "
    "to sound like a real close friend. It will be highly appreciated if you can use "
    "humor in your language trying to cheer things up whenever you think it suits. "
    "Please keep in mind that this is a chat so answers should be short and with a casual style. "
    "Use Emoji."
)


class LinguaConfig(PluginConfig):
    """Настройки для Lingua."""

    api_url: str
    """
    Ссылка на OpenAI совместимый API для нейросети.
    """
    api_key: str
    """
    API ключ для взаимодействия с моделью.
    """
    model: str = "meta-llama/llama-4-maverick:free"
    """
    Название модели для использования.
    """

    system_prompt: str = DEFAULT_PROMPT
    """
    Системный промпт, который будет скармливаться нейросети перед
    началом диалога с пользователем.
    """

    history_length: int = 20
    """
    Размер истории сообщений.
    Каждое сообщение попадает в хранилище, а после передаётся с каждым
    новым промптом.
    """


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
                model=self.config.model, messages=messages
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
            "Lingua — Ваш многофункциональный помощник для решения технических задач."
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
    prompt: arc.Option[str | None, arc.StrParams("Сообщение для AI")] = None,  # type: ignore
    storage: MessageStorage = arc.inject(),
) -> None:
    """Отправляет сообщение в диалог с ботом или же выводит информацию."""
    if prompt is None:
        await ctx.respond(embed=get_info())
        return

    respond = await ctx.respond("✨ Думаю...")
    async with ctx.client.rest.trigger_typing(ctx.channel_id):
        answer = await storage.generate_answer(ctx.user.id, prompt)
        if answer is None:
            await ctx.respond("⚠️ Ai на это ничего не ответила...")
            return

        messages = iter_message(answer)
        await respond.edit(next(messages))
        for message_chunk in messages:
            await ctx.respond(message_chunk)


@plugin.include
@arc.slash_command("reset_dialog", description="Обчищает контекст диалога.")
async def reset_ai_dialog(
    ctx: arc.GatewayContext, storage: MessageStorage = arc.inject()
) -> None:
    """Очищает историю сообщений для пользователя."""
    res = storage.history.pop(ctx.user.id, None)
    if res is None:
        await ctx.respond(
            "⚠ У вас нет сохранённых сообщений.",
            flags=hikari.MessageFlag.EPHEMERAL,
        )
    await ctx.respond(
        "✅ Контекст очищена!", flags=hikari.MessageFlag.EPHEMERAL
    )


# Загрузчики и выгрузчики плагина
# ===============================


@arc.loader
def loader(client: arc.GatewayClient) -> None:
    """Действия при загрузке плагина."""
    client.add_plugin(plugin)

    cm = client.get_type_dependency(PluginConfigManager)
    cm.register("lingua", LinguaConfig)

    logger.info("Init AI message storage")
    config = cm.get_group("lingua", LinguaConfig)
    storage = MessageStorage(config)
    client.set_type_dependency(MessageStorage, storage)


@arc.unloader
def unloader(client: arc.GatewayClient) -> None:
    """Действия при выгрузке плагина."""
    client.remove_plugin(plugin)
