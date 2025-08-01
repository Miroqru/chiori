"""Приветствие.

Приветствует новых участников на сервере.

Version: v1.1.1 (4)
Author: Milinuri Nirvalen
"""

import arc
import hikari

from chioricord.config import PluginConfig, PluginConfigManager

plugin = arc.GatewayPlugin("Welcome")


class WelcomeConfig(PluginConfig):
    """Пример использования настроек для плагина."""

    listen_guild: int

    welcome_channel: int

    welcome_role: int | None = None


_WELCOME_TEXT = (
    "Я **Chiori** (Шиори) - милый бот для вашего лампового сервера.\n"
    "У меня есть множество замечательный функций для вас:\n"
    "- Музыкальный плеер.\n"
    "- Множество мини-игр.\n"
    "- Поощрение активности участников.\n\n"
    "🎉 И многое-многое другое!"
)

_FIRST_STEPS = (
    "Что можно сделать для начала:\n\n"
    "- Почитать документацию Шиори.\n"
    "- Узнать список плагинов `/plugins` и доступных команд `/help`.\n\n"
    "Желаю удачно провести время. 🩷"
)

# Обработка событий
# =================


@plugin.listen(hikari.GuildJoinEvent)
@plugin.inject_dependencies()
async def listener_name(event: hikari.GuildJoinEvent) -> None:
    """Когда кто-то добавляет бота."""
    emb = hikari.Embed(
        title="🎀 Давайте знакомиться!",
        description=_WELCOME_TEXT,
        color=hikari.Color(0xFF9966),
    )
    emb.set_author(
        name="Документация Chioricord",
        url="https://miroq.ru/chio/",
        icon="https://miroq.ru/logo.png",
    )
    emb.set_thumbnail("https://miroq.ru/chio/images/chio.png")
    emb.add_field("Первые шаги", _FIRST_STEPS)

    guild = event.get_guild() or await event.app.rest.fetch_guild(
        event.guild_id
    )
    channel = guild.system_channel_id
    if channel is not None:
        await event.app.rest.create_message(channel, emb)


@plugin.listen(hikari.MemberCreateEvent)
@plugin.inject_dependencies()
async def on_join(
    event: hikari.MemberCreateEvent, config: WelcomeConfig = arc.inject()
) -> None:
    """Когда кто-то заходит на сервере."""
    if event.user.is_bot or event.guild_id != config.listen_guild:
        return

    if config.welcome_role is not None:
        await event.member.add_role(config.welcome_role)

    emb = hikari.Embed(
        title="Добро пожаловать.",
        description=f"Мы рабы приветствовать {event.member.mention}!",
        color=hikari.Color(0x99FFCC),
    )
    emb.set_thumbnail(event.member.make_avatar_url())
    emb.set_footer(
        text="С любовью команда Salormoon", icon="https://miroq.ru/ava.jpg"
    )
    guild = event.member.get_guild() or await event.app.rest.fetch_guild(
        event.member.guild_id
    )
    channel = guild.system_channel_id or config.welcome_channel
    await event.app.rest.create_message(channel, emb)


# Загрузчики и выгрузчики плагина
# ===============================


@arc.loader
def loader(client: arc.GatewayClient) -> None:
    """Действия при загрузке плагина."""
    client.add_plugin(plugin)
    cm = client.get_type_dependency(PluginConfigManager)
    cm.register("welcome", WelcomeConfig)


@arc.unloader
def unloader(client: arc.GatewayClient) -> None:
    """Действия при выгрузке плагина."""
    client.remove_plugin(plugin)
