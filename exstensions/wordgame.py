"""Игра в слова.

Суть игры досаточно простая.
Первый участник называет слово.
Следующие участник наызвает слово на последную букву предыдущего.

Правила игры:
- Новое слово начинается с последней буквы предыдущего.
- Использовать только существительные единственного числа.
- Слова должны быть в единственном числе иминимальеного падежа.

Предоставляет
-------------

- /word <word>: Добавить новое слово в цепочку слов.

Version: v0.4.1 (14)
Author: Milinuri Nirvalen
"""

from time import time
from typing import NamedTuple
from pathlib import Path
import re
import json

import hikari
import arc
import miru

from loguru import logger


plugin = arc.GatewayPlugin("Wordgame")

# Общие правила используются при начале гры и если отправлено
# неправильное слово.
_GAME_RULES = (
    "- Новое слово начинается с последней буквы предыдущео.\n"
    "- Только существительные именительного падежа.\n"
    "- Слова должны быть в единственном числе именительного падежа.\n"
    "- Слова не должны повторояться."
)

# Описывает сколько должно пройти времени с последнго обновления
# чтобы после началась новая игра
# Используется чтобы не затягивать игры слишком надолго
#
# По умолчанию занчение утсановлено в 12 чаов
_START_NEW_GAME_AFTER = 43200


# Вспомогательные компоненты
# ==========================

def get_word(raw_word: str) -> str | None:
    """Получает слово из строки текста.

    Для поиска слова используется регулярное выражение.
    Извелкает слова более двух симовлов русского языка.
    При нахождении иного символа, поиск слова заканчивается.
    Если не удалось найти слово из строки, то возвращает None.

    :param raw_word: Строка с текстом, откуда нужно извлесь слово.
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
    else:
        return word[-1]


# Глвынй игровой класс
# ====================

class WordGame:
    """Представление игры в слова.

    Позводяет пользователям взаимодействаоть с текущей игрой.
    Например добавлять новое слово в цепочку.

    :param last_user_id: ID последнего пользователя, кто скзаал слово.
    :type last_user_id: int | None
    :param last_word: Последнее слово в цепочке.
    :type last_word: str | None
    """

    def __init__(
        self,
        last_user_id: int | None = None,
        last_word: str | None = None,
    ):
        self.last_user = last_user_id
        self.last_word = last_word

    def validate_word(self, ctx: arc.GatewayContext, word: str) -> str | None:
        """Проверяет строку на корректность чтобы его добавить.

        Пробует извлечь слово из строки.
        После проверяет, не совпадают ли пользователи, кто полседний
        раз отправлял слово в цепочку.
        Также проверяет, чтобы первая буква нового слова совпадала с
        последней буквой предыдущего слова.

        :param ctx: Контекст сообщения, кто отправил новое слово.
        :type ctx: arc.GatewayContext
        :param word: Строка, которую необходимо проверить.
        :type word: str
        :return: Новое слово в цепочку, или None, если не подходит.
        :rtype: str | None
        """
        word = get_word(word)
        if word is None:
            return None

        if self.last_user is not None:
            if word == self.last_word:
                return None

            if ctx.user.id == self.last_user:
                return None

            last_letter = get_last_letter(self.last_word)
            if last_letter != word[0]:
                return None
        return word

    async def next_word(self, ctx: arc.GatewayContext, word: str) -> bool:
        """Доабвлеяет новое слво в цеопчку.

        Внутри проводит проверку что слово может быть доабвлено в цепь.
        Если нельзя доавбить новое слово, то отправляет сообщение с
        ошибкой и возвращает Fasle.
        Если доавбенное слово было первым в цепочке, то отправляет
        сообщение об успешном начале новой игры.
        Иначе же просто отпарвялет сообщение что доабвлено новое слово.
        При успешном добавлении нового слова в цеопчку возвращет True.

        :param ctx: Контекст команды, кто добавил новое слово и когда.
        :type ctx: arc.GatewayContext
        :param word: Слово, которое пользователь собирается добавить.
        :type word: str
        :return: Статус довбления нового слова.
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
        оно не может быть доабвлено в цепочку слов.
        Также сообщает правила игры, чтобы пользователь понимал
        примеруню причну, почему его слово не было добавлено в
        цепочку слов.

        :param word: Оригинальное слово, которое не добавлено.
        :type word: str
        :return: Сообщенеи об ошибке добавления нового слова.
        :rtype: hikari.Embed
        """
        return hikari.Embed(
            title=f"Точно {word}?",
            description=(
                "Вероятно вы где-то ошиблись, а может сейчас не ваш ход?\n"
                f"Последнее слово: {self.last_word}"
            ),
            color=hikari.Color(0xff0099)
        ).add_field(
            name="Правила игры",
            value=_GAME_RULES
        )

    def new_game_message(self) -> hikari.Embed:
        """Сообщенеи на случай начала новой игры.

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
            color=hikari.Color(0x66ccff)
        ).add_field(
            name="Правила игры",
            value=_GAME_RULES
        )

    def next_word_message(self, next_word: str) -> hikari.Embed:
        """Сообщенеи о добавлении нового слова.

        Отпрвялется, когда пользователь успешно добавляет слово в
        цепочку слов.

        :param next_word: Новое слово в цепочке.
        :type next_word: str
        :return: Экземпляр сообщения, которыое будет отпрвелно.
        :rtype: hikari.Embed
        """
        return hikari.Embed(
            title="Игра в слова",
            description=f"{self.last_word} -> **{next_word}**",
            color=hikari.Color(0x66ffcc)
        )


