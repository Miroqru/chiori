"""Коробка с утилитами.

Различные полезные команды, которые вы можете использовать.

Предоставляет
-------------

- /avatar [user] - Получает аватар участника

Version: v0.1
Author: Milinuri Nirvalen
"""

import arc
import hikari

plugin = arc.GatewayPlugin("utils")


# определение команд
# ==================

@plugin.include
@arc.slash_command("avatar", description="Получить аватар пользователя.")
async def nya_handler(
    ctx: arc.GatewayContext,
    user: arc.Option[
        hikari.User | None, arc.UserParams("Кого нужно някнуть")
    ] = None
) -> None:
    """простая команда для получения аватара пользоватея.

    Извлекает аватар из экземпляра пользователя.
    Вы можете выбрать как конкретного пользователя, так и выбрать себя,
    оставив аргумент user пустым.
    """
    if user is None:
        user = ctx.user

    embed = hikari.Embed(
        title="О пользователе",
        color=user.accent_color
    ).set_image(user.avatar_url)
    await ctx.respond(embed=embed)


# Загрузчики и выгрузчики плагина
# ===============================

@arc.loader
def loader(client: arc.GatewayClient) -> None:
    client.add_plugin(plugin)

@arc.unloader
def unloader(client: arc.GatewayClient) -> None:
    client.remove_plugin(plugin)
