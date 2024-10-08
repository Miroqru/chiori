"""Список плагинов.

Предоставляет
-------------

- /plugins - Список плагинов.
- /help - Список всех активных команд бота.
- /help [plugin] - Список команд для конкретного плагина.

Version: v0.3 (7)
Author: Milinuri Nirvalen
"""

import arc
import hikari

# Глобальные переменные
# =====================

plugin = arc.GatewayPlugin("Pluginlist")

# настройки отображения индекса пакетов
# index_url: Ссылка до раздела документации Chioricord
# icon_url: Ссылка на иконку индекса пакетов
index_url = "https://45.89.190.183/chio/commands/"
icon_url = "https://45.89.190.183/chio/images/chio.png"


# определение команд
# ==================

@plugin.include
@arc.slash_command("plugins", description="Список активных плагинов.")
async def plugin_handler(
    ctx: arc.GatewayContext,
) -> None:
    """Список всех загруженных плагинов Чиори.

    Вклчюает в себя перечисление всех навзний плагинов.
    """
    plugins = ctx.client.plugins

    embed = hikari.Embed(
        title=f"📦 Загруженные плагины ({len(plugins)})",
        description=", ".join(sorted(plugins.keys())),
        color=hikari.colors.Color(0x00ffcc)
    ).add_field(
        name="Подсказка",
        value="`/help [plugin]`: Список команд указанного плагина."
    ).set_author(
        name="Индекс плагинов",
        url=index_url,
        icon=icon_url
    )

    await ctx.respond(embed=embed)


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
    res = ''
    other_comands = '\n'
    cmd_count = 0
    for pn, plugin in ctx.client.plugins.items():
        pl_comands_count = 0
        pl_comands_str = ''

        for cmd in plugin.walk_commands(hikari.CommandType.SLASH):
            pl_comands_count += 1
            pl_comands_str += f" /{cmd.name}"

        if pl_comands_count < 3:
            other_comands += pl_comands_str
        else:
            res += f"\n**{pn}**: {pl_comands_str}"
        cmd_count ++ pl_comands_count
    res += other_comands

    return hikari.Embed(
        title=f"🌟 Доступные команды ({cmd_count})",
        description=res,
        color=hikari.colors.Color(0x8866cc)
    ).add_field(
        name="Подсказка",
        value="Используйте `/help [plugin]` для подробностей"
    ).set_author(
        name="Индекс плагинов",
        url=index_url,
        icon=icon_url
    )

def get_plugin_commands(ctx: arc.GatewayContext, plugin_name: str) -> hikari.Embed:
    """Получает список команд для конкретного плагина.

    Если не удалось найти плагин по названиею, выдаст соответвубшее
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
            title="👀 Упсь",
            description=f"Я не смогла найти `{plugin_name}` плагин.",
            color=hikari.colors.Color(0x9966ff)
        ).add_field(
            name="Подсказка",
            value="`/plugins`: Все загруженные плагины Чиори"
        )
    res = ""
    cmd_count = 0
    for command in plugin.walk_commands(hikari.CommandType.SLASH):
        cmd_count += 1
        res += f"\n- `{command.name}`: {command.description}"

    return hikari.Embed(
        title=f"✨ Команда {plugin_name} ({cmd_count}):",
        description=res,
        color=hikari.colors.Color(0xaa00ff)
    ).set_author(
        name="Индекс плагинов",
        url=index_url,
        icon=icon_url
    )


@plugin.include
@arc.slash_command("help", description="Получить список всех команд")
async def help_handler(
    ctx: arc.GatewayContext,
    plugin: arc.Option[
        str | None,
        arc.StrParams("Название плагина для получение его списка команд")
    ] = None
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
