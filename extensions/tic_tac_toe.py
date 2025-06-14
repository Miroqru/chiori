"""Крестики-нолики.

Одна из игр на двоих.
Есть поле 3 на 3, а также два игрока, которые играют в эту игру.
Задача каждого игрока, собрать 3 одинаковых элемента в ряд.
не важно, по вертикали, горизонтали или диагонали.
Выигрывает первый, кто соберёт 3 крестика или нолика.

Есть два варианта игры:

- **Классический**: У вас есть после 3 на 3, а также два участника.
- **Бесконечный**: Похож на обычный, однако со временем выши старые
  ходы стирается и клетки освобождаются.

Предоставляет
-------------

- /ttt - Игра крестики-нолики.

Version: v0.5.2 (20)
Author: Milinuri Nirvalen
"""

import arc
import hikari
import miru

# Глобальные переменные
# =====================

plugin = arc.GatewayPlugin("tic_tac_toe")

# Как будут выглядеть крестик и нолик
# Возможно в будущем появится настройки для стиля элементов
_TTT_SIM = ["⭕", "❌"]

# Все выигрышные комбинации, при которых надо собрать 3 элемента в ряд
_WIN_PATTERNS = [
    (0, 1, 2),
    (3, 4, 5),
    (6, 7, 8),
    (0, 3, 6),
    (1, 4, 7),
    (2, 5, 8),
    (0, 4, 8),
    (2, 4, 6),
]

_GAME_RULES = (
    "- Нажмите на свободно поле, чтобы отметить его своим.\n"
    "- Для победы соберите 3 знака по диагонали/вертикали/горизонтали.\n"
    "- **Бесконечный режим**: Со временем клетки будут освобождаться."
)

# Вспомогательные классы представления кнопок и игрового поля
# ===========================================================


