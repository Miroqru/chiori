"""Игра камень-ножницы-бумага.

Предоставляет
-------------

- /rps  - Игра Камень Ножницы бумага

Version: v0.1 (3)
Author: Milinuri Nirvalen
"""

from typing import NamedTuple
from enum import IntEnum

import arc
import hikari
import miru

plugin = arc.GatewayPlugin("Rps")

_RPS_SIM = [
    "🪨", "🧻", "✂️"
]

# Предсталвения кнопок
# ====================

class GameObject(IntEnum):
    ROCK = 0
    PAPER = 1
    SCISSORS = 2

    def __str__(self) -> str:
        return _RPS_SIM[self.value]

class Player(NamedTuple):
    user: hikari.User
    choice: GameObject

    def __str__(self) -> str:
        return f"{self.choice} {self.user.mention}"


class ContinueButton(miru.Button):
    def __init__(self):
        super().__init__(
            label="Играть",
            style=hikari.ButtonStyle.SUCCESS,
            disabled=True
        )

    async def callback(self, ctx: miru.ViewContext):
        winner = self.view.end_game()
        if winner is None:
            await ctx.edit_response(
                self.view.game_end_no_winner(),
                components=None
            )
        else:
            await ctx.edit_response(
                self.view.get_game_result(winner),
                components=None
            )

        self.view.stop()

    def set_active(self):
        self.disabled = False

class GameButton(miru.Button):
    def __init__(self, game_object: GameObject):
        super().__init__(
            label=_RPS_SIM[game_object.value]
        )
        self.game_object = game_object

    async def callback(self, ctx: miru.ViewContext):
        if not self.view.add_player(ctx.user, self.game_object):
            return await ctx.respond(
                self.view.no_valid_player_message(),
                delete_after=10
            )
        await ctx.edit_response(
            self.view.get_game_status(),
            components=self.view
        )


class RockPaperScissorsView(miru.View):
    def __init__(self):
        super().__init__()
        self._players: list[Player] = []
        self._ready_to_game = False
        self.limit_players = 2
        self.game_result = None

        self.add_item(GameButton(GameObject.ROCK))
        self.add_item(GameButton(GameObject.PAPER))
        self.add_item(GameButton(GameObject.SCISSORS))

        self.continue_button = ContinueButton()
        self.add_item(self.continue_button)


    def check_in_list(self, user: hikari.User) -> bool:
        for player in self._players:
            if user == player.user:
                return True
        return False

    def add_player(self, user: hikari.User, choice: GameObject) -> bool:
        if len(self._players) == 0:
            self._players.append(Player(user, choice))
            return True
        else:
            if len(self._players) >= self.limit_players:
                return False

            if self.check_in_list(user):
                return False

            self._players.append(Player(user, choice))

            if not self._ready_to_game:
                if len(self._players) >= 2:
                    self._ready_to_game = True
                    self.continue_button.set_active()

            return True


    def get_winner(self, a: Player, b: Player) -> Player | None:
        if a.choice == b.choice:
            return None

        if a.choice == GameObject.ROCK and b.choice == GameObject.PAPER:
            return b
        if a.choice == GameObject.ROCK and b.choice == GameObject.SCISSORS:
            return a

        if a.choice == GameObject.PAPER and b.choice == GameObject.ROCK:
            return a
        if a.choice == GameObject.PAPER and b.choice == GameObject.SCISSORS:
            return b

        if a.choice == GameObject.SCISSORS and b.choice == GameObject.ROCK:
            return b
        if a.choice == GameObject.SCISSORS and b.choice == GameObject.PAPER:
            return a

    def end_game(self) -> Player | None:
        return self.get_winner(self._players[0], self._players[1])


    def get_players(self, hide: bool = True) -> str:
        res = ""
        for p in self._players:
            if hide:
                res += f"\n- {p.user.mention}"
            else:
                res += f"\n{p}"
        return res

    def get_game_status(self) -> hikari.Embed:
        return hikari.Embed(
            title="RPS",
            description=self.get_players(),
            colour=hikari.colors.Color(0xdc8add)
        )

    def get_game_result(self, winner: Player) -> hikari.Embed:
        return hikari.Embed(
            title=f"{winner.choice} Камень ножницы бумага / Игра окончена",
            description=f"{self._players[0]} x {self._players[1]}",
            color=hikari.colors.Color(0x8ff0a4)
        ).add_field("Победитель", str(winner), inline=True)

    def game_end_no_winner(self) -> hikari.Embed:
        return hikari.Embed(
            title=f"{self._players[0].choice} Камень ножницы бумага / Ничья",
            description=f"{self._players[0]} x {self._players[1]}",
            color=hikari.colors.Color(0xffbe6f)
        )

    def no_valid_player_message(self) -> hikari.Embed:
        return hikari.Embed(
            title=f"{_RPS_SIM[1]} Каень ножницы бумага / Ась?",
            description=(
                "Вероятно вы уже сделаи свой выбор.\n"
                "Или лобби данной игры переполнено."
            ),
            colour=hikari.colors.Color(0xdc8add)
        )


# определение команд
# ==================

@plugin.include
@arc.slash_command("rps", description="Игра Камень Ножницы Бумага.")
async def nya_handler(
    ctx: arc.GatewayContext,
    client: miru.Client = arc.inject()
) -> None:
    view = RockPaperScissorsView()
    await ctx.respond(view.get_game_status(), components=view)
    client.start_view(view)


# Загрузчики и выгрузчики плагина
# ===============================

@arc.loader
def loader(client: arc.GatewayClient) -> None:
    """Загружает плагин в ядро."""
    client.add_plugin(plugin)

@arc.unloader
def unloader(client: arc.GatewayClient) -> None:
    """Выгружает плагин из ядра."""
    client.remove_plugin(plugin)
