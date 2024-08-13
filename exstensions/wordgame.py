"""Игра в слова."""

from pathlib import Path
import re
import json

import hikari
import arc
import miru

from loguru import logger


plugin = arc.GatewayPlugin("Wordgame")

def get_word(raw_word: str) -> str | None:
    match_word = re.match(r"[а-я]{2,}", raw_word.lower())
    if match_word is None:
        return None
    return match_word.group()


class WordGame:
    def __init__(
        self,
        last_user_id: int | None = None,
        last_word: str | None = None
    ):
        self.last_user = last_user_id
        self.last_word = last_word
        self.storage = None

    async def next_word(self, ctx: arc.GatewayContext, word: str) -> bool:
        new_word = get_word(word)
        if new_word is None:
            embed = hikari.Embed(
                title=f"Точно {word}?",
                description="Слово должно состоять как минимум из 2-х букв",
                color=hikari.Color(0xff0099)
            )
            await ctx.respond(embed=embed)
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

    def new_game_message(self) -> hikari.Embed:
        return hikari.Embed(
            title="Игра в слова / Начало",
            description=(
                f"Вы начинаете новую игру со слова **{self.last_word}**\n"
                f"Следующий игров говорит слово на букву {self.last_word[-1]}"
            ),
            color=hikari.Color(0x66ccff)
        ).add_field(
            name="Правила игры",
            value=(
                "- Новое слово начинается с последней буквы предыдущео.\n"
                "- Только существительные именительного падежа."
            )
        )

    def next_word_message(self, next_word: str) -> hikari.Embed:
        return hikari.Embed(
            title="Игра в слова",
            description=f"{self.last_word} -> **{next_word}**",
            color=hikari.Color(0x66ffcc)
        )

class GameStorage:
    def __init__(self, storage_file: Path):
        self.storage_file = storage_file
        self._games: dict[int, WordGame] = {}

    def connect(self):
        try:
            with open(self.storage_file) as f:
                json_games: dict[str, list[str, int]] = json.loads(f.read())
            games = {}
            for k, v in json_games.items():
                games[k] = WordGame(v[0], v[1])
            self._games = games
            logger.info("Word games loaded from file")
        except Exception as e:
            logger.error(e)

    def close(self):
        try:
            dump_games = {}
            for k, v in self._games.items():
                dump_games[k] = [v.last_user, v.last_word]
            with open(self.storage_file, "w") as f:
                f.write(json.dumps(dump_games))
            logger.info("Word games saved in file")
        except Exception as e:
            logger.error(e)

    def get(self, guild_id: int) -> WordGame:
        if guild_id in self._games:
            return self._games[guild_id]
        return WordGame()

    def set(self, guild_id: int, game: WordGame):
        self._games[guild_id] = game


GSTORAGE = GameStorage(Path("bot_data/word_game.json"))


# определение команд
# ==================

@plugin.include
@arc.slash_command("word", description="Сказать слово для игры в слова.")
async def nya_handler(
    ctx: arc.GatewayContext,
    word: arc.Option[str, arc.StrParams("Какое вы хотите сказать слово?")]
) -> None:
    if ctx.guild_id is None:
        return await ctx.respond("Вы не можете играть в одиночку.")

    game = GSTORAGE.get(str(ctx.guild_id))
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
