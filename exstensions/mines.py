"""Игра Сапёр.

Предоставляет
-------------

- /mines - Начать игру

Version: v0.1 (1)
Author: Milinuri Nirvalen
"""

import random

import arc
import hikari
import miru

from icecream import ic


plugin = arc.GatewayPlugin("mines")


def get_game_status(view) -> hikari.Embed:
     return hikari.Embed(
        title="💣 Сапёр",
        description=(
            "Хотите попробовать свои силы?\n"
            "В этой игре вам предстоит обезвредить минное поле."
        ),
        color=hikari.colors.Color(0x00ccff)
    ).add_field(
        name="Правила игры просты:",
        value=(
            "- Нажмите на поле, чтобы его обезвредить.\n"
            "- Число укажет сколько бомб рядом с вашим полем.\n"
            "- Если вы попадётесь на бомбу, игра закончится."
        )
    ).add_field(name="Всего бомб", value=str(view.total_bombs), inline=True
    ).add_field(name="Осталось клеток", value=str(view.cels_left), inline=True)


class EmptyButton(miru.Button):
    def __init__(self, index: int) -> None:
        super().__init__(
            label="?",
            style=hikari.ButtonStyle.SECONDARY
        )
        self.index = index


    async def callback(self, ctx: miru.ViewContext) -> None:
        self.disabled = True
        nerby_bombs = self.view.count_bombs(self.index)
        if nerby_bombs > 0:
            self.style = hikari.ButtonStyle.PRIMARY
        self.label = str(nerby_bombs)
        self.view.cels_left -= 1

        if self.view.cels_left == 0:
            self.view.stop()
            await ctx.edit_response(embed=hikari.Embed(
                title="💣 Сапёр / Игра пройдена",
                description=(
                        "Поздравляем с успешным прохождением игры.\n"
                        "Мы и не сомневались в том, что вы сможете победить."
                    ),
                color=hikari.colors.Color(0x8ff0a4)
                ),
                components=None
            )
        else:
            await ctx.edit_response(
                embed=get_game_status(self.view),
                components=self.view
            )

class BombButton(miru.Button):
    def __init__(self, index: int) -> None:
        super().__init__(
            label="?",
            style=hikari.ButtonStyle.SECONDARY
        )
        self.index = index

    async def callback(self, ctx: miru.ViewContext) -> None:
        self.label = "💣"
        self.style = hikari.ButtonStyle.DANGER
        self.view.stop()

        await ctx.edit_response(
            embed=hikari.Embed(
                title="💣 Сапёр / Игра окончена",
                description=(
                    "Что-ж, кажется для вас это конец.\n"
                    "Может стоит попробовать ещё раз?"
                ),
                colour=hikari.colors.Color(0xffbe6f)
            ),
            components=self.view
        )


class MineView(miru.View):
    def __init__(self):
        super().__init__()

        self.mines = []
        self.total_bombs = 0
        self.cels_left = 0
        self.gen_mines()

    def gen_mines(self):
        self.mines.clear()
        self.total_bombs = 0

        for x in range(25):
            if random.randint(1, 6) == 6:
                button = BombButton(x)
                self.total_bombs += 1
            else:
                button = EmptyButton(x)

            self.mines.append(button)
            self.add_item(button)
            self.cels_left = 25 - self.total_bombs

    def count_bombs(self, index: int):
        pos_y, pos_x = divmod(index, 5)
        bomb_counter = 0

        for y_shift in range(-1, 2):
            if pos_y+y_shift < 0 or pos_y+y_shift > 4:
                continue

            for x_shift in range(-1, 2):
                if pos_x+x_shift < 0 or pos_x+x_shift > 4:
                    continue

                t_index = (pos_y+y_shift)*5 + (pos_x+x_shift)
                if isinstance(self.mines[t_index], BombButton):
                    bomb_counter += 1
        return bomb_counter


# определение команд
# ==================

@plugin.include
@arc.slash_command("mines", description="Начать игру сапёр.")
async def mines_handler(
    ctx: arc.GatewayContext,
    client: miru.Client = arc.inject()
) -> None:
    view = MineView()
    await ctx.respond(embed=get_game_status(view), components=view)
    client.start_view(view)


# Загрузчики и выгрузчики плагина
# ===============================

@arc.loader
def loader(client: arc.GatewayClient) -> None:
    client.add_plugin(plugin)

@arc.unloader
def unloader(client: arc.GatewayClient) -> None:
    client.remove_plugin(plugin)
