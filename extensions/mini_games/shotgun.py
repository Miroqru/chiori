"""Русская рулетка.

Игра для весёлой компании, которой нечем заняться в свободное время.

Предоставляет
-------------

- /shot - Начать игру в рулетку.

Version: v1.0 (1)
Author: Milinuri Nirvalen
"""

from random import randint

import arc
import hikari
import miru

plugin = arc.GatewayPlugin("Shotgun")


class ShotButton(miru.Button):
    """Кнопка для рулетки."""

    def __init__(self) -> None:
        super().__init__(label="Выстрелить", emoji="🔫")
        self.view: ShotView

    async def callback(self, ctx: miru.ViewContext) -> None:
        """Действие при нажатии на кнопку."""
        res = self.view.shot(ctx.user)
        if res:
            await ctx.edit_response(self.view.end_message(), components=None)
            self.view.stop()
        else:
            await ctx.edit_response(self.view.status(), components=self.view)


class ShotView(miru.View):
    """Игра рулетка."""

    def __init__(self) -> None:
        super().__init__()
        self.cur = 0
        self.end = 0
        self.players: list[hikari.User] = []
        self.results: dict[int, int] = {}
        self.looser: None | hikari.User = None

        self.new_game()
        self.add_item(ShotButton())

    def new_game(self) -> None:
        """Начинает новую игру."""
        self.cur = 0
        self.end = randint(1, 8)
        self.players = []
        self.results = {}
        self.looser = None

    def list_players(self) -> str:
        """Список игроков."""
        res = ""
        if self.looser is not None:
            res += f"**Проигравший**: {self.looser.mention}\n"
        if len(self.players) == 0:
            res += "пока никто не стрелял."

        for player in sorted(self.players, key=lambda p: self.results[p.id]):
            if self.looser is not None and self.looser == player:
                name = f"~~{player.display_name}~~"
            else:
                name = str(player.display_name)

            res += f"- {name}: {self.results[player.id]}\n"

        return res

    def status(self) -> hikari.Embed:
        """Собирает статус игры."""
        return hikari.Embed(
            title="🔫 Рулетка",
            description=(
                f"{self.list_players()}\n🔫 Стреляли: {self.cur}/8 раз."
            ),
            color=0x000CCFF,
        )

    def end_message(self) -> hikari.Embed:
        """Собирает сообщение о завершении игры."""
        return hikari.Embed(
            title="🔫 Рулетка / Игра завершена",
            description=(
                f"{self.list_players()}\n🔫 Стреляли: {self.cur}/8 раз."
            ),
            color=0xFF33CC,
        )

    def shot(self, user: hikari.User) -> bool:
        """Выстреливает из револьвера.

        Возвращает флаг проигрыша.
        """
        self.cur += 1
        if user not in self.players:
            self.players.append(user)
            self.results[user.id] = 0
        self.results[user.id] += 1

        if self.cur >= self.end:
            self.looser = user
            return True
        return False


# определение команд
# ==================


@plugin.include
@arc.slash_command("shot", description="Начать новую игру в рулетку.")
async def nya_handler(
    ctx: arc.GatewayContext, client: miru.Client = arc.inject()
) -> None:
    """Игра рулетка.

    Игроки стреляются до тех пор. пока не произойдёт выстрел.
    Игра для двух и более игроков.
    """
    view = ShotView()
    await ctx.respond(view.status(), components=view)
    client.start_view(view)


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
