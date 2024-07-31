"""Список плагинов.

Предоставляет
-------------

- /plugins - Список плагинов
- /help - Список всех активных команд бота
- /help [plugin] - Список команд для конкретного плагина

Version: v0.1 (5)
Author: Milinuri Nirvalen
"""

import arc
import hikari

# Глобальные переменные
# =====================

plugin = arc.GatewayPlugin("Pluginlist")


# определение команд
# ==================

@plugin.include
@arc.slash_command("plugins", description="Список активных плагинов.")
async def plugin_handler(
    ctx: arc.GatewayContext,
) -> None:
    """Список всех загруженных плагинов бота."""
    plugins = ctx.client.plugins

    embed = hikari.Embed(
        title=f"Список плагинов ({len(plugins)})",
        description=", ".join(plugins.keys()),
        color=hikari.colors.Color(0x00ffcc)
    )
    # .add_field(
    #     name="Подсказка",
    #     value="Введите `/plugins [plugin_name]` для подробной информации."
    # )

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
    res = ", ".join([
        command.name
        for command in ctx.client.walk_commands(hikari.CommandType.SLASH)
    ])

    return hikari.Embed(
        title="🌟 Список команд",
        description=res,
        color=hikari.colors.Color(0xaa00ff)
    ).add_field(
        name="Подсказка",
        value="Используйте `/help [plugin]` для подробностей"
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
            title="Плагин не найден",
            description=f"Я не смогла найти плагин `{plugin_name}`",
            color=hikari.colors.Color(0xff00aa)
        )
    res = ""
    for command in plugin.walk_commands(hikari.CommandType.SLASH):
        res += f"\n- `{command.name}`: {command.description}"

    return hikari.Embed(
        title=f"Команда плагина {plugin_name}:",
        description=res,
        color=hikari.colors.Color(0xaa00ff)
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
