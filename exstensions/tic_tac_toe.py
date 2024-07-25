"""Крестики-нолики.

Одна из игр на двоих.
Есть поле 3 на 3, а также два игрока, которые играют в эту игру.
Задача каждого игрока, собрать 3 одинаковых элемента в ряд.
не важно, по вертикали, горизонтали или диагонали.
Выйграет первый, кто соберёт 3 крестика или нолика.

Есть два варианта игры:

- **Классический**: У вас есть полсе 3 на 3, а также два участника.
- **Бесконечный**: Похож на обычный, однако со временем выши старые
  ходы стирются и клетки освобождаются.

Предоставляет
-------------

- /ttt - Игра крестики-нолики.

Version: v0.4 (17)
Author: Milinuri Nirvalen
"""

import arc
import hikari
import miru

# Глобальные переменные
# =====================

plugin = arc.GatewayPlugin("ttt")

# Как будут выглядить крестик и нолик
# Возможно в будущем появится настройки для стиля элементов
_TTT_SIM = [
    "⭕", "❌"
]

# Все выйгрышные комбинации, при которых надо собрать 3 элемента в ряд
_WIN_PATTERNS = [
    (0, 1, 2), (3, 4, 5), (6, 7, 8),
    (0, 3, 6), (1, 4, 7), (2, 5, 8),
    (0, 4, 8), (2, 4, 6)
]


# Вспомогательные классы представления кнопок и игрового поля
# ===========================================================

class GameButton(miru.Button):
    """Описывает одну из клеток поля.

    По умолчанию она ничем не примечательная.
    Когда на неё нажимает игрок, она становится или кретиком или
    ноликом, в зависимости от игрока.

    Если выбран бесконечный режим, то со времнем данная клетка
    будет освобождена от пользователя.
    """

    def __init__(self, index: int, row: int):
        super().__init__(
            label="⬛",
            style=hikari.ButtonStyle.SECONDARY,
            row=row
        )
        self.index = index
        self.opener: hikari.User | None = None

    async def callback(self, ctx: miru.ViewContext) -> None:
        """Действия при нажатии на клетку.

        Для начала надо проверить, может ли данный пользователь нажать
        на кнопку.
        Если окажется что нет, то выводим сообщение с ошибкой.
        Дальше помечаем данную клетку как открытую.
        Когда не останется свободных клеток -игра заканчивается ничьей.
        Проверяем нет ли у нас победителя после открытия данной клетки.
        При наличии победителя, игра заканчивается его победой.
        Иначе же игра продолжается дальше и ход передаётся следующему
        игроку.

        :param ctx: Контекст при котором была нажата кнопка, кем, где..
        :type ctx: miru.ViewContext
        """
        if not self.view.validate_player(ctx):
            return await ctx.respond("АААААААААААААААААААААААААа, ты кто?")

        self.set_open(ctx)

        winner = self.view.is_game_over(self.index)
        if winner is not None:
            await ctx.edit_response(
                self.view.end_game_message(winner),
                components=self.view
            )
            self.view.stop()
            return

        if self.view.cell_left == 0:
            await ctx.edit_response(
                self.view.end_game_no_winner(),
                components=self.view
            )
            self.view.stop()
            return

        self.view.next_player()
        await ctx.edit_response(
            self.view.get_game_status(),
            components=self.view
        )


    def set_open(self, ctx: miru.ViewContext) -> None:
        """помечает клетку как кем-то открытую.

        Она окрасится в синий цвет и станет недоступна для
        использования.
        Также текст клетки изменится на кретик или нолик в
        зависимости от игрока.
        В конце отмечает кем была открыта клетка.

        :param ctx: Кто нажал на клетку.
        :type ctx: miru.ViewContext
        """
        self.style = hikari.ButtonStyle.PRIMARY
        self.disabled = True
        self.label = _TTT_SIM[self.view._cur]
        self.view.cell_left -= 1
        self.opener = ctx.user


    def before_close(self) -> None:
        """подготовливает клетку к высвобождению.

        Окрашивает его в нейтральный цвет, а также убирает владельца.
        """
        self.style = hikari.ButtonStyle.SECONDARY
        self.opener = None

    def set_close(self) -> None:
        """Помечает клетку как готовую к высвобождени."""
        self.view.cell_left += 1

    def after_close(self) -> None:
        """Действие после освобождения клетки.

        Позволяет снова игрокам использовать данную кнопку.
        """
        self.disabled = False
        self.label = "⬛"


    def set_winner(self) -> None:
        """Помечет клетку как победную, окрашивая её в зеленый цвет."""
        self.style = hikari.ButtonStyle.SUCCESS


