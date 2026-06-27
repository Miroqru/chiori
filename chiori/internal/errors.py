"""Общий обработчик ошибок.

Обрабатывает корневые ошибки, если они не были перехвачены на уровне расширений.
Всякую неожиданную ошибку он отправляет в событии UnexpectedError.
"""

import hikari
from loguru import logger

from chiori.client import ChioContext
from chiori.events import UnexpectedError


def forbid_message(exc: hikari.ForbiddenError) -> hikari.Embed:
    logger.error(exc)
    emb = hikari.Embed(
        title="⚠️ Недостаточно прав",
        description=(
            "Я не могу получить доступ к указанному ресурсу.\n"
            "Возможно у меня для этого недостаточно прав.\n"
            "Или быть может такой функционал не входит в мои обязанности.\n\n"
        ),
        color=hikari.Color(0xFF9966),
    )
    emb.add_field("🔌 Подробности", f"`[{exc.code}]: {exc.status}`\n> {exc.message}")
    return emb


def _error_message(ctx: ChioContext, exc: Exception) -> hikari.Embed:
    logger.exception(exc)
    emb = hikari.Embed(
        title="⚡ Ой, прошу-прощения",
        description=(
            "Произошла небольшая ошибочка в работе.\n"
            "Вы можете попробовать воспользоваться командой позже.\n"
            "🌱 Если проблема сохранится, обратитесь за помощью."
        ),
        color=hikari.Color(0xFF6699),
        timestamp=ctx.interaction.created_at,
    )
    emb.add_field("🔌 Подробности", f"`{type(exc)}`:\n> {exc}")
    return emb


async def client_error_handler(ctx: ChioContext, exc: Exception) -> None:
    """Отлавливаем исключение если что-то  пошло не по плану.

    К примеру это могут быть ошибки внутри обработчиков.
    Неправильно переданные команды.
    Если обработчики сами не реализуют обработчики ошибок, то все
    исключения будут попадать сюда.
    """
    # Оставим это как есть.
    # Потому что больше нигде не планируется использовать обработку ошибок.
    # Так что нет смысла давать доступ к словарю ошибок.
    if message := ctx.client._errors.get(type(exc)):  # noqa: SLF001
        await ctx.respond(message(exc))
        return

    # Такой метод прямым текстом написан в документации
    # Это нужно чтобы отловить и обработать любую ошибку.
    try:
        raise exc  # noqa: TRY301
    except Exception as e:  # noqa: BLE001
        await ctx.respond(_error_message(ctx, e))
        ctx.client.app.event_manager.dispatch(UnexpectedError(ctx, exc))
