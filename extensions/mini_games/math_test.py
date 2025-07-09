"""Тест по математике.

Позволяет участникам соревноваться в навыках подсчёта чисел.

Предоставляет
-------------

- /math - Начать тест по математике.

Version: v0.5.1 (10)
Author: Milinuri Nirvalen
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import IntEnum
from random import randint, shuffle

import arc
import hikari
import miru

plugin = arc.GatewayPlugin("Math Test")

_MATH_TIMER = 60
_OPERATORS = ["+", "-", "*", "/"]


class Operators(IntEnum):
    """Доступные операторы лдя математических упражнений."""

    add = 0
    sub = 1
    mul = 2
    div = 3

    def result(self, a: int, b: int) -> int:
        """Получает результат для данного оператора над двумя числами."""
        if self.value == Operators.add:
            return a + b
        elif self.value == Operators.sub:
            return a - b
        elif self.value == Operators.mul:
            return a * b
        elif self.value == Operators.div:
            return round(a / b)
        return 1

    def __str__(self) -> str:
        """Возвращает строковое представление оператора."""
        return _OPERATORS[self.value]


@dataclass
class MathExample:
    """Математический пример для решения."""

    num_a: int
    num_b: int
    operator: Operators
    result: int


class ResultButton(miru.Button):
    """Кнопка с вариантом ответа.

    Одна из кнопок с правильным ответом.
    Другие с случайно подобранным значением.
    Задача игрока нажать на кнопку с правильным ответом.
    """

    def __init__(self) -> None:
        super().__init__(label="?")
        self.view: MathView
        self.number = 0

    async def callback(self, ctx: miru.ViewContext) -> None:
        """Действия при нажатие на кнопку.

        Отправляет ответ в view.
        Обновляет состояние игры.
        Если игра кончилась, завершает view.
        """
        res = self.view.answer_example(self.number)
        if res:
            await ctx.edit_response(self.view.status(), components=self.view)
        else:
            await ctx.edit_response(self.view.status(), components=None)
            self.view.stop()

    def set_num(self, num: int) -> None:
        """Устанавливает новое значение для кнопки."""
        self.number = num
        self.label = str(num)


class MathView(miru.View):
    """Математические задачки.

    Предоставляет embed с математическим примером и 4 вариантами ответа.
    Задача игрока нажать на правильную кнопку.
    """

    def __init__(self) -> None:
        super().__init__()
        self.success = 0
        self.fail = 0
        self.total = 0

        self.end_time: datetime | None = None
        self.example: MathExample | None = None

        self.buttons: list[ResultButton] = []
        self.new_game()

    @property
    def score(self) -> int:
        """Подсчитывает общий результат для игры."""
        return round((self.success * 10) * (self.success / self.total))

    def new_game(self) -> None:
        """Начинает новую игру."""
        self.success = 0
        self.fail = 0
        self.end_time = datetime.now() + timedelta(seconds=_MATH_TIMER)
        self.example = self.get_example()

        self.buttons = []
        for _ in range(4):
            b = ResultButton()
            self.buttons.append(b)
            self.add_item(b)

        self.add_answers(self.example)

    def get_example(self) -> MathExample:
        """Получает новый пример."""
        first = randint(0, 100)
        second = randint(1, 100)
        operator = Operators(randint(0, 3))
        return MathExample(
            first, second, operator, operator.result(first, second)
        )

    def add_answers(self, example: MathExample) -> None:
        """Добавляет случайные ответы на задачу."""
        res: list[int] = []
        res.append(example.result)
        for m in range(1, 4):
            res.append(example.result + randint(-m, m * 10))
        shuffle(res)

        for i, r in enumerate(res):
            self.buttons[i].set_num(r)

    def status(self) -> hikari.Embed:
        """Собирает сообщение статуса игры.

        Содержит текущий пример, результаты игры и сколько осталось времени.
        """
        if self.example is None:
            example = "А где пример?"
        else:
            example = (
                f"{self.example.num_a} {self.example.operator} "
                f"{self.example.num_b} = `?`"
            )
        now = datetime.now()

        emb = hikari.Embed(
            title="🧮 Тест по математике",
            description=f"✏️ Вопрос: {self.total + 1}\n{example}",
            color=0x33FFCC,
        )

        if self.total > 0:
            emb.add_field(
                "Результат",
                (
                    f"**Счёт**: {self.score}\n"
                    f"`{self.success}` / `{self.total}` (`{self.fail}` ошибок)"
                ),
            )

        if self.end_time is not None:
            time_left = round((self.end_time - now).total_seconds())
            emb.add_field(
                "Время",
                f"Осталось: {time_left} секунд",
            )

        return emb

    def answer_example(self, res: int) -> bool:
        """Проверяет правильность ответа пользователя.

        Возвращает флаг продолжения игры.
        Игра завершается когда кончается время.
        если время ещё не кончилось - даёт новый пример.
        """
        if self.example is None or self.end_time is None:
            return False

        if res == self.example.result:
            self.success += 1
        else:
            self.fail += 1
        self.total += 1

        now = datetime.now()
        if now >= self.end_time:
            return False

        self.example = self.get_example()
        self.add_answers(self.example)

        return True


# определение команд
# ==================


@plugin.include
@arc.slash_command("math", description="Начать тест по математике.")
async def nya_handler(
    ctx: arc.GatewayContext, client: miru.Client = arc.inject()
) -> None:
    """Первая няшная команда для бота.

    Позволяет някнуть участника, пожалуй это достаточно мило.
    Впрочем более эта команда ничего не делает.
    """
    view = MathView()
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