class GameButton(miru.Button):
    """Описывает одну из клеток поля.

    По умолчанию она ничем не примечательная.
    Когда на неё нажимает игрок, она становится или крестиком или
    ноликом, в зависимости от игрока.

    Если выбран бесконечный режим, то со временем данная клетка
    будет освобождена от пользователя.
    """

    def __init__(self, index: int, row: int) -> None:
        super().__init__(
            label="⬛", style=hikari.ButtonStyle.SECONDARY, row=row
        )
        self.index = index
        self.opener: hikari.User | None = None
        self.view: TicTacToeView

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
        """
        if not self.view.validate_player(ctx):
            # Удаляем сообщение через 10 секунд, чтобы не засорять чат
            await ctx.respond(
                self.view.no_valid_player_message(), delete_after=10
            )
            return

        self.set_open(ctx)

        # Сначала идёт проверка выигрышных комбинаций
        # А уже после проверка на отсутствие слотов
        # Дабы решить проблему когда вы выигрываете последним ходом
        winner = self.view.is_game_over(self.index)
        if winner is not None:
            await ctx.edit_response(
                self.view.end_game_message(winner), components=self.view
            )
            self.view.stop()
            return

        if self.view.cell_left == 0:
            await ctx.edit_response(
                self.view.end_game_no_winner(), components=self.view
            )
            self.view.stop()
            return

        self.view.next_player()
        await ctx.edit_response(self.view.game_status(), components=self.view)

    def set_open(self, ctx: miru.ViewContext) -> None:
        """помечает клетку как кем-то открытую.

        Она окрасится в синий цвет и станет недоступна для
        использования.
        Также текст клетки изменится на крестик или нолик в
        зависимости от игрока.
        В конце отмечает кем была открыта клетка.
        """
        self.style = hikari.ButtonStyle.PRIMARY
        self.disabled = True
        self.label = _TTT_SIM[self.view._cur]
        self.view.cell_left -= 1
        self.opener = ctx.user

    def before_close(self) -> None:
        """Подготавливает клетку к высвобождению.

        Окрашивает его в нейтральный цвет, а также убирает владельца.
        """
        self.style = hikari.ButtonStyle.SECONDARY
        self.opener = None

    def set_close(self) -> None:
        """Помечает клетку как готовую к освобождению."""
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
    """Представление игрового поля крестики-нолики.

    У нас есть игровое поле 3 на 3 кнопки, а также два игрока,
    которые играют в эту игру.
    Задача игроков, собрать подходящий паттерн из одинаковых символов.
    Выиграет первый у кого это получится.

    Есть два режима игры, помимо классического также есть бесконечный.
    Когда со временем старые клетки очищаются.
    """

    def __init__(self, endless: bool = False) -> None:
        super().__init__()
        self.endless = endless

        self._board: list[int] = []
        self._players: list[hikari.User] = []
        self._cur = 0
        self._open_log: list[int] = []
        self._cell_left = 9

        # Для бесконечных крестиков-ноликов
        self._prepare_close: int | None = None
        self._next_close: int | None = None

        self.start_game()

    def start_game(self) -> None:
        """Начинает новую игру крестики-нолики.

        Очищает старые данные, формирует игровое поле.
        """
        # Очищаем старые данные
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
        """Переключает курсор на следующего игрока."""
        self._cur = (self._cur + 1) % 2

    def validate_player(self, ctx: miru.ViewContext) -> bool:
        """Проверяет что игрок может играть в крестики-нолики.

        Если ещё никто не прикасался к полю, добавит первого
        пользователя в список игроков, кто нажмёт на кнопку.
        Далее добавит следующего игрока в игру.
        Теперь по очереди выбор будет между двумя добавленными
        игроками.

        Чтобы никто другой не мог играть, кроме двух выбранных игроков.

        :param ctx: Контекст нажатия на кнопку (пользователь).
        :type ctx: miru.ViewContext
        :return: Может ли нажавший кнопку пользователь играть в игру.
        :rtype: bool
        """
        # Добавляем игроков, если их не хватает
        if len(self._players) < 2:  # noqa: PLR2004
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

    def is_game_over(self, cell_index: int) -> hikari.User | None:
        """Проверяем, не закончилась ли игра.

        Данный метод вызывается при каждом нажатии кнопки.
        Он проверяет, нет ли ни у кого совпадающих элементов.
        Если кто-то уже собрал комбинацию для победы, тогда мы вернём
        экземпляр этого участника игры.
        Иначе же игра продолжается.

        Если выбран бесконечный режим игры, то помимо этого будет
        вызван метод для регистрации нажатой кнопки.
        """
        if self.endless:
            self.register_open(cell_index)

        # Тут будет всё очень печально
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

            if a_btn.opener == b_btn.opener and b_btn.opener == c_btn.opener:
                a_btn.set_winner()
                b_btn.set_winner()
                c_btn.set_winner()
                return a_btn.opener
        return None

    def register_open(self, cell_index: int) -> None:
        """Регистрирует открытие всех клеток.

        Только для бесконечного режима игры.
        Запоминает порядок при котором открывались поля в игре.
        Чтобы постепенно их "забывать".
        Этот процесс происходит в 3 этапа:

        - Для начала клетка помечается как готовая освободиться.
        - Далее клетка теряет своего владельца и становится пустой.
        - Клетка полностью освобождается и её можно использовать.
        """
        if self._next_close is not None:
            self._board[self._next_close].after_close()

        if self._prepare_close is not None:
            self._board[self._prepare_close].set_close()
            self._next_close = self._prepare_close

        self._open_log.append(cell_index)
        if len(self._open_log) > 5:  # noqa: PLR2004
            i = self._open_log.pop(0)
            self._board[i].before_close()
            self._prepare_close = i

    # Вспомогательные методы для сборки сообщений
    # ===========================================

    def get_players(self) -> str:
        """Возвращает строковый список игроков.

        Используется чтобы отобразить список всех кто играет в игру.
        Это лучше, чем гадать, где в данный момент играет.
        Если игроков недостаточно, выводит сообщение как можно
        присоединиться к игре.
        """
        if len(self._players) < 2:  # noqa: PLR2004
            res = "Нажмите на поле, чтобы присоединиться к игре"
        else:
            res = ""
        for i, user in enumerate(self._players):
            res += f"\n{_TTT_SIM[i]} {user.mention}"
        return res

    def game_status(self) -> hikari.Embed:
        """Собирает сообщение со статусом игры.

        данное сообщение будет обновляться при каждом нажатии кнопки.
        Возвращает название, описание, кто сейчас ходит, режим игры,
        правила, а также список игроков.

        Словом, вся необходимая информация о текущем ходе игры.
        Когда игра будет закончена с некоторым результатом, данное
        сообщение будет заменено другим.
        """
        return (
            hikari.Embed(
                title=f"{_TTT_SIM[self._cur]} Крестики-нолики",
                description=(
                    "Перед вами игровое поле.\n"
                    "Вы сошлись здесь в дуэли, чтобы доказать свою силу.\n"
                    "Мешать вам будет только ограниченное поле и ваш противник."
                ),
                colour=hikari.colors.Color(0x00B0F4),
            )
            .add_field(
                name="Режим игры",
                value="Бесконечный" if self.endless else "Обычный.",
                inline=True,
            )
            .add_field(name="Игроки", value=self.get_players(), inline=True)
            .add_field(
                name="Правила игры",
                value=_GAME_RULES,
            )
        )

    def end_game_no_winner(self) -> hikari.Embed:
        """Собирает сообщение при ничьей.

        Используется по окончанию игры в ничейную пользу.
        Данный исход возможен при стандартном режиме игры, когда
        не остаётся свободных клеток.

        Отображает количество описание, режим игры и игроков.
        """
        return (
            hikari.Embed(
                title=f"{_TTT_SIM[self._cur]} Крестики-нолики / Ничья",
                description=(
                    "Это была долгая битва.\n"
                    "Однако поле закончилось.\n"
                    "Теперь не получится выяснить кто выиграл."
                ),
                colour=hikari.colors.Color(0xFFBE6F),
            )
            .add_field(name="Режим игры", value="Обычный", inline=True)
            .add_field(name="Игроки", value=self.get_players(), inline=True)
        )

    def end_game_message(self, winner: hikari.User) -> hikari.Embed:
        """Сообщение при победе одного из игроков.

        Отображается сразу как только кто-то из игроков одержал победу.
        Отображает описание, победителя, режим, список игроков.
        """
        return (
            hikari.Embed(
                title=f"{_TTT_SIM[self._cur]} Крестики-нолики / Игра завершена",
                description=(
                    "Это была долгая битва.\n"
                    "И только один мог выйти из неё победителем.\n\n"
                    f"**Победитель**: {winner.mention}"
                ),
                colour=hikari.colors.Color(0x8FF0A4),
            )
            .add_field(
                name="Режим игры",
                value="Бесконечный" if self.endless else "Обычный.",
                inline=True,
            )
            .add_field(name="Игроки", value=self.get_players(), inline=True)
        )

    def current_player(self) -> str:
        """Собирает информацию о текущем игроке.

        Символ игрока, а также его упоминание.
        """
        res = _TTT_SIM[self._cur]
        if len(self._players) < 2:  # noqa: PLR2004
            return res + " игрока"
        else:
            return f"{res} {self._players[self._cur].mention}"

    def no_valid_player_message(self) -> hikari.Embed:
        """Сообщение если кто-то посторонний нажал на кнопку.

        Это может быть как просто сторонний пользователь, так и игрок,
        до которого ещё не дошла очередь.
        В таком случае будет отправлено сообщение с ошибкой.
        Данное сообщение будет удалено через некоторое время, чтобы
        не засорять чат.
        """
        return hikari.Embed(
            title=f"{_TTT_SIM[self._cur]} Крестики-нолики / Ась?",
            description=(
                "Возможно вы не участник данной игры.\n"
                "ну или возможно сейчас не ваш ход.\n\n"
                "Так или иначе сейчас ход:"
                f"{self.current_player()}"
            ),
            colour=hikari.colors.Color(0xDC8ADD),
        )


# определение команд
# ==================


@plugin.include
@arc.slash_command("ttt", description="Начать игру крестики-нолики.")
async def nya_handler(
    ctx: arc.GatewayContext,
    endless: arc.Option[
        bool, arc.BoolParams("Бесконечная ли игр (нет)")
    ] = False,
    client: miru.Client = arc.inject(),
) -> None:
    """Начинает новую игру крестики-нолики.

    Для того чтобы двум игрокам начать играть, достаточно нажать на
    поле.
    Бот сам запомнит первых двух участников игры, чтобы никто другой
    не мог помешать их игре.
    """
    view = TicTacToeView(endless=endless)
    await ctx.respond(view.game_status(), components=view)
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