class TicTacToeView(miru.View):
    """Предсталвение игрового поля крестики-нолики.

    У нас есть игровое поле 3 на 3 кнопки, а также два игрока,
    котоыре играют в эту игру.
    Задача игроков, собрать подходящий паттерн из одинаковых символов.
    Выиграет первый у кого это получится.

    Есть два режима игры, помимо классического также есть бесконечный.
    Когда со временем старые клетки очищаются.

    :param endless: Бесконечный режим игры по умолчанию выключен.
    :rtype endless: bool
    """

    def __init__(self, endless: bool = False):
        super().__init__()
        self.endless = endless

        self._board = []
        self._players = []
        self._cur = 0
        self._open_log = []
        self._cell_left = 9

        self._prepare_close: int | None = None
        self._next_close: int | None = None

        self.start_game()


    def start_game(self) -> None:
        """Начинает новую игру крестики-нолики.

        Очищает старые данные, формирует игровое поле.
        """
        # Очишаем старые данные
        self._board.clear()
        self._players.clear()
        self.cell_left = 9
        self._open_log.clear()

        # Формируем игровое поле
        for x in range(9):
            row = x // 3
            button = GameButton(x, row)
            self._board.append(button)
            self.add_item(button)

    def next_player(self) -> None:
        """Переключает курсок на следующего игрока."""
        self._cur = (self._cur + 1) % 2

    def validate_player(self, ctx: miru.ViewContext) -> bool:
        """Проверяет что игрок может играть в крестики-нолики.

        Если ещё никто не прикасался к полю, добавит первого
        пользователя в писок игроков, кто нажмёт на кнопку.
        Далее добавит следющего игрока в игру.
        Теперь по очереди выбор будет между двумя добавленными
        игроками.

        Чтобы никто другой не мог играть, кроме двух выбранных игроков.

        :param ctx: Контекст нажатия на кнопку (пользователь).
        :type ctx: miru.ViewContext
        :return: Может ли нажавший кнопку пользователь играть в игру.
        :rtype: bool
        """
        # Добавляем игроков, если их не хватает
        if len(self._players) < 2:
            if len(self._players) == 0:
                self._players.append(ctx.user)
            elif ctx.user != self._players[0]:
                self._players.append(ctx.user)
            else:
                return False
        if ctx.user not in self._players:
            return False
        if ctx.user != self._players[self._cur]:
            return False
        return True

    def is_game_over(self, index: int) -> hikari.User | None:
        """Проверяем, не закончилась ли игра.

        Данный метод вызывается при каждом нажатии кнопки.
        Он проверяет, нет ли ни у кого совпадающих элементов.
        Если кто-то уже осбрал комбинацию для победы, тогда мы вернём
        экземпляр этого учатсника игры.
        Иначе же игра продолжается.

        Если выбран бесконечный режим игры, то помимо этого будет
        вызван метод для регистрации нажатой кнопки.

        :param index: Порядковый номер нажатой кнопки (0-8).
        :type index: int
        :return: Экземпляр пользователя-победителя, иначе None.
        :rtype: hikari.User | None
        """
        if self.endless:
            self.register_open(index)

        # Тут будет говнокод
        for a_index, b_index, c_index in _WIN_PATTERNS:
            a_btn = self._board[a_index]
            b_btn = self._board[b_index]
            c_btn = self._board[c_index]

            if a_btn.opener is None:
                continue

            if b_btn.opener is None:
                continue

            if c_btn.opener is None:
                continue

            if (a_btn.opener == b_btn.opener and b_btn.opener == c_btn.opener):
                a_btn.set_winner()
                b_btn.set_winner()
                c_btn.set_winner()
                return a_btn.opener
        return None

    def register_open(self, index: int) -> None:
        """Регистрирует открытие всех клеток.

        Тольок для бесконечного режима игры.
        Запоминает порядок при котором открывались поля в игре.
        Чтобы постепенно их "забывать".
        Этот процесс происходит в 3 этапа:

        - Для начала клетка помечается как готовая освободиться.
        - Далее клетка теряет своего владельца и становится пустой.
        - Клетка полностью освобождается и её можно использовать.

        :param index: Порядковый номер клетки для записи (0-8).
        :type index: int
        """
        if self._next_close is not None:
            self._board[self._next_close].after_close()

        if self._prepare_close is not None:
            self._board[self._prepare_close].set_close()
            self._next_close = self._prepare_close

        self._open_log.append(index)
        if len(self._open_log) > 5:
            i = self._open_log.pop(0)
            self._board[i].before_close()
            self._prepare_close = i


    # Вспомогательные методы для сборки сообщений
    # ===========================================

    def get_players(self) -> str:
        if len(self._players) < 2:
            res = "Нажмите на поле, чтобы присоедениться к игре"
        else:
            res = ""
        for user in self._players:
            res += f"\n- {user.mention}"
        return res

    def get_game_status(self) -> hikari.Embed:
        return hikari.Embed(
            title=f"{_TTT_SIM[self._cur]} Крестики-нолики",
            description=(
                "Перед вами игровое поле.\n"
                "Вы сошлись здесь в дуэли, чтобы доказать свою силу.\n"
                "Мешать вам будет только ограниченное поле, да ваш противник."
            ),
            colour=hikari.colors.Color(0x00b0f4)
        ).add_field(
            name="Режим игры",
            value="Бесконечный" if self.endless else "Обычный.",
            inline=True
        ).add_field(
            name="Игроки", value=self.get_players(), inline=True
        ).add_field(
            name="Правила игры",
            value=(
            "- Нажмите на свободно поле, чтобы отметить его своим знаком.\n"
            "- Для победы соберите 3 знака  по диагонали/вертикали/горизонтали.\n"
            "- **Бесконечный режим**: Со временем клетки будут освобождаться."
            )
        )

    def end_game_no_winner(self) -> hikari.Embed:
        return hikari.Embed(
            title=f"{_TTT_SIM[self._cur]} Крестики-нолики / Ничья",
            description=(
                "Это была долгая битва.\n"
                "Однако поле закончилось.\n"
                "Теперь не получится выяснить кто выиграл."
            ),
            colour=hikari.colors.Color(0xffbe6f)
        ).add_field(
            name="Режим игры", value="Обычный", inline=True
        ).add_field(
            name="Игроки", value=self.get_players(), inline=True
        )

    def end_game_message(self, winner: hikari.User) -> hikari.Embed:
        return hikari.Embed(
            title=f"{_TTT_SIM[self._cur]} Крестики-нолики / Ничья",
            description=(
                "Это была долгая битва.\n"
                "И толко один мог выйти из неё победителем.\n\n"
                f"**Выйграл**: {winner.mention}"
            ),
            colour=hikari.colors.Color(0x8ff0a4)

        ).add_field(
            name="Режим игры",
            value="Бесконечный" if self.endless else "Обычный.",
            inline=True
        ).add_field(
            name="Игроки", value=self.get_players(), inline=True
        )


# определение команд
# ==================

@plugin.include
@arc.slash_command("ttt", description="Начать игру крестики-нолики.")
async def nya_handler(
    ctx: arc.GatewayContext,
    endless: arc.Option[bool, arc.BoolParams("Бесконечная ли игр (нет)")
    ] = False,
    client: miru.Client = arc.inject()
) -> None:
    """Начинает новую игру крестики-нолики.

    Для того чтобы двум игрокам начать играть, достаточно нажать на
    поле.
    Бот сам запомнит первых двух участников игры, чтобы никто другой
    не мог помешать их игре.
    """
    view = TicTacToeView(endless=endless)
    await ctx.respond(view.get_game_status(), components=view)
    client.start_view(view)


# Загрузчики и выгрузчики плагина
# ===============================

@arc.loader
def loader(client: arc.GatewayClient) -> None:
    """Производит загрузку плагина."""
    client.add_plugin(plugin)

@arc.unloader
def unloader(client: arc.GatewayClient) -> None:
    """Производит выгрузку плагина."""
    client.remove_plugin(plugin)
