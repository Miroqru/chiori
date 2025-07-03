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

from collections.abc import Sequence

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


QueryTrack = ongaku.Playlist | Sequence[ongaku.Track] | ongaku.Track

_MAX_FIELDS = 25


def format_time(milliseconds: int) -> str:
    """Преобразует количество миллисекунд в строку времени."""
    days, r = divmod(milliseconds // 1000, 86400)
    hours, r = divmod(r, 3600)
    minutes, seconds = divmod(r, 60)

    if days > 0:
        return f"{days}:{hours:02d}:{minutes:02d}:{seconds:02d}"

    elif hours > 0:
        return f"{days * 24 + hours}:{minutes:02d}:{seconds:02d}"

    return f"{(days * 24 + hours) * 60 + minutes}:{seconds:02d}"


def track_status(track: ongaku.Track) -> str:
    """Возвращает краткую информацию о треке для плейлиста."""
    if track.info.is_stream:
        stream_emoji = "📻 "
    else:
        stream_emoji = ""

    return (
        f"{stream_emoji}{track.info.author} "
        f"(`{format_time(track.info.length)}`)"
    )


def track_embed(track: ongaku.Track, requestor: hikari.User) -> hikari.Embed:
    """Описание конкретного трека."""
    if track.info.is_stream:
        color = hikari.Color(0xCC66FF)
    else:
        color = hikari.Color(0x66CCFF)

    emb = hikari.Embed(
        title=track.info.title,
        description=(
            f"Автор: {track.info.author}\n"
            f"Длительность: `{format_time(track.info.length)}`\n"
            f"Начало: `{format_time(track.info.position)}`\n"
        ),
        url=track.info.uri,
        color=color,
    )
    emb.add_field("Добавил", requestor.mention, inline=True)
    emb.add_field("Источник", track.info.source_name, inline=True)
    emb.set_image(track.info.artwork_url)
    return emb


def list_track_embed(
    track: Sequence[ongaku.Track], requestor: hikari.User
) -> hikari.Embed:
    """Описание конкретного трека."""
    first_track = track[0]

    if first_track.info.is_stream:
        color = hikari.Color(0xCC66FF)
    else:
        color = hikari.Color(0x66CCFF)

    emb = hikari.Embed(
        title=f"Добавил треки ({len(track)})",
        description=(
            f"Название: {first_track.info.title}"
            f"Автор: {first_track.info.author}\n"
            f"Длительность: `{format_time(first_track.info.length)}`\n"
            f"Начало: `{format_time(first_track.info.position)}`\n"
            f"Источник: `{first_track.info.source_name}`\n"
            f"Добавил: {requestor.mention}\n"
        ),
        color=color,
    )
    emb.set_thumbnail(first_track.info.artwork_url)

    for i, sub_track in enumerate(track[1:]):
        if i == _MAX_FIELDS:
            break
        emb.add_field(sub_track.info.title, track_status(sub_track))

    return emb


def playlist_embed(
    playlist: ongaku.Playlist, requestor: hikari.User
) -> hikari.Embed:
    """Описание конкретного трека."""
    first_track = playlist.tracks[0]
    if first_track.info.is_stream:
        color = hikari.Color(0xCC66FF)
    else:
        color = hikari.Color(0x66CCFF)

    emb = hikari.Embed(
        title=playlist.info.name,
        description=(
            f"Название: {first_track.info.title}"
            f"Автор: {first_track.info.author}\n"
            f"Длительность: `{format_time(first_track.info.length)}`\n"
            f"Начало: `{format_time(first_track.info.position)}`\n"
            f"Источник: `{first_track.info.source_name}`\n"
            f"Добавил: {requestor.mention}\n"
            f"Треков: {len(playlist.tracks)}\n"
        ),
        color=color,
    )
    emb.set_thumbnail(first_track.info.artwork_url)

    for i, sub_track in enumerate(playlist.tracks[1:]):
        if i == _MAX_FIELDS:
            break
        emb.add_field(sub_track.info.title, track_status(sub_track))

    return emb


def query_track_embed(
    query: QueryTrack, requestor: hikari.User
) -> hikari.Embed:
    """Собирает embed о добавленном плеер треке."""
    if isinstance(query, ongaku.Track):
        return track_embed(query, requestor)
    elif isinstance(query, ongaku.Playlist):
        return playlist_embed(query, requestor)
    return list_track_embed(query, requestor)


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

    emb = query_track_embed(res, ctx.author)
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
    emb = query_track_embed(res, ctx.author)
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
        await ctx.respond("Музыка приостановлена.")
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
    await ctx.respond(list_track_embed(player.queue, ctx.author))


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
    await ctx.respond(f"{amount} песен пропускаю.")


@plugin.include
@arc.with_hook(arc_ensure_player)
@arc.slash_command("stop", "Остановить воспроизведение.")
async def stop_player(
    ctx: arc.GatewayContext,
    player: ongaku.Player = arc.inject(),
) -> None:
    """Останавливает воспроизведение в канале."""
    await player.disconnect()
    await ctx.respond("Увидимся позже.")


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
