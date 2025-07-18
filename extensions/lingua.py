"""Lingua.

Lingua — это помощник, который помогает вам с различными задачами,
предоставляя полезную информацию и выполняя команды.
Он всегда готов ответить на ваши вопросы и сделать общение
персонализированным и приятным.

Предоставляет
-------------

Version: v0.12 (10)
Maintainer: atarwn
Source: https://github.com/atarwn/Lingua
"""

from collections import deque
from dataclasses import dataclass
from datetime import datetime
from typing import Literal, Self, cast

import arc
import hikari
from loguru import logger
from openai import OpenAI
from openai.types.chat import ChatCompletionMessageParam

from chiorium.config import PluginConfig, PluginConfigManager

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


# Дополнительные функции
# ======================


async def _get_channel(
    client: arc.GatewayClient, channel_id: int
) -> hikari.PartialChannel:
    channel = client.cache.get_guild_channel(channel_id)
    if channel is not None:
        return channel
    return await client.rest.fetch_channel(channel_id)


async def _get_guild(client: arc.GatewayClient, guild_id: int) -> hikari.Guild:
    guild = client.cache.get_guild(guild_id)
    if guild is not None:
        return guild
    return await client.rest.fetch_guild(guild_id)


@dataclass(slots=True, frozen=True)
class ChatContext:
    user: hikari.User
    channel: hikari.PartialChannel
    guild: hikari.Guild | None

    @classmethod
    def from_ctx(cls, ctx: arc.GatewayContext) -> Self:
        return cls(ctx.user, ctx.channel, ctx.get_guild())

    @classmethod
    async def from_event(
        cls, client: arc.GatewayClient, event: hikari.MessageCreateEvent
    ) -> Self:
        return cls(
            event.author,
            await _get_channel(client, event.channel_id),
            await _get_guild(client, event.message.guild_id)
            if event.message.guild_id is not None
            else None,
        )

    @property
    def chat_prompt(self) -> str:
        now = datetime.now().strftime("%Y/%m/%d")
        if self.guild is None:
            location = "Do you communicate in private messages."
        else:
            location = f"you are communicating on the {self.guild.name} discord server in the {self.channel.name} channel"
        return f"You're talking to {self.user.display_name} with the username {self.user.username}. Today is {now}. {location}"


def get_info() -> hikari.Embed:
    """Немного информации о расширении."""
    embed = hikari.Embed(
        title="Привет, я Aika!",
        description=(
            "Ваш многофункциональный помощник для решения технических задач.\n"
            "Для начала общения напиши мне личное сообщение, упомяните меня или "
            "ответьте на одно из моих сообщений."
        ),
        color=0x00AAE5,
    )
    embed.set_thumbnail(
        "https://raw.githubusercontent.com/atarwn/Lingua/refs/heads/main/assets/lingua.png"
    )
    embed.set_footer(
        text="Lingua v0.13 © Milinuri, 2024-2025", icon="https://miroq.ru/ava.jpg"
    )
    return embed


# Контекст переписки
# ==================


MessagesT = deque[ChatCompletionMessageParam]
RoleT = Literal["user"] | Literal["system"] | Literal["assistant"]


@dataclass(slots=True)
class UserContext:
    """Пользовательский контекст переписки."""

    model: str
    chat: hikari.Snowflake | None
    messages: MessagesT
    system_prompt: str
    chat_prompt: str

    def add_message(self, content: str, role: RoleT = "user") -> None:
        """Добавляет сообщение в историю."""
        self.messages.append({"role": role, "content": content})  # type: ignore

    @property
    def history(self) -> list[ChatCompletionMessageParam]:
        res: list[ChatCompletionMessageParam] = [
            {"role": "system", "content": self.system_prompt},
            {"role": "system", "content": self.chat_prompt},
        ]
        res.extend(self.messages)
        return res

    def update_chat(self, ctx: ChatContext) -> None:
        """Обновляет информацию о текущем чате."""
        self.chat = ctx.channel.id
        self.chat_prompt = ctx.chat_prompt


HistoryT = dict[int, UserContext]


