"""Простой модуль для работы с цветовой палитрой.

Author: Milinuri Nirvalen
Version: v0.2 (3)
"""

import colorsys
import re
from random import randint
from typing import NamedTuple


hexcolor_patter = re.compile(r'#[0-9a-f]{6}')

class ColorParseError(Exception):
    """Используется, когда не удалось получить цветовой код из строки."""
    pass


def parse_color_hex(text: str) -> str | None:
    """Получает цветовой код из строки.

    Обрабатывает строку в поисках цветового года.
    > #FFFFFF -> #FFFFFF
    > ssas -> None
    > aa #aaaaaa -> #aaaaaa

    :param text: Текст из которого нужно извлечь цветовой код.
    :type text: str
    :return: Цветовой код или ничего.
    :rtype: str | None
    """
    color_hex = hexcolor_patter.search(text)
    if color_hex is None:
        return None
    return color_hex.group()


class Color(NamedTuple):
    """Представляет собой цвет в цветовом пространстве RGB."""
    red: int
    green: int
    blue: int

    @classmethod
    def random(clt) -> "Color":
        """Возвращает случайный цвет."""
        return Color(
            red = randint(1, 255),
            green = randint(1, 255),
            blue = randint(1, 255),
        )

    @classmethod
    def from_hex(cls, text: str) -> "Color":
        """Получает цвето из hex кода.

        - #ffccff -> Color(255, 204, 255).
        - dlsdas -> ColorParseEroor()

        если не удалось получить цвет, выбрасывает исключение.

        :param text: Цветовой код из которого нужно получить цвет.
        :type text: str
        :return: Цвет.
        :rtype: Color
        """
        color_hex = parse_color_hex(text)
        if color_hex is None:
            raise ColorParseError(f"No math color from: {text}")

        return Color(
            red = int(color_hex[1:3], base=16),
            green = int(color_hex[3:5], base=16),
            blue = int(color_hex[5:7], base=16)
        )

    def to_hex_code(self) -> str:
        """преобразует цвет в hex код.

        - Color(255, 204, 255) -> #ffccff

        :return: Цветовой hex-код.
        :rtype: str
        """
        return f"#{hex(self.red)[2:]:0>2}{hex(self.green)[2:]:0>2}{hex(self.blue)[2:]:0>2}"

    def to_hsv(self) -> tuple[int, int, int]:
        """Преобразует RGB цвет в HSV."""
        hsv = colorsys.rgb_to_hsv(
            self.red/255,
            self.green/255,
            self.blue/255,
        )
        return (
            round(hsv[0] * 360),
            round(hsv[1] * 100),
            round(hsv[2] * 100),
        )
