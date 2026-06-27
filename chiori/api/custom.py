"""Стилизация Шиори.

Предоставляет настройки по изменению стиля бота.
Настройки стиля используются между расширениями.
"""

import hikari
from pydantic import BaseModel, ConfigDict

from chiori.api.config import PluginConfig


class CustomModel(BaseModel):
    """Модель для настроек."""

    model_config = ConfigDict(extra="forbid", frozen=True)


# FIXME: Исправить тип цвета на hikari.Color
class CustomColors(CustomModel):
    """Палитра цветов.

    Предоставляют общий набор цветов для сообщений.
    Используется для стандартизации общего стиля.
    Все цвета представлены как числа в hex формате.
    """

    primary: int
    """Основной цвет. Используется по умолчанию."""

    secondary: int
    """Вторичный цвет. Чаще всего используется для подмен."""

    disabled: int
    """Приглушённый цвет."""

    accent: int
    """Цвет акцентного сообщения."""

    info: int
    """Цвет информационного сообщений."""

    success: int
    """Цвет успешно выполненного сообщения."""

    warning: int
    """Цвет предупреждающего сообщения."""

    error: int
    """Цвет сообщения с ошибкой."""


# FIXME: Исправить тип на hikari.ActivityType
class CustomActivity(CustomModel):
    """Активность Шиори.

    Отображается во время работы в статусе и профиле Discord.
    """

    name: str
    """Название активности."""

    state: str | None = None
    """Состояние активности.

    Может предоставлять больше информации об активности.
    """

    url: str | None = None
    """Ссылка на активность.

    Актуально только если активность streaming.
    """

    type: int
    """Тип активности."""

    @property
    def activity(self) -> hikari.Activity:
        """Возвращает представление активности для Шиори."""
        return hikari.Activity(
            name=self.name, state=self.state, url=self.url, type=self.type
        )


type EmojiID = str


class Custom(PluginConfig, config="custom"):
    """Настройки оформления.

    Представляют общие настройки по оформлению бота.
    """

    name: str = "Chiori"
    """Отображаемое имя бота."""

    desc: str = "Милая горничная для нашего сервера."
    """Краткое описание бота."""

    activity: CustomActivity
    """Активность Шиори в статусе и профиле."""

    color: CustomColors
    """Палитра цветов.

    Используется для предоставления стандартных цветов для Embed сообщений.
    """

    emoji: dict[str, EmojiID | dict[str, EmojiID]]
    """Индекс custom emoji для использования."""
