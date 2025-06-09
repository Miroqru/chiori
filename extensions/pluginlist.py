"""Список плагинов.

Предоставляет
-------------

- /plugins - Список плагинов.
- /help - Список всех активных команд бота.
- /help [plugin] - Список команд для конкретного плагина.

Version: v0.4 (9)
Author: Milinuri Nirvalen
"""

import arc
import hikari

# Глобальные переменные
# =====================

plugin = arc.GatewayPlugin("Plugin list")

# настройки отображения индекса пакетов
# index_url: Ссылка до раздела документации Chioricord
# icon_url: Ссылка на иконку индекса пакетов
index_url = "https://miroq.ru/chio/commands/"
icon_url = "https://miroq.ru/chio/images/chio.png"


_FOOTER_TEXT = "Chiori v0.4"

# определение команд
# ==================


@plugin.include
@arc.slash_command("plugins", description="Список активных плагинов.")
async def plugin_handler(
    ctx: arc.GatewayContext,
) -> None:
    """Список всех загруженных плагинов Чиори.

    Включает в себя перечисление всех названий плагинов.
    """
    plugins = ctx.client.plugins
    emb = hikari.Embed(
        title=f"🎀 Расширения ({len(plugins)})",
        description=", ".join(sorted(plugins.keys())),
        color=0x00FFCC,
    )
    emb.add_field(
        name="Подсказка",
        value="`/help [plugin]`: Список команд указанного плагина.",
    )
    emb.set_author(name="Индекс плагинов", url=index_url, icon=icon_url)
    emb.set_footer(_FOOTER_TEXT)
    await ctx.respond(emb)


# Информация о списке команд
# ==========================


def get_all_commands(ctx: arc.GatewayContext) -> hikari.Embed:
    """Получает все команды бота.

    Кратко выводит названия всех команд, которые можно использовать
    пользователям бота.

    :param ctx: Контекст команды, для получения экземпляра клиента бота.
    :type ctx: arc.GatewayContext
    :return: Сообщение со списком всех команд бота.
    :rtype: hikari.Embed
    """
    res = ""
    other_commands = "\n**Прочие**:"
    cmd_count = 0
    for pn, plugin in ctx.client.plugins.items():
        pl_commands_count = 0
        pl_commands_str = ""

        for cmd in plugin.walk_commands(hikari.CommandType.SLASH):
            pl_commands_count += 1
            pl_commands_str += f" {cmd.display_name}"

        if pl_commands_count < 3:
            other_commands += pl_commands_str
        else:
            res += f"\n**{pn}**: {pl_commands_str}"
        cmd_count += pl_commands_count
    res += other_commands

    return (
        hikari.Embed(
            title=f"🌟 Доступные команды ({cmd_count})",
            description=res,
            color=hikari.colors.Color(0x8866CC),
        )
        .add_field(
            name="Подсказка",
            value="Используйте `/help [plugin]` для подробностей",
        )
        .set_author(name="Индекс плагинов", url=index_url, icon=icon_url)
        .set_footer(_FOOTER_TEXT)
    )


def get_plugin_commands(
    ctx: arc.GatewayContext, plugin_name: str
) -> hikari.Embed:
    """Получает список команд для конкретного плагина.

    Если не удалось найти плагин по названиям, выдаст соответствующие
    предупреждение.
    Будет предоставлен список команд с кратким их описанием.

    :param ctx: Контекст команд, для получение экземпляра клиента.
    :type ctx: arc.GatewayContext
    :param plugin_name: Название плагина, для получения его команд.
    :type plugin_name: str
    :return: Сообщение со списком команд плагина или ошибкой поиска.
    :rtype: hikari.Embed
    """
    plugin = ctx.client.plugins.get(plugin_name)
    if plugin is None:
        return hikari.Embed(
            title="👀 У-упс-ь",
            description=f"Я не смогла найти `{plugin_name}` плагин.",
            color=hikari.colors.Color(0x9966FF),
        ).add_field(
            name="Подсказка", value="`/plugins`: Все загруженные плагины Чиори"
        )
    res = ""
    cmd_count = 0
    for command in plugin.walk_commands(hikari.CommandType.SLASH):
        cmd_count += 1
        res += f"\n- `{command.display_name}`: {command.description}"

    return (
        hikari.Embed(
            title=f"✨ Команда {plugin_name} ({cmd_count}):",
            description=res,
            color=hikari.colors.Color(0xAA00FF),
        )
        .set_author(name="Индекс плагинов", url=index_url, icon=icon_url)
        .set_footer(_FOOTER_TEXT)
    )


@plugin.include
@arc.slash_command("help", description="Получить список всех команд")
async def help_handler(
    ctx: arc.GatewayContext,
    plugin: arc.Option[
        str | None,
        arc.StrParams("Название плагина для получение его списка команд"),
    ] = None,
) -> None:
    """Отображает список команд.

    Если не переданы аргументы, кратко выдаст справку о всех доступных
    командах бота.
    Если передать название плагина, то выдаст команды конкретного
    плагина с их кратким описанием.
    """
    if plugin is None:
        embed = get_all_commands(ctx)
    else:
        embed = get_plugin_commands(ctx, plugin_name=plugin)

    await ctx.respond(embed=embed)


# Загрузчики и выгрузчики плагина
# ===============================


@arc.loader
def loader(client: arc.GatewayClient) -> None:
    """Действия при загрузке плагина."""
    client.add_plugin(plugin)


@arc.unloader
def unloader(client: arc.GatewayClient) -> None:
    """Действия при выгрузке плагина."""
    client.remove_plugin(plugin)
