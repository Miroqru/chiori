"""Игра Угадай число.

Бот загажывает некоторое число от 1 до 1000.
Задача пользователя - верно отгадать число.

Предоставляет
-------------

/guessnum - Игра угадай число

Version: 0.1
Author: Milinuri Nirvalen
"""

from random import randint

import arc
import hikari
import miru

# Глобальные переменные
# =====================

plugin = arc.GatewayPlugin("Guess number")


# Вспомогательный класс определения игрового компонента
# =====================================================

class GuessModal(miru.Modal):
    guess = miru.TextInput(
        label="Некоторое число от 1 до 1000",
        min_length=1,
        max_length=3
    )

    def __init__(self, view: "GuessView"):
        super().__init__(title="Какое же число?")
        self.view = view

    async def callback(self, ctx: miru.ModalContext) -> None:
        if self.guess.value.isdigit():
            guess = int(self.guess.value)
        else:
            await ctx.respond(
                "Вам бы следовало написать тут число от 1 до 1000",
                delete_after=10
            )

        if guess > 1000 or guess < 1:
            return await ctx.respond(
                "Вам бы следовало написать тут число от 1 до 1000",
                delete_after=10
            )

        self.view._user_guess = guess
        game_over = self.view.is_game_over()
        if game_over:
            await ctx.edit_response(
                embed=self.view.end_game()
            )
            self.view.stop()
        else:
            await ctx.edit_response(
                embed=self.view.game_status()
            )


class GuessView(miru.View):
    def __init__(self):
        super().__init__()
        self._guess = None
        self._user_guess = None

        self.new_game()

    @miru.button("Загадать")
    async def main_button(self, ctx: miru.ViewContext, button: miru.Button) -> None:
        modal = GuessModal(self)
        await ctx.respond_with_modal(modal)

    def new_game(self) -> None:
        self._guess = randint(1, 1000)
        self._user_guess = None

    def is_game_over(self) -> None:
        return self._user_guess == self._guess

    def guess_status(self) -> str:
        if self._user_guess is None:
            return "Вы ещё не делали предположений."
        elif self._user_guess < self._guess:
            return f"Загаданное вами число **{self._user_guess}** меньше моего"
        elif self._user_guess > self._guess:
            return f"Загаданное вами число **{self._user_guess}** больше моего"
        else:
            return f"Я загадывала **{self._user_guess}**"

    def game_status(self) -> hikari.Embed:
        return hikari.Embed(
            title="Угадай число",
            description="Я загадала некоторое число от 1 до 1000."
        ).add_field("Ваше предположение", self.guess_status())

    def end_game(self) -> hikari.Embed:
        return hikari.Embed(
            title="Угадай число / игра закончена",
            description="Вы успешно отгадали число."
        ).add_field("Ваше прдположение", self.guess_status())


# определение команд
# ==================

@plugin.include
@arc.slash_command("guessnum", description="Начать игру Угадай число.")
async def nya_handler(
    ctx: arc.GatewayContext,
    client: miru.Client = arc.inject()
) -> None:
    view = GuessView()
    await ctx.respond(embed=view.game_status(), components=view)
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
