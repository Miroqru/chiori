"""Рунический переводчик.

переносит скрипт переводчика их проекта Diverse в Chiori.

Некоторые правила перевода:
- Каждый русский символ переводится согласно таблице.
- Каждые 2 переведённые символа обрамляются отступом.
- Символ ⌀ (пробел) обрамляется отступами всегда.
- Все прочие символы остаются не тронутыми.
- При переводе теряется привязка к регистру.

Version: v1.0.4 (5)
Author: Milinuri Nirvalen
"""

from typing import NamedTuple

import arc
import hikari

from chioricord.client import ChioClient, ChioContext
from chioricord.plugin import ChioPlugin

plugin = ChioPlugin("Rune")


class Rune(NamedTuple):
    """Представление каждой буквы при переводе.

    Содержит в себе как символ, так и его произношение.
    """

    rune: str
    pronounce: str


RUNE_TABLE = {
    "а": Rune("ℵ", "Ло"),
    "б": Rune("ℵᵥ", "Но"),
    "в": Rune("ℵᵦ", "Со"),
    "г": Rune("ℵᵣ", "Фо"),
    "д": Rune("ℶ", "Лу"),
    "е": Rune("ℶᵥ", "Ну"),
    "ё": Rune("ℶᵦ", "Су"),
    "ж": Rune("ℶᵧ", "Фу"),
    "з": Rune("ℶᵣ", "Шу"),
    "и": Rune("ℷ", "Ле"),
    "й": Rune("ℷᵥ", "Не"),
    "к": Rune("ℷᵦ", "Се"),
    "л": Rune("ℷᵧ", "Фе"),
    "м": Rune("ℷᵣ", "Ше"),
    "н": Rune("ℸ", "Ла"),
    "о": Rune("ℸᵥ", "На"),
    "п": Rune("ℸᵦ", "Са"),
    "р": Rune("ℸᵧ", "Фа"),
    "с": Rune("ℸᵣ", "Ша"),
    "т": Rune("ⅎ", "Ли"),
    "у": Rune("ⅎᵥ", "Ни"),
    "ф": Rune("ⅎᵦ", "Си"),
    "х": Rune("ⅎᵧ", "Фи"),
    "ц": Rune("ⅎᵣ", "Ши"),
    "ч": Rune("⍺", "Ля"),
    "ш": Rune("⍺ᵥ", "Нн"),
    "щ": Rune("⍺ᵦ", "Ся"),
    "Ъ": Rune("⍺ᵧ", "Фя"),
    "ы": Rune("⍺ᵣ", "Шя"),
    "ь": Rune("ᴪ", "Лю"),
    "э": Rune("ᴪᵥ", "Ню"),
    "ю": Rune("ᴪᵦ", "Сю"),
    "я": Rune("ᴪᵧᵣ", "Фю"),
    " ": Rune("⌀", "Тос"),
}


# Функции перевода
# ================


def get_text(text_rune: str) -> str | None:
    """Получает рунический символ из текста."""
    for text, rune in RUNE_TABLE.items():
        if text_rune == rune.rune:
            return text
    return None


def translate_to_rune(text: str) -> str:
    """Переводит текст в руны."""
    res = ""
    rune_counter = 0
    for s in text:
        rune = RUNE_TABLE.get(s)
        if rune is None:
            res += s
        elif s == " ":
            res += f" {rune.rune} "
            rune_counter = 0
        else:
            res += rune.rune
            rune_counter += 1

        if rune_counter == 2:  # noqa: PLR2004
            res += " "
            rune_counter = 0

    return res


def translate_to_text(rune_text: str) -> str:
    """Переводи руны в обычный текст."""
    res = ""
    rune_buffer = ""

    for s in rune_text:
        if s == " ":
            continue

        if rune_buffer == "":
            rune_buffer += s
            continue

        complex_rune = get_text(rune_buffer + s)
        simple_rune = get_text(rune_buffer)
        if complex_rune is not None:
            rune_buffer = ""
            res += complex_rune
            continue
        if simple_rune is not None:
            res += simple_rune
        else:
            res += rune_buffer

        rune_buffer = s

    if rune_buffer != "":
        simple_rune = get_text(rune_buffer)
        res += simple_rune if simple_rune is not None else rune_buffer

    return res


# определение команд
# ==================


@plugin.include
@arc.slash_command("rune", description="Перевод на рунический язык.")
async def rune_translate(
    ctx: ChioContext,
    text: arc.Option[str, arc.StrParams("Текст для перевода")],  # type: ignore
) -> None:
    """Переводит текст в рунический язык по словарю."""
    await ctx.respond(
        embed=hikari.Embed(
            title="📄 Переводчик",
            description=f"`{translate_to_rune(text)}`",
            color=hikari.Color(0x00FFCC),
        )
    )


@plugin.include
@arc.slash_command("unrune", description="Обратный перевод рунического текста.")
async def unrune_translate(
    ctx: ChioContext,
    text: arc.Option[str, arc.StrParams("Текст для перевода")],  # type: ignore
) -> None:
    """Расшифровывает рунический текст."""
    await ctx.respond(
        embed=hikari.Embed(
            title="📄 Переводчик",
            description=f"`{translate_to_text(text)}`",
            color=hikari.Color(0x00FFCC),
        )
    )


# Загрузчики и выгрузчики плагина
# ===============================


@arc.loader
def loader(client: ChioClient) -> None:
    """Действия при загрузке плагина."""
    client.add_plugin(plugin)
