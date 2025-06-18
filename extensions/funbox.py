"""Коробка с игрушками.

Расширение, которое предоставляет различные забавные команды без
какой-либо определённой тематики.

Предоставляет
-------------

- /ping: Проверить что бот работает.
- /dice: Подбросить кубик.
- /flip: Подбросить монетку.
- /ball: Совет от мудрого шара.

Version: v0.4 (5)
Author: Milinuri Nirvalen
"""

import random

import arc
import hikari

from chioricord.config import PluginConfig, PluginConfigManager

plugin = arc.GatewayPlugin("Funbox")


class FunboxConfig(PluginConfig):
    """Различные настройки для коробки весёлостей."""

    flip_results: list[str] = ["Орла", "Решку"]
    ball_prefix: list[str] = [
        "Совершенно точно ",
        "определённо ",
        "скорее всего ",
        "звезды подсказывают что ",
        "возможно ",
        "вероятно ",
    ]
    ball_result: list[str] = [
        "да",
        "нет",
        "попробуйте позже",
        "не знаю",
        "не уверен",
    ]


# определение команд
# ==================


@plugin.include
@arc.slash_command("ping", description="Проверить работу бота.")
async def ping(ctx: arc.GatewayContext) -> None:
    """Проверить что бот в сети и отвечает на запросы."""
    await ctx.respond("🏓 Понг!")


@plugin.include
@arc.slash_command("dice", description="Подбросить кубик.")
async def roll_dice(
    ctx: arc.GatewayContext,
    sides: arc.Option[int, arc.IntParams("Сколько сторон у кубика (6)")] = 6,
    count: arc.Option[int, arc.IntParams("Сколько будет кубиков (1)")] = 1,
) -> None:
    """Подбрасывает кубик.

    По умолчанию подбрасывает 1 кубик с 6-тью гранями.
    Вы можете переопределить, сколько будет кубиков и сколько будет
    у них граней.
    Сообщение с результатом содержит настройки кубиков, результаты для
    каждого кубика и конечную сумму.
    """
    # Валидация входящих параметров
    sides = min(max(3, sides), 100)
    count = min(max(1, count), 10)
    result = [random.randint(1, sides) for _ in range(count)]

    # Собираем красивое сообщение
    emb = hikari.Embed(
        title="🎲 Подбросили кубики",
        description=(
            "Вы берёте свои любимые кубики.\n"
            "Немного встряхнув их в ладонях, вы, лёгким движением руки,"
            "выбрасываете их на стол.\n\n"
            "Что же тут у нас?"
        ),
        color=hikari.colors.Color(0xF66151),
    )

    # Добавляем результат подсчётов
    if count == 1:
        emb.add_field(name="Итого", value=str(result))
    else:
        str_value = str(result[0])
        for r in result[1:]:
            str_value += f" + {r}"
        str_value += f" = {sum(result)}"
        emb.add_field(name="Итого", value=str_value)

    await ctx.respond(emb)


@plugin.include
@arc.slash_command("flip", description="Подбросить монетку.")
async def flip_coin(
    ctx: arc.GatewayContext, cm: PluginConfigManager = arc.inject()
) -> None:
    """Подбрасывает монетку.

    Вы можете подбросить только одну монетку.
    В результате может выпасть орёл или решка.
    Сообщение с результатом содержит выпавшую сторону монетки.
    """
    config: FunboxConfig = cm.get_group("funbox")
    result = random.randint(0, 1)
    result_str = config.flip_results[result]
    await ctx.respond(f"🪙 Подбросив монетку вы увидели там {result_str}.")


@plugin.include
@arc.slash_command("ball", description="Совет от мудрого шара.")
async def flip_ball(
    ctx: arc.GatewayContext, cm: PluginConfigManager = arc.inject()
) -> None:
    """8 шар.

    Вы можете задать любой вопрос, а мудрый шар подскажет вам ответ.
    На самом деле ответ подбирается случайный.
    Но так ведь даже веселее.
    """
    config: FunboxConfig = cm.get_group("funbox")
    if random.randint(0, 1) == 1:
        prefix = random.choice(config.ball_prefix)
    else:
        prefix = ""
    result = random.choice(config.ball_result)

    await ctx.respond(f"🔮 **Мудрый шар говорит Вам**:\n\n> {prefix}{result}")


@plugin.include
@arc.slash_command("chance", description="Вероятность случайного события")
async def chance(
    ctx: arc.GatewayContext,
    event: arc.Option[str, arc.StrParams("Некоторое событие")],
) -> None:
    """Вероятность случайного события.

    Возвращает случайное число в диапазоне от 0 до 100.
    """
    num = random.randint(0, 100)
    await ctx.respond(f"🎀 Вероятность {event} - {num}%")


# Загрузчики и выгрузчики плагина
# ===============================


@arc.loader
def loader(client: arc.GatewayClient) -> None:
    """Действия при загрузке плагина."""
    client.add_plugin(plugin)
    cm: PluginConfigManager = client.get_type_dependency(PluginConfigManager)
    cm.set_group("funbox", FunboxConfig)


@arc.unloader
def unloader(client: arc.GatewayClient) -> None:
    """Действия при выгрузке плагина."""
    client.remove_plugin(plugin)
