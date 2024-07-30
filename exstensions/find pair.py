"""Ня.

да, это маленькое расширение нужно чтобы някать ваших участников,
не больше.

Предоставляет
-------------

- /pair - Начтаь игру найди пару

Version: v0.1
Author: Milinuri Nirvalen
"""

from random import shuffle

import arc
import hikari
import miru

plugin = arc.GatewayPlugin("Find pair")

_PAIRS = [
    "🍌", "🍓", "🍇", "🍞", "🥐", "🍫", "🍦","☕",
]

class GameButton(miru.Button):
    def __init__(self, pair: int, row: int) -> None:
        super().__init__(
            label="⬛",
            style=hikari.ButtonStyle.SECONDARY,
            row=row
        )
        self.pair = pair

    async def callback(self, ctx: miru.ViewContext):
        self.view.open_pair(self)
        game_over = self.view.is_game_over()
        if game_over:
            await ctx.edit_response(
                embed=self.view.end_game_message(),
                components=self.view
            )
            self.view.stop()
        else:
            await ctx.edit_response(
                embed=self.view.game_status(),
                components=self.view
            )

    def set_open(self):
        self.disabled = True
        self.style = hikari.ButtonStyle.PRIMARY
        self.label = _PAIRS[self.pair]

    def set_close(self):
        self.disabled = False
        self.style = hikari.ButtonStyle.SECONDARY
        self.label = "⬛"

    def set_completed(self):
        self.disabled = True
        self.style = hikari.ButtonStyle.SUCCESS
        self.label = _PAIRS[self.pair]


class PairView(miru.View):
    def __init__(self):
        super().__init__()

        self._board = []
        self.first_open: GameButton | None = None
        self.secons_open: GameButton | None = None
        self.pair_left = 0

        self.new_game()

    def new_game(self) -> None:
        self._board.clear()
        self.first_open = None
        self.secons_open = None
        self.pair_left = 8

        for x in range(8):
            self._board.append(x)
            self._board.append(x)
        shuffle(self._board)

        for i, pair in enumerate(self._board):
            row = i // 4
            self.add_item(GameButton(pair, row=row))

    def open_pair(self, button: GameButton) -> None:
        if self.first_open is not None and self.secons_open is not None:
            self.first_open.set_close()
            self.first_open = None

            self.secons_open.set_close()
            self.secons_open = None

        if self.first_open is None:
            self.first_open = button
            button.set_open()

        elif self.secons_open is None:
            if self.first_open.pair == button.pair:
                self.first_open.set_completed()
                self.first_open = None
                button.set_completed()
                self.pair_left -= 1
            else:
                button.set_open()
                self.secons_open = button

    def is_game_over(self) -> bool:
        return self.pair_left <= 0

    def end_game_message(self) -> hikari.Embed:
        return hikari.Embed(
            title="☕ Найди пару / игра окончена",
            description="Поздравляем, вы успешо нашли все пары",
            color=hikari.colors.Color(0x8ff0a4)
        )

    def game_status(self) -> hikari.Embed:
        return hikari.Embed(
            title="☕ Найди пару",
            description=(
                "Ваша заача найти пару для всех вкусностей.\n"
                "- Нажмите на поле, чтобы открыть его.\n"
                "- Два одинаковых поля образуют пару.\n"
                "- Не одинаковые поля будут закрываться."
            ),
            color=hikari.colors.Color(0x00ccff)
        ).add_field("Пар осталось", str(self.pair_left))


# определение команд
# ==================

@plugin.include
@arc.slash_command("pair", description="Игра найди пару.")
async def nya_handler(
    ctx: arc.GatewayContext,
    client: miru.Client = arc.inject()
) -> None:
    view = PairView()
    await ctx.respond(view.game_status(), components=view)
    client.start_view(view)


# Загрузчики и выгрузчики плагина
# ===============================

@arc.loader
def loader(client: arc.GatewayClient) -> None:
    client.add_plugin(plugin)

@arc.unloader
def unloader(client: arc.GatewayClient) -> None:
    client.remove_plugin(plugin)
