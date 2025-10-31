"""Простой модуль для работы с цветовой палитрой.

Представляет класс для представления цвета.
Позволяет получать цветовой код из строки.
А также переводить цвета из различных форматов.

Author: Milinuri Nirvalen
Version: v0.3 (12)
"""

import colorsys
import re

from hikari import Color

rgb_pattern = re.compile(r"rgb\((\d{0,3}),\s?(\d{0,3}),\s?(\d{0,3})\)")
hsv_pattern = re.compile(r"hsv\((\d{0,3}),\s?(\d{0,3}),\s?(\d{0,3})\)")


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
    return (int(groups[0]) % 255, int(groups[1]) % 255, int(groups[2]) % 255)


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
    return (int(groups[0]) % 360, int(groups[1]) % 100, int(groups[2]) % 100)


class HsvColor(Color):
    """Надстройка над `hikari.Color`.

    Предоставляет дополнительные методы для работы с hsv цветом.
    """

    @classmethod
    def from_hsv(cls, text: str) -> "HsvColor":
        """Получает цвета из hsv строки текста.

        - hsv(0, 0, 100) -> #FFFFFF
        - hello -> ColorParseError()
        - aa hsv(300,100,80) -> #cc00cc

        если не удалось получить цвет, выбрасывает исключение.

        Args:
            text (str): Строка из которой нужно получить цвет.

        """
        hsv = parse_color_hsv(text)
        if hsv is None:
            raise ValueError(f"No math HSV color from: {text}")
        rgb = colorsys.hsv_to_rgb(hsv[0], hsv[1], hsv[2])
        # Типизация шалит, спасибо hikari
        return HsvColor.from_rgb_float(rgb[0], rgb[1], rgb[2])  # pyright: ignore[reportReturnType]

    @classmethod
    def parse(cls, text: str) -> "HsvColor":
        """Пытается получить цветовой код из строки.

        Просматривает строку на наличие RGB, hex, HSV кодов цвета.

        Args:
            text (str): Строка из которой нужно получить цвет.

        Returns:
            Color: Представление цвета в RGB пространстве

        """
        rgb = parse_color_rgb(text)
        if rgb is not None:
            return HsvColor.from_rgb(rgb[0], rgb[1], rgb[2])  # pyright: ignore[reportReturnType]

        hsv = parse_color_hsv(text)
        if hsv is not None:
            to_rgb = colorsys.hsv_to_rgb(
                hsv[0] / 360, hsv[1] / 100, hsv[2] / 100
            )
            return HsvColor.from_rgb_float(to_rgb[0], to_rgb[1], to_rgb[2])  # pyright: ignore[reportReturnType]

        # Типизация шалит, спасибо hikari
        return HsvColor.from_hex_code(text)  # pyright: ignore[reportReturnType]

    @property
    def hsv(self) -> tuple[int, int, int]:
        """Преобразует RGB цвет в HSV.

        Возвращает кортеж из трёх чисел:
        - Оттенок (0-360).
        - Контраст (0-100).
        - Яркость (0-100).
        """
        hsv = colorsys.rgb_to_hsv(
            (self >> 16) & 0xFF, (self >> 8) & 0xFF, self & 0xFF
        )
        return (round(hsv[0] * 360), round(hsv[1] * 100), round(hsv[2] * 100))
