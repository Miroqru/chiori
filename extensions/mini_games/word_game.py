"""Игра в слова.

Суть игры достаточно простая.
Первый участник называет слово.
Следующие участник называет слово на последнюю букву предыдущего.

Правила игры:
- Новое слово начинается с последней буквы предыдущего.
- Использовать только существительные единственного числа.
- Слова должны быть в единственном числе именительного падежа.

Version: v0.4.4 (21)
Author: Milinuri Nirvalen
"""

import json
import re
from pathlib import Path
from time import time
from typing import NamedTuple

import arc
import hikari
from loguru import logger

from chioricord.client import ChioClient, ChioContext
from chioricord.plugin import ChioPlugin

plugin = ChioPlugin("Words")

# Общие правила используются при начале гры и если отправлено
# неправильное слово.
_GAME_RULES = (
    "- Новое слово начинается с последней буквы предыдущего.\n"
    "- Только существительные именительного падежа.\n"
    "- Слова должны быть в единственном числе именительного падежа.\n"
    "- Слова не должны повторяться."
)

# Описывает сколько должно пройти времени с последнего обновления
# чтобы после началась новая игра
# Используется чтобы не затягивать игры слишком надолго
#
# По умолчанию значение установлено в 12 часов
_START_NEW_GAME_AFTER = 43200


# Вспомогательные компоненты
# ==========================


def get_word(raw_word: str) -> str | None:
    """Получает слово из строки текста.

    Для поиска слова используется регулярное выражение.
    Извлекает слова более двух символов русского языка.
    При нахождении иного символа, поиск слова заканчивается.
    Если не удалось найти слово из строки, то возвращает None.

    :param raw_word: Строка с текстом, откуда нужно взялось слово.
    :type raw_word: str
    :return: Полученное слово или None, если не удалось извлечь.
    :rtype: str | None
    """
    match_word = re.match(r"[а-я]{2,}", raw_word.lower())
    if match_word is None:
        return None
    return match_word.group()


def get_last_letter(word: str) -> str:
    """Получает последний символ.

    Пропускает те, на которые нельзя образовать новое слово.
    """
    if word[-1] in ("ь", "ъ", "ы"):
        return word[-2]
    return word[-1]


# Главный игровой класс
# ====================


class Word(NamedTuple):
    """Одно слово для цепочки слов.

    помимо самого слова, запоминается пользователь, который его сказал.

    :param text: Текст слова для запоминания.
    :type text: str
    :param user_id: Кто добавил это слово в цепочку.
    :type user_id: int
    """

    text: str
    user_id: int


