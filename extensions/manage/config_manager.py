"""управление настройками.

Позволяет просматривать настройки бота.

Предоставляет
-------------

- /config - Список всех групп настроек.
- /config <group> - Настройки для конкретной группы.

Version: v1.1 (2)
Author: Milinuri Nirvalen
"""

import arc
import hikari

from chioricord.config import PluginConfigManager
from chioricord.hooks import owner_hook

plugin = arc.GatewayPlugin("Config manager")


@plugin.inject_dependencies()
async def group_opts(
    data: arc.AutocompleteData[arc.GatewayClient, str],
    cm: PluginConfigManager = arc.inject(),
) -> list[str]:
    """Авто дополнение для списка расширений."""
    if data.focused_value is None:
        return list(cm.groups)[:25]

    res: list[str] = []
    for group in cm.groups:
        if group.startswith(data.focused_value):
            res.append(group)
    return res[:25]


def config_status(cm: PluginConfigManager) -> hikari.Embed:
    """Общие сведения о настройках."""
    groups = ""
    for group in cm.groups:
        groups += f"\n- `{group}`"
    emb = hikari.Embed(
        title="⚙️ Настройки Chiori",
        description=f"Доступные группы: {groups}",
        color=hikari.Color(0xEECCAA),
    )
    emb.add_field(
        "Подсказка",
        ("- `/config <name>`: просмотреть настройки определённой группы."),
    )
    return emb


def config_group(cm: PluginConfigManager, group: str) -> hikari.Embed:
    """Настройки конкретной группы."""
    config = cm.get_group(group)
    proto = cm.get_proto(group)

    config_params = ""
    for k, v in config:
        config_params += f"\n**{k}**: {v}"

    proto_params = ""
    for k, v in proto.model_fields.items():
        proto_params += f"\n**{k}**: {v.annotation} = {v.default}"
        if v.description is not None:
            proto_params += f"\n> {v.description}"

    emb = hikari.Embed(
        title=f"🔑 Настройки {group}",
        description=proto_params,
        color=hikari.Color(0xEECCAA),
    )
    emb.add_field("Настройки", config_params)
    return emb


# определение команд
# ==================


@plugin.include
@arc.with_hook(owner_hook)
@arc.slash_command("config", description="Настройки Chiori.")
async def nya_handler(
    ctx: arc.GatewayContext,
    group: arc.Option[  # type: ignore
        str | None, arc.StrParams("Группа настроек")
    ] = None,
    cm: PluginConfigManager = arc.inject(),
) -> None:
    """Первая няшная команда для бота.

    Позволяет някнуть участника, пожалуй это достаточно мило.
    Впрочем более эта команда ничего не делает.
    """
    if group is None:
        emb = config_status(cm)
    else:
        emb = config_group(cm, group)

    await ctx.respond(emb)


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
