"""Регистр custom emoji.

Позволяет расширениям определять и использовать emoji, определённые в
глобальных настройках.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Unpack

from pydantic import ValidationError

from chiori.api.registry import RegisterModel, Registry, validation_error

if TYPE_CHECKING:
    from pydantic import ConfigDict

    from chiori.api.custom import Custom

logger = logging.getLogger(__name__)


class EmojiModel(RegisterModel, extra="allow"):
    """Базовая модель для определения набора emoji."""

    def __init_subclass__(cls, name: str, **kwargs: Unpack[ConfigDict]) -> None:
        """Позволяет определить имя модели."""
        super().__init_subclass__(**kwargs)
        if not name:
            raise ValueError("Model must have unique name")

        cls.__model_name__ = name


class EmojiRegistry(Registry[EmojiModel]):
    """Регистр custom emoji.

    Позволяет расширениям определять список custom emoji.
    И после использовать его.
    """

    def _load_proto(self, name: str, proto: type[EmojiModel], custom: Custom) -> None:
        logger.debug("Load emoji set %s", name)
        model = proto.model_validate(custom.emoji)
        self._models[name] = model
        self._client.set_type_dependency(proto, model)

    def load(self) -> None:
        """Загружает модели из их прототипов."""
        custom = self._client.custom
        fail_load: list[str] = []
        for name, proto in self._protos.items():
            try:
                self._load_proto(name, proto, custom)
            except ValidationError as e:
                validation_error(e)
                fail_load.append(name)

        if len(fail_load) > 0:
            logger.error("Failed to load some emoji sets:")
            for name in fail_load:
                logger.error("- %s", name)

        self._protos = {}