class WordGame:
    """Представление игры в слова.

    Позволяет пользователям взаимодействовать с текущей игрой.
    Например добавлять новое слово в цепочку.

    :param last_user_id: ID последнего пользователя, кто сказал слово.
    :type last_user_id: int | None
    :param last_word: Последнее слово в цепочке.
    :type last_word: str | None
    """

    def __init__(
        self,
        last_user_id: int | None = None,
        last_word: str | None = None,
        word_chain: list[Word] | None = None,
    ) -> None:
        self.last_user = last_user_id
        self.last_word = last_word
        self.word_chain = word_chain or []

    def search_word(self, word: str) -> Word | None:
        """Производит поиск слова в цепочке слов.

        Это используется чтобы предотвратить повтор слов.
        Если слово не было найдено в цепочке, то возвращает None.

        :param word: Слово для поиска в цепочке слов.
        :type word: str
        :return: Слово в цепочке, если было найдено, иначе None.
        :rtype: Word | None
        """
        for word_link in self.word_chain:
            if word == word_link.text:
                return word_link
        return None

    def validate_word(self, ctx: ChioContext, word: str) -> str | None:
        """Проверяет строку на корректность чтобы его добавить.

        Пробует извлечь слово из строки.
        После проверяет, не совпадают ли пользователи, кто последний
        раз отправлял слово в цепочку.
        Также проверяет, чтобы первая буква нового слова совпадала с
        последней буквой предыдущего слова.

        :param ctx: Контекст сообщения, кто отправил новое слово.
        :type ctx: ChioContext
        :param word: Строка, которую необходимо проверить.
        :type word: str
        :return: Новое слово в цепочку, или None, если не подходит.
        :rtype: str | None
        """
        clear_word = get_word(word)
        if clear_word is None:
            return None

        if self.last_user is not None:
            if clear_word == self.last_word:
                return None

            if ctx.user.id == self.last_user:
                return None

            word_link = self.search_word(word)
            if word_link is not None:
                return None

            last_letter = get_last_letter(self.last_word)
            if last_letter != word[0]:
                return None
        return word

    async def next_word(self, ctx: ChioContext, word: str) -> bool:
        """Добавляет новое слово в цепочку.

        Внутри проводит проверку что слово может быть добавлено в цепь.
        Если нельзя добавить новое слово, то отправляет сообщение с
        ошибкой и возвращает False.
        Если добавленное слово было первым в цепочке, то отправляет
        сообщение об успешном начале новой игры.
        Иначе же просто отправляет сообщение что добавлено новое слово.
        При успешном добавлении нового слова в цепочку возвращает True.

        :param ctx: Контекст команды, кто добавил новое слово и когда.
        :type ctx: ChioContext
        :param word: Слово, которое пользователь собирается добавить.
        :type word: str
        :return: Статус добавление нового слова.
        :rtype: bool
        """
        new_word = self.validate_word(ctx, word)
        if new_word is None:
            await ctx.respond(embed=self.error_message(word), delete_after=10)
            return False

        if self.last_word is None:
            self.last_word = new_word
            embed = self.new_game_message()
        else:
            self.word_chain.append(Word(self.last_word, self.last_user))
            embed = self.next_word_message(new_word)
            self.last_word = new_word

        self.last_user = ctx.user.id
        await ctx.respond(embed=embed)
        return True

    # Методы для получения сообщения
    # ==============================

    def error_message(self, word: str) -> hikari.Embed:
        """Сообщение о неправильном слове.

        Если введённое пользователем содержит ошибку, из-за чего
        оно не может быть добавлено в цепочку слов.
        Также сообщает правила игры, чтобы пользователь понимал
        примерную причину, почему его слово не было добавлено в
        цепочку слов.

        :param word: Оригинальное слово, которое не добавлено.
        :type word: str
        :return: Сообщение об ошибке добавления нового слова.
        :rtype: hikari.Embed
        """
        return hikari.Embed(
            title=f"Точно {word}?",
            description=(
                "Вероятно вы где-то ошиблись, а может сейчас не ваш ход?\n"
                f"Последнее слово: {self.last_word}"
            ),
            color=hikari.Color(0xFF0099),
        ).add_field(name="Правила игры", value=_GAME_RULES)

    def new_game_message(self) -> hikari.Embed:
        """сообщение на случай начала новой игры.

        Сообщает всем, что началась новая игра.
        Сообщает первое слово, а также правила игры.

        :return: Сообщение о начале новой игры.
        :rtype: hikari.Embed
        """
        last_letter = f"`{get_last_letter(self.last_word)}`"
        return hikari.Embed(
            title="Игра в слова / Начало",
            description=(
                f"Вы начинаете новую игру со слова **{self.last_word}**\n"
                f"Следующий игрок говорит слово на букву {last_letter}.\n"
                f"Игра начнётся с начала после 12 часов молчания."
            ),
            color=hikari.Color(0x66CCFF),
        ).add_field(name="Правила игры", value=_GAME_RULES)

    def next_word_message(self, next_word: str) -> hikari.Embed:
        """Сообщение о добавлении нового слова.

        Отправляется, когда пользователь успешно добавляет слово в
        цепочку слов.

        :param next_word: Новое слово в цепочке.
        :type next_word: str
        :return: Экземпляр сообщения, которое будет отправлено.
        :rtype: hikari.Embed
        """
        return hikari.Embed(
            title="Игра в слова",
            description=f"{self.last_word} -> **{next_word}**",
            color=hikari.Color(0x66FFCC),
        )


class GameData(NamedTuple):
    """Описывает данные игры в хранилище."""

    game: WordGame
    last_update: int