class MessageStorage:
    """История сообщений с пользователем."""

    def __init__(self, config: LinguaConfig) -> None:
        self.config = config
        self.history: HistoryT = {}
        self.client = OpenAI(base_url=config.api_url, api_key=config.api_key)

    async def create_context(self, ctx: ChatContext) -> UserContext:
        """Создаёт новый контекст переписки с пользователем."""
        return UserContext(
            self.config.model,
            ctx.channel.id,
            deque(maxlen=self.config.history_length),
            self.config.system_prompt,
            ctx.chat_prompt,
        )

    async def set_model(self, ctx: ChatContext, model: str) -> None:
        """Устанавливает модель для AI."""
        context = self.history.get(ctx.user.id)
        if context is None:
            context = await self.create_context(ctx)
        context.model = model

    async def get_completion(self, context: UserContext) -> str | None:
        """Делает запрос к AI модели."""
        return (
            self.client.chat.completions.create(
                model=context.model, messages=context.history
            )
            .choices[0]
            .message.content
        )

    async def generate_answer(self, content: str, ctx: ChatContext) -> str | None:
        """Генерирует некоторый ответ от AI."""
        context = self.history.get(ctx.user.id)
        if context is None:
            context = await self.create_context(ctx)
        elif ctx.channel.id != context.chat:
            context.update_chat(ctx)

        context.add_message(content)
        completion = await self.get_completion(context)
        if completion is None:
            return None

        context.add_message(completion, "assistant")
        return completion


# Обработка событий
# =================


@plugin.listen(hikari.MessageCreateEvent)
@plugin.inject_dependencies
async def on_message(
    event: hikari.MessageCreateEvent, storage: MessageStorage = arc.inject()
) -> None:
    """Ответ на сообщения пользователей."""
    if not event.is_human or event.message.content is None:
        return

    app = cast(hikari.GatewayBotAware, event.app)
    me = app.get_me()
    if me is None:
        raise ValueError("OwnUser can`t be None")

    is_dm = event.message.guild_id is None
    if is_dm:
        content = event.message.content
    elif me.id in (event.message.user_mentions_ids or []):
        content = event.message.content[len(me.mention) + 1 :]
    else:
        return

    context = await ChatContext.from_event(plugin.client, event)

    # attachment = event.message.attachments[0] if event.message.attachments else None
    async with app.rest.trigger_typing(event.channel_id):
        # message = await app.chats.get(event.author_id).send(
        #     app.open_ai_client,
        #     content=content,
        #     image_url=attachment.url if attachment else None,
        # )

        answer = await storage.generate_answer(content, context)
        if answer is None:
            await event.message.respond("⚠️ Ai на это ничего не ответила...")
        elif len(answer) <= MAX_MESSAGE_LENGTH:
            await event.message.respond(answer, reply=not is_dm)
        else:
            await event.message.respond(
                "Сообщение оказалось слишком длинным, держите `.txt` файл.",
                attachment=hikari.Bytes(memoryview(answer.encode()), "message.txt"),
                reply=True,
            )


# определение команд
# ==================


@plugin.include
@arc.slash_command("chat", description="Диалог с AI.")
async def lingua_handler(
    ctx: arc.GatewayContext,
    prompt: arc.Option[str | None, arc.StrParams("Сообщение для AI")] = None,  # type: ignore
    storage: MessageStorage = arc.inject(),
) -> None:
    """Отправляет сообщение в диалог с ботом или же выводит информацию."""
    if prompt is None:
        await ctx.respond(embed=get_info())
        return

    chat_ctx = ChatContext.from_ctx(ctx)
    respond = await ctx.respond("✨ Думаю...")
    async with ctx.client.rest.trigger_typing(ctx.channel_id):
        answer = await storage.generate_answer(prompt, chat_ctx)
        if answer is None:
            await ctx.respond("⚠️ Ai на это ничего не ответила...")
        elif len(answer) <= MAX_MESSAGE_LENGTH:
            await respond.edit(answer)
        else:
            await respond.edit(
                "Сообщение оказалось слишком длинным, держите `.txt` файл.",
                attachment=hikari.Bytes(memoryview(answer.encode()), "message.txt"),
            )


@plugin.include
@arc.slash_command("clear_context", description="Обчищает контекст диалога.")
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
    await ctx.respond("✅ Контекст очищена!", flags=hikari.MessageFlag.EPHEMERAL)


@plugin.include
@arc.slash_command("model", description="Выбрать AI модель для диалога.")
async def set_ai_model(
    ctx: arc.GatewayContext,
    model: arc.Option[str, arc.StrParams("Желаемая модель")],  # type: ignore
    storage: MessageStorage = arc.inject(),
) -> None:
    """Очищает историю сообщений для пользователя."""
    context = ChatContext.from_ctx(ctx)
    await storage.set_model(context, model)
    await ctx.respond(
        f"✅ Выбрана модель `{model}`!", flags=hikari.MessageFlag.EPHEMERAL
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

