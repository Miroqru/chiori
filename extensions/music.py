"""Музыкальный плеер для Chiori.

Использует библиотеку hikari-ongaku для взаимодействия с lavalink.

Предоставляет
-------------

- /play <query>: Сыграть песню.
- /add <query>: Добавить песню в очередь.
- /pause: Поставить плеер на паузу/возобновить произведение.
- /queue: Очередь воспроизведения.
- /volume <1-100>: Установить громкость плеера.
- /skip [1]: Пропустить песни в очереди.
- /stop: Остановить воспроизведение.

Version: v2.0 (21)
Author: Milinuri Nirvalen
"""

import arc
import hikari
import ongaku
from loguru import logger
from ongaku.ext.injection import arc_ensure_player

from chioricord.config import PluginConfig, PluginConfigManager

plugin = arc.GatewayPlugin("Music")


class MusicConfig(PluginConfig):
    """Настройки для плагина музыки."""

    name: str = "miroq player"
    """Имя музыкальной сессии."""

    ssl: bool = False
    """Используется ли ssl (https) шифрование."""

    host: str = "127.0.0.1"
    """Хост, на котором работает плеер."""

    port: int = 2333
    """Порт, на котором работает плеер."""

    password: str = "you_shall_not_pass"
    """Пароль для подключения к плееру."""


# определение команд
# ==================


@plugin.include
@arc.slash_command("play", description="Сыграть песню.")
async def play_song(
    ctx: arc.GatewayContext,
    query: arc.Option[  # type: ignore
        str, arc.StrParams("Какую песню играть")
    ],
    ongaku_client: ongaku.Client = arc.inject(),
) -> None:
    """Играет песню в голосовом канале."""
    guild = ctx.get_guild()
    if guild is None or ctx.guild_id is None:
        raise arc.GuildOnlyError()

    state = guild.get_voice_state(ctx.author)
    if state is None or state.channel_id is None:
        await ctx.respond(
            "Вам бы в голосовой канал зайти, или где мне играть?",
            flags=hikari.MessageFlag.EPHEMERAL,
        )
        return

    res = await ongaku_client.rest.load_track(query)

    if res is None:
        await ctx.respond(
            "простите, я не нашла что мне играть.",
            flags=hikari.MessageFlag.EPHEMERAL,
        )
        return

    try:
        player = ongaku_client.fetch_player(ctx.guild_id)
    except ongaku.PlayerMissingError:
        player = ongaku_client.create_player(ctx.guild_id)

    player.add(res)

    if not player.connected:
        await player.connect(state.channel_id)

    # TODO: подробная информация о треке
    emb = hikari.Embed(description=f"Добавила: {res}")
    await player.play(requestor=ctx.author)
    await ctx.respond(emb)


@plugin.include
@arc.with_hook(arc_ensure_player)
@arc.slash_command("add", description="Добавить песни в очередь.")
async def add_songs(
    ctx: arc.GatewayContext,
    query: arc.Option[  # type: ignore
        str, arc.StrParams("Какую песню играть")
    ],
    ongaku_client: ongaku.Client = arc.inject(),
    player: ongaku.Player = arc.inject(),
) -> None:
    """Добавляет песни в очередь проигрывания."""
    res = await ongaku_client.rest.load_track(query)

    if res is None:
        await ctx.respond(
            "простите, я не нашла что мне играть.",
            flags=hikari.MessageFlag.EPHEMERAL,
        )
        return

    player.add(res)
    emb = hikari.Embed(description=f"Добавила: {res}")
    await ctx.respond(emb)


@plugin.include
@arc.with_hook(arc_ensure_player)
@arc.slash_command("pause", "Приостановить/возобновить воспроизведение.")
async def player_pause(
    ctx: arc.GatewayContext,
    player: ongaku.Player = arc.inject(),
) -> None:
    """Останавливает/возобновляет воспроизведение музыку."""
    await player.pause()

    if player.is_paused:
        await ctx.respond("Музыку приостановлена.")
    else:
        await ctx.respond("Музыка продолжается.")


@plugin.include
@arc.with_hook(arc_ensure_player)
@arc.slash_command("queue", "Очередь воспроизведения.")
async def player_queue(
    ctx: arc.GatewayContext,
    player: ongaku.Player = arc.inject(),
) -> None:
    """Очередь воспроизведения."""
    if len(player.queue) == 0:
        await ctx.respond("Очередь пуста. Играть нечего.")
        return

    emb = hikari.Embed(
        title="Очередь",
        description=f"Текущий трек: {player.queue[0]}",
    )

    for x in range(len(player.queue)):
        if x == 0:
            continue

        if x >= 25:  # noqa: PLR2004
            break

        track = player.queue[x]

        emb.add_field(track.info.title, track.info.author)

    await ctx.respond(emb)


@plugin.include
@arc.with_hook(arc_ensure_player)
@arc.slash_command("volume", "Установить громкость плеера.")
async def player_volume(
    ctx: arc.GatewayContext,
    volume: arc.Option[  # type: ignore
        int,
        arc.IntParams("Насколько кричать.", min=0, max=100),
    ],
    player: ongaku.Player = arc.inject(),
) -> None:
    """Устанавливает громкость для плеера."""
    await player.set_volume(volume)
    await ctx.respond(f"Сейчас я пою на {volume}/100 громкости")


@plugin.include
@arc.with_hook(arc_ensure_player)
@arc.slash_command("skip", "Пропустить песню.")
async def skip_command(
    ctx: arc.GatewayContext,
    amount: arc.Option[  # type: ignore
        int,
        arc.IntParams("Сколько песен пропустить (1)", min=1),
    ] = 1,
    player: ongaku.Player = arc.inject(),
) -> None:
    """Пропускает песни в очереди."""
    await player.skip(amount)
    await ctx.respond(f"{amount} песен было пропущено.")


@plugin.include
@arc.with_hook(arc_ensure_player)
@arc.slash_command("stop", "Остановить воспроизведение.")
async def stop_player(
    ctx: arc.GatewayContext,
    player: ongaku.Player = arc.inject(),
) -> None:
    """Останавливает воспроизведение в канале."""
    await player.disconnect()
    await ctx.respond("Successfully stopped the player.")


# Загрузчики и выгрузчики плагина
# ===============================


@arc.loader
def loader(client: arc.GatewayClient) -> None:
    """Действия при загрузке плагина."""
    client.add_plugin(plugin)
    cm = client.get_type_dependency(PluginConfigManager)
    cm.register("music", MusicConfig)
    config = cm.get_group("music", MusicConfig)

    logger.info("Create ongaku session")
    ongaku_client = ongaku.Client.from_arc(client)

    # ongaku_client = client.get_type_dependency(ongaku.Client)
    ongaku_client.create_session(
        name=config.name,
        ssl=config.ssl,
        host=config.host,
        port=config.port,
        password=config.password,
    )


@arc.unloader
def unloader(client: arc.GatewayClient) -> None:
    """Действия при выгрузке плагина."""
    client.remove_plugin(plugin)
