"""Игра Угадай число.

Бот загадывает некоторое число от 1 до 1000.
Задача пользователя - верно отгадать число.

Предоставляет
-------------

 - /guessnum - Начать игру Угадай число.

Version: 0.2.1 (3)
Author: Milinuri Nirvalen
"""

from random import randint

import arc
import hikari
import miru

plugin = arc.GatewayPlugin("Guess number")
_MAX_GUESS = 1000

# Вспомогательный класс определения игрового компонента
# =====================================================


class GuessModal(miru.Modal):
    """Модальное окно для игры угадай число.

    Позволяет пользователю ввести свою догадку.
    """

    guess = miru.TextInput(
        label=f"Некоторое число от 1 до {_MAX_GUESS}",
        min_length=1,
        max_length=3,
    )

    def __init__(self, view: "GuessView") -> None:
        super().__init__(title="Какое же число?")
        self.view: GuessView = view

    async def callback(self, ctx: miru.ModalContext) -> None:
        """Действие при вводе догадки."""
        if self.guess.value is not None and self.guess.value.isdigit():
            guess = int(self.guess.value)
        else:
            await ctx.respond(
                f"Вам бы следовало написать тут число от 1 до {_MAX_GUESS}",
                flags=hikari.MessageFlag.EPHEMERAL,
            )
            return None

        if guess > _MAX_GUESS or guess < 1:
            await ctx.respond(
                f"Вам бы следовало написать тут число от 1 до {_MAX_GUESS}",
                flags=hikari.MessageFlag.EPHEMERAL,
            )
            return

        self.view.user_guess = guess
        game_over = self.view.is_game_over()
        if game_over:
            await ctx.edit_response(embed=self.view.end_game())
            self.view.stop()
        else:
            await ctx.edit_response(embed=self.view.game_status())


class GuessView(miru.View):
    """Игра угадай числа."""

    def __init__(self) -> None:
        super().__init__()
        self._guess: int = 0
        self.user_guess: int = 0
        self.new_game()

    @miru.button("Загадать")
    async def main_button(
        self, ctx: miru.ViewContext, button: miru.Button
    ) -> None:
        """Открывает модальное окно для ввода предполагаемого числа."""
        modal = GuessModal(self)
        await ctx.respond_with_modal(modal)

    def new_game(self) -> None:
        """Начинает новую игру."""
        self._guess = randint(1, 1000)
        self.user_guess = 0

    def is_game_over(self) -> bool:
        """проверяет не завершилась ил игра."""
        return self.user_guess == self._guess

    def guess_status(self) -> str:
        """Сообщение отношения догадки.

        Насколько пользователь близок к загаданному числу.
        """
        if self.user_guess < self._guess:
            return f"Загаданное вами число **{self.user_guess}** меньше моего"
        elif self.user_guess > self._guess:
            return f"Загаданное вами число **{self.user_guess}** больше моего"
        else:
            return f"Я загадывала **{self.user_guess}**"

    def game_status(self) -> hikari.Embed:
        """Сообщение статуса игры."""
        return hikari.Embed(
            title="Угадай число",
            description="Я загадала некоторое число от 1 до 1000.",
        ).add_field("Ваше предположение", self.guess_status())

    def end_game(self) -> hikari.Embed:
        """Сообщение о завершении игры."""
        return hikari.Embed(
            title="Угадай число / игра закончена",
            description="Вы успешно отгадали число.",
        ).add_field("Ваше предположение", self.guess_status())


# определение команд
# ==================


@plugin.include
@arc.slash_command("guessnum", description="Начать игру Угадай число.")
async def guess_number(
    ctx: arc.GatewayContext, client: miru.Client = arc.inject()
) -> None:
    """Игра угадай число.

    Бот загадывает числа, а задача пользователя его отгадать.
    """
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