class GameStorage:
    """Хранилище сессия игры.

    Сохраняет данные игры в формате ключ как сервер id и значение как
    экземпляр игры.
    Позволяет сохранять данные игры в оперативную память.
    А также загружать и выгружать их из файла в формате json.

    :param path: Путь к файлу куда сохранять данные.
    :type path: Path
    """

    def __init__(self, storage_file: Path) -> None:
        self.storage_file = storage_file
        self._games: dict[int, GameData] = {}

    # Работаем с диском
    # =================

    def _load_word_chain(self, json_list: list[tuple[str, int]]) -> list[Word]:
        word_chain = []
        for word in json_list:
            word_chain.append(Word(word[0], word[1]))
        return word_chain

    def _dump_word_chain(self, word_chain: list[Word]) -> list[tuple[str, int]]:
        json_list: list[tuple[str, int]] = []
        for word in word_chain:
            json_list.append((word.text, word.user_id))
        return json_list

    def connect(self) -> None:
        """Подключает хранилище.

        Загружает данные из файла и преобразует в словарь экземпляров
        WordGame.
        Данные хранятся в формате json.

        .. code-block:: json

            {
                // server id: [user_id: int, last_word: str]
                "1232313": [
                    3123123, // id последнего кто отправил слово
                    "слово", // текст последнего слова
                    [ ... ], // вся последующая цепочка слов
                    17934133, // UNIXtime последнего обновления
                ]
            }
        """
        try:
            with open(self.storage_file) as f:
                json_games: dict[int, list] = json.loads(f.read())
            games = {}
            for k, v in json_games.items():
                games[k] = GameData(
                    game=WordGame(v[0], v[1], self._load_word_chain(v[2])),
                    last_update=v[3],
                )
            self._games = games
            logger.info("Word games loaded from file")
        except Exception as e:
            logger.error(e)

    def close(self) -> None:
        """Закрывает соединение с хранилищем.

        Записывает локальные данные из оперативной памяти на диск.
        Для записи данных используется формат json.

        .. code-block:: json

            {
                // server id: [user_id: int, last_word: str]
                "1232313": [
                    3123123, // id последнего кто отправил слово
                    "слово", // текст последнего слова
                    [ ... ], // вся последующая цепочка слов
                    17934133, // UNIXtime последнего обновления
                ]
            }
        """
        try:
            dump_games = {}
            for k, v in self._games.items():
                # Да-да, это просто прекрасный способ описать данные
                dump_games[k] = [
                    v.game.last_user,
                    v.game.last_word,
                    self._dump_word_chain(v.game.word_chain),
                    v.last_update,
                ]
            with open(self.storage_file, "w") as f:
                f.write(json.dumps(dump_games, ensure_ascii=False))
            logger.info("Word games saved in file")
            self._games = {}
        except Exception as e:
            logger.error(e)

    # Работаем с оперативной памятью
    # ==============================

    def get(self, guild_id: int) -> WordGame:
        """Получает экземпляр игры по id сервера.

        Если не удалось найти игру,

        :param guild_id: ID сервера чтобы получить игру в слова.
        :type guild_id: int
        :return: Экземпляр игры в слова.
        :rtype: WordGame
        """
        if guild_id in self._games:
            game_data = self._games[guild_id]
            # Вероятно будет несколько затратно узнавать время
            if game_data.last_update > 0 and (
                int(time()) - game_data.last_update > _START_NEW_GAME_AFTER
            ):
                return WordGame()
            return self._games[guild_id].game
        return WordGame()

    def set(self, guild_id: int, game: WordGame) -> None:
        """Записывает экземпляр игры в хранилище.

        Используется чтобы сохранить результаты игры.

        :param guild_id: id дискорд сервера как ключ для словаря.
        :type guild_id: int
        :param game: Экземпляр текущей игры в слова.
        :type game: WordGame
        """
        self._games[guild_id] = GameData(game, int(time()))


# Создаём одно глобальное хранилище для всего плагина
# TODO: Начать использовать конфиг
GLOBAL_STORAGE = GameStorage(Path("bot_data/word_game.json"))


# определение команд
# ==================


@plugin.include
@arc.slash_command("word", description="Сказать слово для игры в слова.")
async def word_handler(
    ctx: ChioContext,
    word: arc.Option[str, arc.StrParams("Какое вы хотите сказать слово?")],
) -> None:
    """Добавляет новое слово для игры в слова.

    Если это верное слово на сервере, то начинается игра.
    Все последующие слова будут добавлены в цепочку.
    После каждого удачного слова в цепочке происходит сохранение в
    оперативную память.
    """
    if ctx.guild_id is None:
        await ctx.respond("Вы не можете играть в одиночку.")
        return

    game = GLOBAL_STORAGE.get(ctx.guild_id)
    status = await game.next_word(ctx, word)
    if status:
        GLOBAL_STORAGE.set(ctx.guild_id, game)


@plugin.include
@arc.slash_command(
    "mewword",
    description="Новая игру в слова.",
    # обычно права удалять сообщения есть у помощника и выше
    default_permissions=hikari.Permissions.MANAGE_MESSAGES,
)
async def new_word_game(
    ctx: ChioContext,
    word: arc.Option[str, arc.StrParams("Какое вы хотите сказать слово?")],
) -> None:
    """Принудительно начинает новую игру в слова.

    Можно использовать, чтобы очистить результаты игры.
    """
    if ctx.guild_id is None:
        await ctx.respond("Вы не можете играть в одиночку.")
        return

    game = WordGame()
    status = await game.next_word(ctx, word)
    if status:
        GLOBAL_STORAGE.set(ctx.guild_id, game)


# Загрузчики и выгрузчики плагина
# ===============================


@plugin.listen(arc.events.StartedEvent)
async def connect(event: arc.StartedEvent[ChioClient]) -> None:
    """Подключаемся к базам данных при запуске бота."""
    logger.info("Connect to word games storage")
    GLOBAL_STORAGE.connect()


@plugin.listen(arc.events.StoppingEvent)
async def disconnect(event: arc.StoppingEvent[ChioClient]) -> None:
    """Время отключаться от баз данных, вместе с отключением бота."""
    logger.info("Close connect to word games storage")
    GLOBAL_STORAGE.close()


@arc.loader
def loader(client: ChioClient) -> None:
    """Действия при загрузке плагина."""
    client.add_plugin(plugin)
