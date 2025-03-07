"""Игра камень-ножницы-бумага.

Предоставляет
-------------

- /rps  - Игра Камень Ножницы бумага

Version: v0.3.1 (9)
Author: Milinuri Nirvalen
"""

from enum import IntEnum
from typing import NamedTuple

import arc
import hikari
import miru

plugin = arc.GatewayPlugin("Rps")

# Использованные в игре символы
_RPS_SIM = [
    "🪨", "🧻", "✂️"
]

# Предсталвения кнопок
# ====================

class GameObject(IntEnum):
    """Представляет все игровые объекты.

    - Камень затупляет ножницы.
    - Бумага оборачивает камень.
    - Ножницы режут бумагу.
    """

    ROCK = 0
    PAPER = 1
    SCISSORS = 2

    def __str__(self) -> str:
        return _RPS_SIM[self.value]

class Player(NamedTuple):
    """Экземпляр игрока.

    Представляет каждого игрока, сделавшего выбор своего элемента.
    СОхраняет экземпляр пользователя и выбранный им элемент.

    :param user: Экземпляр пользователя, сделавшего выбор.
    :type user: hikari.User
    :param choice: Выбранный игроков элемент.
    :type choice: GameObject
    """

    user: hikari.User
    choice: GameObject

    def __str__(self) -> str:
        return f"{self.choice} {self.user.mention}"


class ContinueButton(miru.Button):
    """Кнопка завершения игры.

    Становится доступна после того, как к игре присоеденится минимум
    2 участника.
    При нажатии на кнопку подводятся результаты игры и на основе этого
    отправляется сообщение о победе или поражении.
    """

    def __init__(self):
        super().__init__(
            label="Играть",
            style=hikari.ButtonStyle.SUCCESS,
            disabled=True
        )

    async def callback(self, ctx: miru.ViewContext) -> None:
        """Действия при нажатии на кнопку.

        Как только вы нажимаете на кнопку продолжения игры.
        Идёт подсчёт результатов и выяснения победителя.
        Если победитель есть, отправляем победное сообщение, если же
        победителя в данном раунден нету, отправляем сообщение о
        ничьей.

        :param ctx: Контекст нажатия на кнопку. Кто, когда, где.
        :type ctx: miru.ViewContext
        """
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

    def set_active(self) -> None:
        """Делает кнопку доступной для нажатия."""
        self.disabled = False

