"""Контекст для AI переписки с пользователем."""

from collections import deque
from dataclasses import dataclass
from datetime import datetime
from typing import Self

import hikari
from openai import AsyncOpenAI
from openai.types.chat import ChatCompletionMessageParam

from chioricord.api import PluginConfig
from chioricord.client import ChioClient, ChioContext
from libs.lingua import MessagesTable, RoleT

MessagesT = deque[ChatCompletionMessageParam]

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
    """Ссылка на OpenAI совместимый API для нейросети."""

    api_key: str
    """API ключ для взаимодействия с моделью."""

    model: str = "meta-llama/llama-4-maverick:free"
    """Название модели по умолчанию для использования."""

    search_model: str | None = None
    """Модель для поиска информации в интернете."""

    system_prompt: str = DEFAULT_PROMPT
    """
    Системное сообщение, который будет скармливаться нейросети перед
    началом диалога с пользователем.
    """

    history_length: int = 20
    """
    Размер истории сообщений.
    Каждое сообщение попадает в хранилище.
    при переполнении, старые сообщение удаляются.
    """

    rate_limit: int | None = None
    """Ограничение на скорость общения с ИИ.

    Измеряется в секундах.
    """

    image_watermark: str | None = None
    """Водяной знак для изображения.
    Будет добавляться если у пользователя нет подписки.
    """

    ai_models: list[str]
    """Список всех доступных моделей."""


async def _get_channel(
    client: ChioClient, channel_id: int
) -> hikari.PartialChannel:
    channel = client.cache.get_guild_channel(channel_id)
    if channel is not None:
        return channel
    return await client.rest.fetch_channel(channel_id)


async def _get_guild(client: ChioClient, guild_id: int) -> hikari.Guild:
    guild = client.cache.get_guild(guild_id)
    if guild is not None:
        return guild
    return await client.rest.fetch_guild(guild_id)


@dataclass(slots=True, frozen=True)
class ChatContext:
    user: hikari.User
    channel: hikari.PartialChannel
    guild: hikari.Guild | None

    @property
    def guild_id(self) -> int | None:
        if self.guild is None:
            return None
        return self.guild.id

    @classmethod
    def from_ctx(cls, ctx: ChioContext) -> Self:
        return cls(ctx.user, ctx.channel, ctx.get_guild())

    @classmethod
    async def from_event(
        cls, client: ChioClient, event: hikari.MessageCreateEvent
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


# TODO: Разобрать контекст
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


class MessageStorage:
    """История сообщений с пользователем."""

    def __init__(self, config: LinguaConfig, messages: MessagesTable) -> None:
        self.config = config
        self.history: dict[int, UserContext] = {}
        self.client = AsyncOpenAI(
            base_url=config.api_url, api_key=config.api_key
        )
        self.messages = messages

    async def create_context(self, ctx: ChatContext) -> UserContext:
        """Создаёт новый контекст переписки с пользователем."""
        return UserContext(
            self.config.model,
            ctx.channel.id,
            deque(maxlen=self.config.history_length),
            self.config.system_prompt,
            ctx.chat_prompt,
        )

    async def user_context(self, ctx: ChatContext) -> UserContext:
        context = self.history.get(ctx.user.id)
        if context is None:
            context = await self.create_context(ctx)
            self.history[ctx.user.id] = context
        return context

    async def set_model(self, ctx: ChatContext, model: str) -> None:
        """Устанавливает модель для AI."""
        context = self.history.get(ctx.user.id)
        if context is None:
            context = await self.create_context(ctx)
        context.model = model

    async def add_message(
        self,
        user: UserContext,
        chat: ChatContext,
        content: str,
        role: RoleT = "user",
    ) -> None:
        """Добавляет сообщение в историю."""
        user.add_message(content)
        await self.messages.add_message(
            chat.user.id, chat.guild_id, chat.channel.id, content, role
        )

    async def generate_answer(
        self, content: str, chat: ChatContext
    ) -> str | None:
        """Генерирует некоторый ответ от AI."""
        user = await self.user_context(chat)
        if chat.channel.id != user.chat:
            user.update_chat(chat)

        res = await self.client.chat.completions.create(
            model=user.model, messages=user.history
        )
        if not len(res.choices):
            return None

        completion = res.choices[0].message.content
        if completion is None:
            return None

        await self.add_message(user, chat, content)
        await self.add_message(user, chat, completion, "assistant")
        return completion
