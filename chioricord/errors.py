"""Общий обработчик ошибок бота."""

from datetime import UTC, datetime

import arc
import hikari
from loguru import logger


async def client_error_handler(ctx: arc.GatewayContext, exc: Exception) -> None:
    """Отлавливаем исключение если что-то  пошло не по плану.

    К примеру это могут быть ошибки внутри обработчиков.
    Неправильно переданные команды.
    Если обработчики сами не реализуют обработчики ошибок, то все
    исключения будут попадать сюда.
    """
    if isinstance(exc, hikari.ForbiddenError):
        emb = hikari.Embed(
            title="⚠️ Недостаточно прав",
            description="Для выполнения данной команды.",
            color=hikari.Color(0xFF9966),
        )
        emb.add_field("status", f"[`{exc.status}`] {exc.message}")
        return

    try:
        raise exc
    except Exception as e:
        logger.exception(e)
        emb = hikari.Embed(
            title="⚡ Что-то пошло не так!",
            description=(
                "Во время выполнения команды..\n\n"
                f"`{type(e)}`: {e}\n\n"
                "🌱 Обратитесь в поддержку за помощью."
            ),
            color=hikari.Color(0xFF6699),
            timestamp=datetime.now(UTC),
        )
        await ctx.respond(emb)
