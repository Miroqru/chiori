"""Простой модуль для работы с цветовой палитрой.

Представляет класс для представления цвета.
Позволяет получать цветовой код из строки.
А также переводить цвета из различных форматов.

Содержит
--------

- Паттерны для поиска цветового кода в строке.
- Исключение при неправильном получении цвета.
- Класс для работы с цветом.

пример использования:

```py
# Некоторый цветовой код формата #RRGGBB
text_color = "#00ffcc"

# Получаем класс цвета и преобразуем его в HSV
color = Color.from_hex(text_color) # Color(0, 204, 255)
hsv = color.to_hsv()
```

.. warning:: Неэффективное хранение памяти.

    Обратите внимание что для хранения цвета используется три числа.
    Можно считать это расточительным использованием памяти.
    Помните про это, если будете использовать библиотеку.

Author: Milinuri Nirvalen
Version: v0.2.3 (10)
"""

import colorsys
import re
from random import randint
from typing import NamedTuple

# паттерны для поиска цвета
# =========================

hexcolor_pattern = re.compile(r"#[0-9a-f]{6}")
rgb_pattern = re.compile(r"rgb\((\d{0,3}),\s?(\d{0,3}),\s?(\d{0,3})\)")
hsv_pattern = re.compile(r"hsv\((\d{0,3}),\s?(\d{0,3}),\s?(\d{0,3})\)")


# Исключения
# ==========


class ColorParseError(Exception):
    """При ошибке получения цветового кода из переведённой строки."""


# Различные цветовые сборщики
# ===========================


def parse_color_hex(text: str) -> str | None:
    """Получает цветовой код из строки.

    Обрабатывает строку в поисках цветового года.

    - #FFFFFF -> #FFFFFF
    - ssas -> None
    - aa #aaaaaa -> #aaaaaa
    """
    color_hex = hexcolor_pattern.search(text)
    if color_hex is None:
        return None
    return color_hex.group()


def parse_color_rgb(text: str) -> tuple[int, int, int] | None:
    """Извлекает rgb строку текста.

    Обрабатывает строку в поисках RGB цветового года.

    - rgb(255, 255, 255) -> #FFFFFF
    - hello -> None
    - aa rgb(204,0,204) -> #cc00cc
    """
    rgb = rgb_pattern.search(text)
    if rgb is None:
        return None
    groups = rgb.groups()

    # Следим чтобы не вышли за границы 00 - FF
    return (
        max(min(int(groups[0]), 255), 0),
        max(min(int(groups[1]), 255), 0),
        max(min(int(groups[2]), 255), 0),
    )


def parse_color_hsv(text: str) -> tuple[int, int, int] | None:
    """Извлекает hsv строку текста.

    Обрабатывает строку в поисках hsb цветового года.

    - hsv(0, 0, 100) -> #FFFFFF
    - hello -> None
    - aa hsv(300,100,80) -> #cc00cc
    """
    hsv = hsv_pattern.search(text)
    if hsv is None:
        return None
    groups = hsv.groups()

    # Следим чтобы не вышли за границы 0 - 100/360
    return (
        max(min(int(groups[0]), 360), 0),
        max(min(int(groups[1]), 100), 0),
        max(min(int(groups[2]), 100), 0),
    )


