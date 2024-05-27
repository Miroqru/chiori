"""Простой модуль для работы с цветовой палитрой.

Author: Milinuri Nirvalen
Version: v0.2 (7)
"""

import colorsys
import re
from random import randint
from typing import NamedTuple


hexcolor_pattern = re.compile(r'#[0-9a-f]{6}')
rgb_pattern = re.compile(r"rgb\((\d{0,3}),\s?(\d{0,3}),\s?(\d{0,3})\)")
hsv_pattern = re.compile(r"hsv\((\d{0,3}),\s?(\d{0,3}),\s?(\d{0,3})\)")

class ColorParseError(Exception):
    """Используется, когда не удалось получить цветовой код из строки."""
    pass


def parse_color_hex(text: str) -> str | None:
    """Получает цветовой код из строки.

    Обрабатывает строку в поисках цветового года.

    - #FFFFFF -> #FFFFFF
    - ssas -> None
    - aa #aaaaaa -> #aaaaaa

    :param text: Текст из которого нужно извлечь цветовой код.
    :type text: str
    :return: Цветовой код или ничего.
    :rtype: str | None
    """
    color_hex = hexcolor_pattern.search(text)
    if color_hex is None:
        return None
    return color_hex.group()

def parse_color_rgb(text: str) -> tuple[int, int, int] | None:
    """Извлекает rgb строку текста.

    Обрабатывает строку в поисках RGB цветового года.

    - rgb(255, 255, 255) -> #FFFFFF
    - ssas -> None
    - aa rgb(204,0,204) -> #cc00cc

    :param text: Текст из которого нужно извлечь цветовой код.
    :type text: str
    :return: Кортеж r,g,b чисел от 0 до 255 или ничего.
    :rtype: str | None
    """
    rgb = rgb_pattern.search(text)
    if rgb is None:
        return None
    groups = rgb.groups()

    # Следим чтобы не вышли за границы 00 - FF
    return (
        max(min(int(groups[0]), 255), 0),
        max(min(int(groups[1]), 255), 0),
        max(min(int(groups[2]), 255), 0)
    )

def parse_color_hsv(text: str) -> tuple[int, int, int] | None:
    """Извлекает hsv строку текста.

    Обрабатывает строку в поисках hsb цветового года.

    - hsv(0, 0, 100) -> #FFFFFF
    - ssas -> None
    - aa hsv(300,100,80) -> #cc00cc

    :param text: Текст из которого нужно извлечь цветовой код.
    :type text: str
    :return: Кортеж h,s,v чисел от 0 до 360/100 или ничего.
    :rtype: str | None
    """
    hsv = hsv_pattern.search(text)
    if hsv is None:
        return None
    groups = hsv.groups()

    # Следим чтобы не вышли за границы 0 - 100/360
    return (
        max(min(int(groups[0]), 360), 0),
        max(min(int(groups[1]), 100), 0),
        max(min(int(groups[2]), 100), 0)
    )


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
        :return: Представление цвета в RGB пространстве.
        :rtype: Color
        """
        color_hex = parse_color_hex(text)
        if color_hex is None:
            raise ColorParseError(f"No math hex color from: {text}")

        return Color(
            red = int(color_hex[1:3], base=16),
            green = int(color_hex[3:5], base=16),
            blue = int(color_hex[5:7], base=16)
        )

    @classmethod
    def from_rgb(cls, text: str) -> "Color":
        """Получает цвето из rgb строки текста.

        - rgb(255, 255, 255) -> #FFFFFF
        - ssas -> ColorParseEroor()
        - aa rgb(204,0,204) -> #cc00cc

        если не удалось получить цвет, выбрасывает исключение.

        :param text: Строка из которого нужно получить цвет.
        :type text: str
        :return: Представление цвета в RGB пространстве.
        :rtype: Color
        """
        rgb = parse_color_rgb(text)
        if rgb is None:
            raise ColorParseError(f"No math RGB color from: {text}")
        return Color(red = rgb[0], green = rgb[1], blue = rgb[2])

    @classmethod
    def from_hsv(cls, text: str) -> "Color":
        """Получает цвето из hsv строки текста.

        - hsv(0, 0, 100) -> #FFFFFF
        - ssas -> ColorParseEroor()
        - aa hsv(300,100,80) -> #cc00cc

        если не удалось получить цвет, выбрасывает исключение.

        :param text: Строка из которого нужно получить цвет.
        :type text: str
        :return: Представление цвета в RGB пространстве.
        :rtype: Color
        """
        hsv = parse_color_hsv(text)
        if hsv is None:
            raise ColorParseError(f"No math HSV color from: {text}")
        return Color(red = hsv[0], green = hsv[1], blue = hsv[2])


    @classmethod
    def parse_color(self, text: str) -> "Color":
        """Пытается получить цветовой код из строки.

        Просматривает строку на наличие RGB, hex, HSV кодов цвета.

        :param text: Строка из которого нужно получить цвет.
        :type text: str
        :return: Представление цвета в RGB пространстве.
        :rtype: Color
        """
        hex_color = parse_color_hex(text)
        if hex_color is not None:
            return Color(
                red = int(hex_color[1:3], base=16),
                green = int(hex_color[3:5], base=16),
                blue = int(hex_color[5:7], base=16)
            )
        rgb_color = parse_color_rgb(text)
        if rgb_color is not None:
            return Color(
                red = rgb_color[0],
                green = rgb_color[1],
                blue = rgb_color[2]
            )
        hsv_color = parse_color_hsv(text)
        if hsv_color is not None:
            rgb_color = colorsys.hsv_to_rgb(
                hsv_color[0]/360,
                hsv_color[1]/100,
                hsv_color[2]/100,
            )
            return Color(
                red = round(rgb_color[0] * 255),
                green = round(rgb_color[1] * 255),
                blue = round(rgb_color[2] * 255)
            )
        raise ColorParseError(f"No match color code in text: {text}")



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

if __name__ == "__main__":
    c1 = Color.parse_color("#cc00cc")
    ic(c1, c1.to_hsv(), c1.to_hex_code())

    c2 = Color.parse_color("rgb(12, 0, 204)")
    ic(c2, c2.to_hsv(), c2.to_hex_code())

    c3 = Color.parse_color("hsv(300, 100, 80)")
    ic(c3, c3.to_hsv(), c3.to_hex_code())
