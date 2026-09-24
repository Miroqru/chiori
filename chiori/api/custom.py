"""Стилизация Шиори.

Предоставляет настройки по изменению стиля бота.
Настройки стиля используются между расширениями.
"""

from typing import Annotated

import hikari
from pydantic import BaseModel, BeforeValidator, ConfigDict

from chiori.api.config import PluginConfig

# Специальные типы для проверки
Color = Annotated[hikari.Color, BeforeValidator(hikari.Color)]
"""Представление цвета.

Записывается в формате 0xFFFFFF.
"""

ActivityType = Annotated[hikari.ActivityType, BeforeValidator(hikari.ActivityType)]
"""Тип активности в Rich presence."""

Status = Annotated[hikari.Status, BeforeValidator(hikari.Status)]
"""Статус участник."""

# Модели
# ======


class CustomModel(BaseModel):
    """Модель для настроек."""

    model_config = ConfigDict(extra="forbid", frozen=True, arbitrary_types_allowed=True)


class CustomColors(CustomModel):
    """Палитра цветов.

    Предоставляют общий набор цветов для сообщений.
    Используется для стандартизации общего стиля.
    Все цвета представлены как числа в hex формате.
    """

    primary: Color
    """Основной цвет. Используется по умолчанию."""

    secondary: Color
    """Вторичный цвет. Чаще всего используется для подмен."""

    disabled: Color
    """Приглушённый цвет."""

    accent: Color
    """Цвет акцентного сообщения."""

    info: Color
    """Цвет информационного сообщений."""

    success: Color
    """Цвет успешно выполненного сообщения."""

    warning: Color
    """Цвет предупреждающего сообщения."""

    error: Color
    """Цвет сообщения с ошибкой."""


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

    type: ActivityType
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

    status: Status
    """Статус бота при запуске."""

    color: CustomColors
    """Палитра цветов.

    Используется для предоставления стандартных цветов для Embed сообщений.
    """

    emoji: dict[str, EmojiID | dict[str, EmojiID]]
    """Индекс custom emoji для использования."""

    model_config = ConfigDict(extra="forbid", frozen=True, arbitrary_types_allowed=True)
