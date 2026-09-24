"""Общий обработчик ошибок.

Обрабатывает корневые ошибки, если они не были перехвачены на уровне расширений.
Для обработки ошибок во время выполнения команды лучше использовать:
arc.CommandErrorEvent.
"""

import arc
import hikari

from chiori.client import ChioClient, ChioContext
from chiori.log import logger


def _guild_only(exc: arc.GuildOnlyError) -> hikari.Embed:
    logger.warning(exc)
    return hikari.Embed(
        title="👀 Секундочку",
        description=(
            "Это команда работает только на серверах.\n"
            "Вы не сможете выполнить её в личных сообщениях со мной.\n"
        ),
        color=0xFFCC66,
    )


def _forbid_message(exc: hikari.ForbiddenError) -> hikari.Embed:
    logger.error(exc)
    emb = hikari.Embed(
        title="⚠️ Недостаточно прав",
        description=(
            "Я не могу получить доступ к указанному ресурсу.\n"
            "Возможно у меня для этого недостаточно прав.\n"
            "Или быть может такой функционал не входит в мои обязанности.\n\n"
        ),
        color=0xFF9966,
    )
    emb.add_field("🔌 Подробности", f"`[{exc.code}]: {exc.status}`\n> {exc.message}")
    return emb


def _owner_only(exc: arc.NotOwnerError) -> hikari.Embed:
    logger.warning(exc)
    return hikari.Embed(
        title="👀 Подождите-ка",
        description=(
            "Эту команду может выполнить только мой хозяин.\n"
            "Я конечно не знаю как вы узнали о её существовании...\n"
            "Но пожалуйста больше не трогайте её, у вас не получится.\n"
        ),
        color=0xFF6699,
    )


def _error_message(ctx: ChioContext, exc: Exception) -> hikari.Embed:
    logger.exception(exc)
    emb = hikari.Embed(
        title="⚡ Ой, прошу-прощения",
        description=(
            "Произошла небольшая ошибочка в работе.\n"
            "Вы можете попробовать воспользоваться командой позже.\n"
            "🌱 Если проблема сохранится, обратитесь за помощью."
        ),
        color=0xFF6699,
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


def setup_errors(client: ChioClient) -> None:
    """Подключает обработчик стандартных ошибок к клиенту."""
    logger.debug("Setup error handler")
    client.set_error_handler(client_error_handler)

    client.register_error(hikari.ForbiddenError, _forbid_message)
    client.register_error(arc.GuildOnlyError, _guild_only)
    client.register_error(arc.NotOwnerError, _owner_only)
