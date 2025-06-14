"""Чистка последствий рейда сервера.

Использовалась во время атаки на один из серверов.
Для использования требуются права администратора сервера.

Должен настраиваться пож каждый конкретный случай рейда.

Version: v1.0 (1)
Author: Milinuri Nirvalen
"""

import arc
from loguru import logger

plugin = arc.GatewayPlugin("Unraid")


# определение команд
# ==================


@plugin.include
@arc.slash_command("unraid", description="Чистка последствий рейда.")
async def unraid(
    ctx: arc.GatewayContext,
    channel_name: arc.Option[
        str | None, arc.StrParams("Имя канал для очистки")
    ] = "переезд",
) -> None:
    """Чистка последствий рейда на сервер.

    Удаляет все каналы с заданным именем.
    """
    guild = ctx.get_guild()
    if guild is None:
        await ctx.respond("Вы должны выполнить эту команду в гильдии.")
        return

    res = await ctx.respond(
        f"⚡ Начата чистка каналов с названием: `{channel_name}`\n"
        f"🔎 **Гильдия**: {guild.id}"
    )

    logger.info("Start unraid process")
    delete_counter = 0
    for c_id, channel in guild.get_channels().items():
        if channel.name == channel_name:
            await channel.delete()
            delete_counter += 1
    logger.info("End unraid")

    await res.edit(
        f"✅ Чистка каналов с именем `{channel_name}` завершена!\n"
        f"⚡ **Удалено**: {delete_counter} каналов.\n"
        f"🔎 **Гильдия**: {guild.id}"
    )


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