class Color(NamedTuple):
    """Представляет собой цвет в цветовом пространстве RGB.

    Для корректной работы диапазон хранимых чисел должен быть от 0 до
    255.
    """

    red: int
    green: int
    blue: int

    # Методы для получения цвета
    # ==========================

    @classmethod
    def random(cls) -> "Color":
        """Возвращает некоторый случайный цвет."""
        return Color(
            red=randint(0, 255),
            green=randint(0, 255),
            blue=randint(0, 255),
        )

    @classmethod
    def from_hex(cls, text: str) -> "Color":
        """Получает цвета из hex кода.

        ```
            #ffccff
             | |  - Blue (00 - ff)
             | - Green (00 - ff)
             - Red (00 - ff)
        ```

        - #ffccff -> Color(255, 204, 255).
        - dlsdas -> ColorParseError()

        Если не удалось получить цвет, выбрасывает исключение.

        Args:
            text (str): Строка из которой нужно получить цвет.

        Returns:
            Color: Представление цвета в RGB пространстве

        """
        color_hex = parse_color_hex(text)
        if color_hex is None:
            raise ColorParseError(f"No math hex color from: {text}")

        return Color(
            red=int(color_hex[1:3], base=16),
            green=int(color_hex[3:5], base=16),
            blue=int(color_hex[5:7], base=16),
        )

    @classmethod
    def from_rgb(cls, text: str) -> "Color":
        """Получает цвето из rgb строки текста.

        ```
            rgb(204, 0, 255)
                |    |  - Blue (0 - 255)
                |    - Green (0 - 255)
                - Red (0 - 255)
        ```

        - rgb(255, 255, 255) -> #FFFFFF
        - hello -> ColorParseError()
        - aa rgb(204,0,204) -> #cc00cc

        Если не удалось извлечь цвет, выбрасывает исключение.

        Args:
            text (str): Строка из которой нужно получить цвет.

        Returns:
            Color: Представление цвета в RGB пространстве

        """
        rgb = parse_color_rgb(text)
        if rgb is None:
            raise ColorParseError(f"No math RGB color from: {text}")
        return Color(red=rgb[0], green=rgb[1], blue=rgb[2])

    @classmethod
    def from_hsv(cls, text: str) -> "Color":
        """Получает цвета из hsv строки текста.

        - hsv(0, 0, 100) -> #FFFFFF
        - hello -> ColorParseError()
        - aa hsv(300,100,80) -> #cc00cc

        если не удалось получить цвет, выбрасывает исключение.

        Args:
            text (str): Строка из которой нужно получить цвет.

        Returns:
            Color: Представление цвета в RGB пространстве

        """
        hsv = parse_color_hsv(text)
        if hsv is None:
            raise ColorParseError(f"No math HSV color from: {text}")
        return Color(red=hsv[0], green=hsv[1], blue=hsv[2])

    # Пытаемся угадать цвет из строки
    # ===============================

    @classmethod
    def parse_color(cls, text: str) -> "Color":
        """Пытается получить цветовой код из строки.

        Просматривает строку на наличие RGB, hex, HSV кодов цвета.

        Args:
            text (str): Строка из которой нужно получить цвет.

        Returns:
            Color: Представление цвета в RGB пространстве

        """
        hex_color = parse_color_hex(text)
        if hex_color is not None:
            return Color(
                red=int(hex_color[1:3], base=16),
                green=int(hex_color[3:5], base=16),
                blue=int(hex_color[5:7], base=16),
            )

        rgb_color = parse_color_rgb(text)
        if rgb_color is not None:
            return Color(
                red=rgb_color[0], green=rgb_color[1], blue=rgb_color[2]
            )

        hsv_color = parse_color_hsv(text)
        if hsv_color is not None:
            to_rgb = colorsys.hsv_to_rgb(
                hsv_color[0] / 360,
                hsv_color[1] / 100,
                hsv_color[2] / 100,
            )
            return Color(
                red=round(to_rgb[0] * 255),
                green=round(to_rgb[1] * 255),
                blue=round(to_rgb[2] * 255),
            )

        raise ColorParseError(f"No match color code in text: {text}")

    # цветовые конверторы
    # ===================

    def to_hex_code(self) -> str:
        """преобразует цвет в hex код.

        - Color(255, 204, 255) -> #ffccff
        """
        r = hex(self.red)[2:]
        g = hex(self.green)[2:]
        b = hex(self.blue)[2:]
        return f"#{r:0>2}{g:0>2}{b:0>2}"

    def to_hsv(self) -> tuple[int, int, int]:
        """Преобразует RGB цвет в HSV.

        Возвращает кортеж из трёх чисел:
        - Оттенок (0-360).
        - Контраст (0-100).
        - Яркость (0-100).
        """
        hsv = colorsys.rgb_to_hsv(
            self.red / 255,
            self.green / 255,
            self.blue / 255,
        )
        return (
            round(hsv[0] * 360),
            round(hsv[1] * 100),
            round(hsv[2] * 100),
        )
