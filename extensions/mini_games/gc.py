"""Сборщик мусора.

Первая игра, использующая библиотеку инвентаря.

Version: v0.0.4 (11)
Author: Milinuri Nirvalen
"""

from random import randint
from typing import NamedTuple

import arc
import hikari
import miru

from chioricord.client import ChioClient, ChioContext
from chioricord.plugin import ChioPlugin
from libs.inventory import Inventory, InventoryItem, ItemIndex

plugin = ChioPlugin("Gc")

_MAX_ENERGY = 5


class RareInfo(NamedTuple):
    """Информация о редкости предмета.

    - tier: Какого класса предмет.
    - icon: Иконочка для представления предмета.
    - chance: С каким шансом может выпасть предмет.
    - max_count: Максимальное количество предметов, которое может выпасть.
    """

    tier: int
    icon: str
    chance: int
    max_amount: int

    def __str__(self) -> str:
        """Преобразовать в строку."""
        return self.icon


DEFAULT_RARE = RareInfo(0, "🟤", 100, 7)
_RARES = [
    RareInfo(3, "🔵", 10, 1),
    RareInfo(2, "🟢", 20, 2),
    RareInfo(1, "⚪", 50, 3),
    RareInfo(0, "🟤", 100, 7),
]


def get_random_rare() -> RareInfo:
    """Получает случайную редкость для предмета по весам."""
    rand_num = randint(0, 101)
    for rare in _RARES:
        if rand_num < rare.chance:
            return rare
    return DEFAULT_RARE


class GameButton(miru.Button):
    """Игровое поле мусорки."""

    def __init__(self, index: int) -> None:
        super().__init__(label="🗑️", style=hikari.ButtonStyle.SECONDARY)
        self.index = index

        self.view: GCView

    async def callback(self, ctx: miru.ViewContext) -> None:
        """Действие при нажатии на кнопку."""
        if not self.view.validate_player(ctx.user):
            await ctx.respond(
                "Не трогайте меня пожалуйста ...", delete_after=10
            )
            return

        rare = await self.view.get_item(self.index)
        if rare is None:
            await ctx.edit_response(
                embed=self.view.stop_game(), components=None
            )
            return
        self.set_open(rare)

        game_over = await self.view.is_game_over()
        if game_over:
            await ctx.edit_response(
                embed=self.view.end_game_massage(), components=None
            )
            self.view.stop()
        else:
            await ctx.edit_response(
                embed=self.view.game_status(), components=self.view
            )

    def set_open(self, rare: RareInfo) -> None:
        """Помечает клетку как открытую."""
        self.disabled = True
        self.label = rare.icon


class GCView(miru.View):
    """Поле свалки."""

    def __init__(
        self,
        user: hikari.User,
        energy: int,
        index: ItemIndex,
        inventory: Inventory,
    ) -> None:
        super().__init__()
        self._user = user
        self._index = index
        self._inventory = inventory

        self._max_energy = energy
        self._energy = 0

        self._board: list[RareInfo] = []
        self._collected_items: list[InventoryItem] = []

        self.new_game()

    def new_game(self) -> None:
        """Начинает новую игру."""
        self._board.clear()
        self._collected_items.clear()
        self._energy = self._max_energy

        for x in range(25):
            self._board.append(get_random_rare())
            self.add_item(GameButton(x))

    def validate_player(self, user: hikari.User) -> bool:
        """проверяет что данный игрок может сделать ход."""
        return user == self._user

    async def get_item(self, index: int) -> RareInfo | None:
        """Получает предмет из поля."""
        self._energy -= 1
        rare = self._board[index]
        item = await self._index.get_random(rare.tier)
        if item is None:
            return None

        self._collected_items.append(
            InventoryItem(index=item, amount=randint(1, rare.max_amount))
        )
        return rare

    async def is_game_over(self) -> bool:
        """проверяет игру на завершение."""
        game_over_flag = self._energy <= 0
        if game_over_flag:
            for item in self._collected_items:
                await self._inventory.give(
                    user_id=self._user.id,
                    item_id=item.index.item_id,
                    amount=item.amount,
                )
            await self._inventory.commit()
        return game_over_flag

    def collected_items_status(self) -> str:
        """Сообщение собранных предметов."""
        if len(self._collected_items) == 0:
            return "Тут пока нет предметов"
        res = ""
        for item in self._collected_items:
            res += f"\n- {item.index.name} (x{item.amount})"
        return res

    def end_game_massage(self) -> hikari.Embed:
        """Сообщение о завершении игры."""
        return (
            hikari.Embed(
                title="🗑️ Поход окончен",
                description=(
                    "У вас больше не осталось сил, чтобы разбираться в горах "
                    "непереработанного мусора.\n"
                    "Самое время посмотреть что вы успели набрать."
                ),
                color=hikari.Color(0x8FF0A4),
            )
            .add_field(name="Находки", value=self.collected_items_status())
            .add_field(
                name="Энергия", value=f"{self._energy} / {self._max_energy}"
            )
        )

    def game_status(self) -> hikari.Embed:
        """Статус игры."""
        return (
            hikari.Embed(
                title="🗑️ Поход",
                description=(
                    "Перед вами большой простор где искать что-нибудь ценное.\n"
                    "Нажмите на пустое поле, чтобы узнать что там находится."
                ),
                color=hikari.Color(0x00CCFF),
            )
            .add_field(name="Находки", value=self.collected_items_status())
            .add_field(
                name="Энергия", value=f"{self._energy} / {self._max_energy}"
            )
        )

    def stop_game(self) -> hikari.Embed:
        """Завершает игру."""
        self.stop()
        return hikari.Embed(
            title="🗑️ Поход / Возникла проблема",
            description="При получении предмета возникла ошибка.",
            color=hikari.Color(0xFF00AA),
        )


# определение команд
# ==================


@plugin.include
@arc.slash_command("gc", description="Отправиться на свалку.")
async def collect_garbage(
    ctx: ChioContext,
    index: ItemIndex = arc.inject(),
    inventory: Inventory = arc.inject(),
    client: miru.Client = arc.inject(),
) -> None:
    """Начинает новых поход на свалку."""
    view = GCView(ctx.user, _MAX_ENERGY, index, inventory)
    await ctx.respond(view.game_status(), components=view)
    client.start_view(view)


# Загрузчики и выгрузчики плагина
# ===============================


@arc.loader
def loader(client: ChioClient) -> None:
    """Действия при загрузке плагина."""
    client.add_plugin(plugin)
