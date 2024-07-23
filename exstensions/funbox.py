"""Коробка с игрушками.

Расширение, которое предоставляет различные забавные команды без
какой-либо определённой тематики.

Предоставляет
-------------

- /ping: Проверить что бот работает.

Version: v0.2 (2)
Author: Milinuri Nirvalen
"""

import random

import arc
import hikari

plugin = arc.GatewayPlugin("funbox")


# определение команд
# ==================

@plugin.include
@arc.slash_command("ping", description="Проверить что бот работает")
async def ping(ctx: arc.GatewayContext):
    await ctx.respond("Понг!")

@plugin.include
@arc.slash_command("dice", description="Подбросить кубик")
async def dice(
    ctx: arc.GatewayContext,
    sides: arc.Option[
        int, arc.IntParams("Сколько сторон у кубика (6)")
    ] = 6,
    count: arc.Option[
        int, arc.IntParams("Сколько будет кубиков (1)")
    ] = 1
):
    # Валидация входящих параметров
    sides = min(max(3, sides), 100)
    count = min(max(1, count), 10)
    if count > 1:
        result = [random.randint(1, sides) for _ in range(count)]
    else:
        result = random.randint(1, sides)

    # Собираем красивое сообщение
    emb = hikari.Embed(
        title="🎲 Подбросили кубики",
        description=("Вы берёте свои любимые кубики.\n"
            "Немного потреся их в ладонях, вы, лёгким движением руки,"
            "выбрасываете их на стол.\n\n"
            "Чтоже тут у нас?"
        ),
        color=hikari.colors.Color(0xf66151)
    )


    # Доабвляем рузальтат подсчётов
    if count == 1:
        emb.add_field(name="Итого", value=str(result))
    else:
        str_value = str(result[0])
        for r in result[1:]:
            str_value += f" + {r}"
        str_value += f" = {sum(result)}"
        emb.add_field(name="Итого", value=str_value)

    return await ctx.respond(embed=emb)


# Загрузчики и выгрузчики плагина
# ===============================

@arc.loader
def loader(client: arc.GatewayClient) -> None:
    client.add_plugin(plugin)


@arc.unloader
def unloader(client: arc.GatewayClient) -> None:
    client.remove_plugin(plugin)
