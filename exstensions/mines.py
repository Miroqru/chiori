"""Игра Сапёр.

Данная игра в представлении не нуждается.
У вас есть поле 5 на 5 клеток, но некоторые из них заминированы.
Как только вы открываете пустое поле, на нём показывается число бомб
поблизости.
Для прохождения игры вам необхоидмо открыть все пустые клетки, не
задев при этом ни одной бомбы.

Предоставляет
-------------

- /mines - Начать игру

Version: v0.3 (13)
Author: Milinuri Nirvalen
"""

import random

import arc
import hikari
import miru


plugin = arc.GatewayPlugin("mines")


# Функции для сборки динамических сообщений
# =========================================

def get_game_status(view) -> hikari.Embed:
     """Сообщение со статусом игры.

     Используется чтобы отобразить текущий прогресс активной игры.
     Показывает основную информацию об игре, правила, а также
     сколько на поле мин и сколько осталось открыть клеток.

    :param view: Экземпляр представления минного поля.
    :type view: miru.View
    :return: Embed, который будет отправлен ботом в чат.
    :rtype: hikari.Embed
     """
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
    ).add_field(name="Бомб", value=str(view.total_bombs), inline=True
    ).add_field(name="Осталось клеток", value=str(view.cels_left), inline=True)


# Классы предствления минного поля
# ================================

class EmptyButton(miru.Button):
    """Пустая кнопка на минном поле.

    Ничего плохого не случится, если на неё нажать.
    По умолчанию она просто серая и не примечатльная, ничем не
    отличается от поля с бомбой.

    Как только вы на неё нажмёте, оно рекурсивно откроется.
    Теперь вместо знака вопроса на ней будет отображено число ближайших
    бомб.
    Если число больше 0, то цвет кнопки поменяется, чтобы предупрежить,
    что где-то рядом может быть бомба.

    Как только вы окроете последную пустую клетку, игра завершится
    победой для вас.

    :param index: Номер позиции кнопки (0-24).
    :type index: int
    """

    def __init__(self, index: int) -> None:
        super().__init__(
            label="?",
            style=hikari.ButtonStyle.SECONDARY
        )
        self.index = index


    async def callback(self, ctx: miru.ViewContext) -> None:
        """Действие при нажатие на кнопку.

        Как только вы нажимаете на кнопку, она рекурсивно открывается.
        Если это была последняя кнопка, то игра завершится вашей
        победой.

        :param ctx: Конктекст, при котором была нажата кнопка.
        :type ctx: miru.ViewContext
        """
        self.view.recursive_open(self)

        # Это ваше победное сообщение
        if self.view.cels_left == 0:
            self.view.open_bomds()
            self.view.stop()
            await ctx.edit_response(embed=hikari.Embed(
                title="💣 Сапёр / Игра пройдена",
                description=(
                        "Поздравляем с успешным прохождением игры.\n"
                        "Мы и не сомневались в том, что вы сможете победить."
                    ),
                color=hikari.colors.Color(0x8ff0a4)
                ),
                components=self.view
            )
        else:
            await ctx.edit_response(
                embed=get_game_status(self.view),
                components=self.view
            )

    def set_open(self, nerby_bombs: int):
        """Помечает клетку как открытую.

        Делает её отключеной, чтобы не было возможности снова её нажать.
        Также меняет текст кнопки на количество ближайших бомб.
        Цвет кнопки также может измениться в зависимости от ближайших
        бомб.

        :param nerby_bombs: Количество ближайших бомб для отображения.
        :type nerby_bombs: int
        """
        self.disabled = True
        if nerby_bombs > 0:
            self.style = hikari.ButtonStyle.PRIMARY
        self.label = str(nerby_bombs)


class BombButton(miru.Button):
    """Поле с бомбой.

    Если на него нажать, игра для вас окончится.
    Было ли это случайностью или намеренно неизвестно.
    Оно никак не выделсятеся по сравению с обычным.
    И лишь ближайшие пустые клетки могут вам подсказать где бомба.

    :param index: Порядковые номер поля (0 - 24).
    :type index: int
    """
    def __init__(self, index: int) -> None:
        super().__init__(
            label="?",
            style=hikari.ButtonStyle.SECONDARY
        )
        self.index = index

    async def callback(self, ctx: miru.ViewContext) -> None:
        """Действие при нажатии на кнопку.

        Когда вы нажимиете на бомбу, игра для вас заканчивается.
        на поле будут отображены другие бомбы.

        :param ctx: Конктекст, при котором была нажата кнопка.
        :type ctx: miru.ViewContext
        """
        self.view.open_bomds()
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
            ).add_field(
                name="Всего бомб",
                value=str(self.view.total_bombs),
                inline=True
            ).add_field(
                name="Осталось клеток",
                value=str(self.view.cels_left),
                inline=True
            ),
            components=self.view
        )


class MineView(miru.View):
    """Представление минного поля.

    Перед вами поле 5 на 5.
    Ваша задача нажать на все пустые поля, не задев поля с бомбами.
    """

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
            if random.randint(1, 5) == 5:
                button = BombButton(x)
                self.total_bombs += 1
            else:
              button = EmptyButton(x)

            self.mines.append(button)
            self.add_item(button)
            self.cels_left = 25 - self.total_bombs

    def get_neibhoors(self, index: int) -> list[miru.Button]:
        pos_y, pos_x = divmod(index, 5)
        bomb_counter = 0
        buttons = []

        for y_shift in range(-1, 2):
            if pos_y+y_shift < 0 or pos_y+y_shift > 4:
                continue

            for x_shift in range(-1, 2):
                if pos_x+x_shift < 0 or pos_x+x_shift > 4:
                    continue

                if x_shift == 0 and y_shift == 0:
                    continue

                pos = (pos_y+y_shift)*5 + (pos_x+x_shift)
                button = self.mines[pos]
                if not button.disabled:
                    buttons.append(button)
        return buttons

    def count_bombs(self, buttons: list[miru.Button]) -> int:
        bomb_counter = 0
        for button in buttons:
            if isinstance(button, BombButton):
                bomb_counter += 1
        return bomb_counter

    def recursive_open(self, index: miru.Button) -> None:
        targets = [index]

        for target in targets:
            if target.disabled:
                continue

            neibhoors = self.get_neibhoors(target.index)
            nerby_bombs = self.count_bombs(neibhoors)
            target.set_open(nerby_bombs)
            self.cels_left -= 1

            if nerby_bombs == 0:
                targets.extend(neibhoors)

    def open_bomds(self):
        for x in self.mines:
            if isinstance(x, BombButton):
                x.label = "💣"


# определение команд
# ==================

@plugin.include
@arc.slash_command("mines", description="Начать игру сапёр.")
async def mines_handler(
    ctx: arc.GatewayContext,
    client: miru.Client = arc.inject()
) -> None:
    """Запускаем игру сапёр."""
    view = MineView()
    await ctx.respond(embed=get_game_status(view), components=view)
    client.start_view(view)


# Загрузчики и выгрузчики плагина
# ===============================

@arc.loader
def loader(client: arc.GatewayClient) -> None:
    """Отвечает за загрузку плагина."""
    client.add_plugin(plugin)

@arc.unloader
def unloader(client: arc.GatewayClient) -> None:
    """Отвечает за выгрузку плагина."""
    client.remove_plugin(plugin)