class GameButton(miru.Button):
    """Кнопка с элементом.

    Всего их три: камень, Ножницы, Бумага.
    При нажатии на такую кнопку, вы будете доабвелны в список игроков
    с выбранным элементом в зависимости от типа кнопки.

    После этого перевыбрать элемент будет нельзя.

    :param game_object: Какой элемент будет предсталвять кнопка.
    :type game_object: GameObject
    """

    def __init__(self, game_object: GameObject):
        super().__init__(
            label=_RPS_SIM[game_object.value]
        )
        self.game_object = game_object

    async def callback(self, ctx: miru.ViewContext) -> None:
        """Описывает действие при нажатии на кнопку.

        как только вы нажимаете на кнопку с соотвутствующим элементом,
        вас добавляют в список игроков с выбранным элементом.

        _extended_summary_

        :param ctx: _description_
        :type ctx: miru.ViewContext
        :return: _description_
        :rtype: _type_
        """
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
    """Класс предствления для игры Камень Ножницы Бумага.

    Реализует все необхоимые методы для игры.
    А также все необхоидмые кнопки.
    """

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
        """Проверяет, есть ли данный пользователь в списоке игроков.

        :param user: Экземпляр пользователя для проверки.
        :type user: hikari.User
        :return: Есть ли данный пользователь в списке игроков.
        :rtype: bool
        """
        for player in self._players:
            if user == player.user:
                return True
        return False

    def add_player(self, user: hikari.User, choice: GameObject) -> bool:
        """Добавляет игрока в список игроков.

        Возвращет статус добавления нового игрока.
        True - Если игрок добавлен в список.

        Попать в список могут несколько не повторяющихся игроков.
        Данная функциия следит, чтобы в список игроков не попали
        дубликаты, а также чтобы список игроков не выходил за заданные
        пределы.

        :param user: Экземпляр пользователя, которого нужно добавить.
        :type user: hikari.User
        :param choice: Какой элемент выбрал польщователь.
        :type choice: GameObject
        :return: Получилось ли доавбить переданного пользователя.
        :rtype: bool
        """
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
        """получает победителя среди двух игроков.

        правила игры думаю вы знаете.

        - Бумага заворачивает камень.
        - Камень затупляет ножницы.
        - Ножницы разрезают бумагу.
        - Одинаковые элементы приводят к ничьей.

        :param a: Пеовый игрок.
        :type a: Player
        :param b: Второй игрок.
        :type b: Player
        :return: Победивший игрок или None, если победителей нет.
        :rtype: Player | None
        """
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
        """Заканчивает игру и возвращает победителя.

        В будущем даный метод может быть расширен, чтобы подводить
        итоге игры с несколькими игроками.

        :return: Победивший игрок или None, если победителей нет.
        :rtype: Player | None
        """
        return self.get_winner(self._players[0], self._players[1])


    def get_players(self, hide: bool = True) -> str:
        """Получает строку со списком игроков.

        Испольузется чтобы отобразить всех игроков, принимающих участие
        в игре.
        Отправляет список с упоминнаниями игроков, а также выбранные
        ими элементы, если это требуется.

        :param hide: Скрывать выбранные элементы (да).
        :type hide: bool | None
        :return: Строковый список игроков.
        :rtype: str
        """
        res = ""
        for p in self._players:
            if hide:
                res += f"\n- {p.user.mention}"
            else:
                res += f"\n{p}"
        return res

    def get_game_status(self) -> hikari.Embed:
        """Возврвщает сообщение статуса игры.

        Данное сообщение будет изменяться каждый раз, как кто-то ножмёт
        на кнопку.
        Отображает список текущих игроков.

        :return: Сообщение с текущим статусом игры.
        :rtype: hikari.Embed
        """
        return hikari.Embed(
            title=f"{_RPS_SIM[1]} Камень ножницы бумага",
            description=self.get_players(),
            color=hikari.colors.Color(0xdc8add)
        )

    def get_game_result(self, winner: Player) -> hikari.Embed:
        """Сообщение с результатами игры.

        Отправялется как только становится известен победитель.
        Отображает игроков, выбранные ими элементы, а также самого
        победителя.

        :param winner: Кто победил в данной игре.
        :type winner: Player
        :return: Сообщение с результатами игры.
        :rtype: hikari.Embed
        """
        return hikari.Embed(
            title=f"{winner.choice} Камень ножницы бумага / Игра окончена",
            description=f"{self._players[0]} x {self._players[1]}",
            color=hikari.colors.Color(0x8ff0a4)
        ).add_field("Победитель", str(winner), inline=True)

    def game_end_no_winner(self) -> hikari.Embed:
        """Сообщение что игра закончилось в ничью.

        Игра может закончиться в ничью, если игроки выбрали одинаковые
        элементы.
        Отображается какие элементы выбрали игроки.

        :return: Сообщение с результатами игры.
        :rtype: hikari.Embed
        """
        return hikari.Embed(
            title=f"{self._players[0].choice} Камень ножницы бумага / Ничья",
            description=(
                "Игроки выбрали одинаковые элементы, игра окончилась ничьей\n"
                f"{self._players[0]} x {self._players[1]}"
            ),
            color=hikari.colors.Color(0xffbe6f)
        )

    def no_valid_player_message(self) -> hikari.Embed:
        """Отправялет сообгение если кто-то потосронний нажал на кнопку.

        Даннео сообщение появляется, если пользователь хочет нажать на
        кнопку ещё раз.
        Также может возникать, если кто-то хочет войти в переполненное
        игровое лобби.

        :return: Сообщение о некорректном действии.
        :rtype: hikari.Embed
        """
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
    """Начинает новую игру в Камень Ножницы Бумага.

    Сразу отображает ещё пустое сообщение со статусом.
    А также кнопки для выбора своей стороны.
    Кнопка продолжить игру пока буедт недоступна, пока не будет
    достаточно игроков.
    """
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