class GameData(NamedTuple):
    """Описывает даныне игры в хранилище.

    :param game: Экземпляр активной игры.
    :type game: Wordgame
    :param last_update: Время последнего сохраенрия игры.
    :type last_update: int
    """

    game: WordGame
    last_update: int

class GameStorage:
    """Хранилище сессия игры.

    Сохраняет данные игры в формате ключ как сервер id и значение как
    экземпляр игры.
    Позвоялет сохранять данные игры в оперативную память.
    А также загружать и выгружать их из файла в формате json.

    :param path: Путь к файлу куда сохранять данные.
    :type path: Path
    """
    def __init__(self, storage_file: Path):
        self.storage_file = storage_file
        self._games: dict[int, GameData] = {}


    # Работаем с диском
    # =================

    def connect(self):
        """Подключает хранилище.

        Загружает данные из файла и преобразует в словарь эземпляров
        WordGame.
        Жанные хранятся в формате json.

        .. code-block:: json

            {
                // server id: [user_id: int, last_word: str]
                "1232313" [3123123, "слово"]
            }
        """

        try:
            with open(self.storage_file) as f:
                json_games: dict[str, list[str, int]] = json.loads(f.read())
            games = {}
            for k, v in json_games.items():
                games[k] = GameData(
                    game=WordGame(v[0], v[1]),
                    last_update=x[2]
                )
            self._games = games
            logger.info("Word games loaded from file")
        except Exception as e:
            logger.error(e)

    def close(self) -> None:
        """Закрывает соединение с хранилишем.

        Записывает локальные данные из оперативнйо памяти на диск.
        Для записи данных используется формат json.

        .. code-block:: json

            {
                // server id: [user_id: int, last_word: str]
                "1232313" [3123123, "слово"]
            }
        """
        try:
            dump_games = {}
            for k, v in self._games.items():
                dump_games[k] = [
                    v.game.last_user,
                    v.game.last_word,
                    v.last_update
                ]
            with open(self.storage_file, "w") as f:
                f.write(json.dumps(dump_games, ensure_ascii=False))
            logger.info("Word games saved in file")
            self._games = {}
        except Exception as e:
            logger.error(e)


    # Работаем с оперативной памятиью
    # ===============================

    def get(self, guild_id: int) -> WordGame:
        """Получает жкземпляр игры по id сервера.

        Если не удалось найти игру,

        :param guild_id: ID сервера чтобы получить игру в слова.
        :type guild_id: int
        :return: Экземпляр игры в слова.
        :rtype: WordGame
        """
        if guild_id in self._games:
            game_data = self._games[guild_id]
            # Вероятно будет несколько затратноузнавать время
            if game_data.last_update > 0 and (
                int(time())-game_data.last_update > _START_NEW_GAME_AFTER
            ):
                return WordGame()
            return self._games[guild_id].game
        return WordGame()

    def set(self, guild_id: int, game: WordGame):
        """Записывает экземпляр игры в хранилище.

        Используется чтобы осхранить результаты игры.

        :param guild_id: id дискорд сервера как ключ для словаря.
        :type guild_id: int
        :param game: Экземпляр текушей игры в слова.
        :type game: WordGame
        """
        self._games[guild_id] = GameData(game, int(time()))

# Создаём одно глобальное хранилище для всего плагина
GSTORAGE = GameStorage(Path("bot_data/word_game.json"))


# определение команд
# ==================

@plugin.include
@arc.slash_command("word", description="Сказать слово для игры в слова.")
async def word_handler(
    ctx: arc.GatewayContext,
    word: arc.Option[str, arc.StrParams("Какое вы хотите сказать слово?")]
) -> None:
    """Добавляет новое слово для игры в слова.

    Если это вервое слово на сервере, то начинается игра.
    Все последющие слова будут доабвелны в цепочку.
    После каждого удачного слова в цепочке происходит сохранение в
    оперативную память.
    """
    if ctx.guild_id is None:
        return await ctx.respond("Вы не можете играть в одиночку.")

    game = GSTORAGE.get(str(ctx.guild_id))
    status = await game.next_word(ctx, word)
    if status:
        GSTORAGE.set(str(ctx.guild_id), game)


@plugin.include
@arc.slash_command(
    "mewword",
    description="Начинает новую игру в слова.",
    # обычно прпва удалять сообщения есть у помошников и выше
    default_permissions=hikari.Permissions.MANAGE_MESSAGES
)
async def word_handler(
    ctx: arc.GatewayContext,
    word: arc.Option[str, arc.StrParams("Какое вы хотите сказать слово?")]
) -> None:
    """Принудительно начинает новую игру в слова.

    Можно использовать, чотбы очистить результаты игры.
    """
    if ctx.guild_id is None:
        return await ctx.respond("Вы не можете играть в одиночку.")

    game = WordGame()
    status = await game.next_word(ctx, word)
    if status:
        GSTORAGE.set(str(ctx.guild_id), game)



# Загрузчики и выгрузчики плагина
# ===============================


@plugin.listen(arc.events.StartedEvent)
async def connect(event: arc.events.StartedEvent):
    """Подключаемся к базам данных при запуске бота."""
    logger.info("Connect to wordgames storage")
    GSTORAGE.connect()


@plugin.listen(arc.events.StoppingEvent)
async def disconnect(event: arc.events.StoppingEvent):
    """Время отключаться от баз данных, вместе с отключением бота."""
    logger.info("Close connect to wordgames storage")
    GSTORAGE.close()


@arc.loader
def loader(client: arc.GatewayClient) -> None:
    """Действия при загрузке плагина."""
    client.add_plugin(plugin)

@arc.unloader
def unloader(client: arc.GatewayClient) -> None:
    """Действия при выгрузке плагина."""
    client.remove_plugin(plugin)
