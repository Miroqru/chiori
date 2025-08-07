"""Музыкальный плеер для Chiori.

Использует библиотеку hikari-ongaku для взаимодействия с lavalink.

TODO для релиза
---------------

- [ ] Документация.
    - [ ] Player
        - [ ] set position
        - [ ] set filters
- [ ] Обработка событий.
    - [ ] StartTrackEvent
    - [ ] EndTrackEvent
    - [ ] PlayerUpdateEvent
    - [ ] StatisticsEvent
- [ ] PlayerView.
- [ ] Портировать говнокод.

Предоставляет
-------------

- /play <query>: Сыграть песню.
- /np: Что сейчас играет.
- /pause: Поставить плеер на паузу/возобновить произведение.
- /autoplay: Автоматически играть следующую песню.
- /loop: Циклическое воспроизведение.
- /volume <1-100>: Установить громкость плеера.
- /skip [1]: Пропустить песни в очереди.
- /stop: Остановить воспроизведение.
- /leave: Завершить воспроизведение.

Плеер:
- /player status: Состояние плеера.
- /player info: Информация о плеере.
- /player stats: Статистика плеера.

Очередь:
- /queue list: Очередь воспроизведения.
- /queue add: Добавить трек в очередь.
- /queue remove: Удалить трек из очереди.
- /queue clear: Очистить очередь.
- /queue shuffle: Перемешать очередь.

Version: v2.5.2 (35)
Author: Milinuri Nirvalen
"""

from collections.abc import Sequence

import arc
import hikari
import ongaku
import ongaku.errors
from loguru import logger
from ongaku.client import Client
from ongaku.ext.injection import arc_ensure_player

from chioricord.api import PluginConfig
from chioricord.client import ChioClient, ChioContext
from chioricord.plugin import ChioPlugin

plugin = ChioPlugin("Music")


class MusicConfig(PluginConfig, config="music"):
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

    player_channel_id: int
    """Канал. куда оправлять сообщения и события плеера."""


QueryTrack = ongaku.Playlist | Sequence[ongaku.Track] | ongaku.Track

_MAX_FIELDS = 25


# Вспомогательные функции
# =======================


def format_time(milliseconds: int) -> str:
    """Преобразует количество миллисекунд в строку времени."""
    days, r = divmod(milliseconds // 1000, 86400)
    hours, r = divmod(r, 3600)
    minutes, seconds = divmod(r, 60)

    if days > 0:
        return f"{days}:{hours:02d}:{minutes:02d}:{seconds:02d}"

    if hours > 0:
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


def now_playing_embed(track: ongaku.Track) -> hikari.Embed:
    """Описание конкретного трека."""
    if track.info.is_stream:
        color = hikari.Color(0xCC66FF)
    else:
        color = hikari.Color(0x66FFCC)

    emb = hikari.Embed(
        title="Сейчас играет",
        description=(
            f"{track.info.title}"
            f"Автор: {track.info.author} (`{track.info.source_name}`)\n"
            f"`{format_time(track.info.position)}` / "
            f"`{format_time(track.info.length)}`\n"
        ),
        url=track.info.uri,
        color=color,
    )
    emb.set_thumbnail(track.info.artwork_url)
    return emb


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
            f"`{format_time(track.info.position)}` / "
            f"`{format_time(track.info.length)}`\n"
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
            f"`{format_time(first_track.info.position)}` / "
            f"`{format_time(first_track.info.length)}`\n"
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
            f"`{format_time(first_track.info.position)}` / "
            f"`{format_time(first_track.info.length)}`\n"
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
    if isinstance(query, ongaku.Playlist):
        return playlist_embed(query, requestor)
    return list_track_embed(query, requestor)


# Обработка событий
# =================


@plugin.listen(ongaku.TrackExceptionEvent)
@plugin.inject_dependencies()
async def on_track_exception(
    event: ongaku.TrackExceptionEvent, config: MusicConfig = arc.inject()
) -> None:
    """Когда Трек во время воспроизведения застревает."""
    emb = hikari.Embed(
        title="Проблема воспроизведения",
        description=(
            f"`{event.exception.severity}`: {event.exception.message}\n"
            f"Причина: {event.exception.cause}"
        ),
        color=hikari.Color(0xFF66CC),
    )
    emb.add_field(event.track.info.title, track_status(event.track))
    await event.app.rest.create_message(config.player_channel_id, emb)


@plugin.listen(ongaku.TrackStuckEvent)
@plugin.inject_dependencies()
async def on_track_stuck(
    event: ongaku.TrackStuckEvent, config: MusicConfig = arc.inject()
) -> None:
    """Когда Трек во время воспроизведения застревает."""
    emb = hikari.Embed(
        title="Проблема воспроизведения",
        description=f"Немного зажевало.\nПорог: `{event.threshold_ms}` мс.",
        color=hikari.Color(0xFF66CC),
    )
    emb.add_field(event.track.info.title, track_status(event.track))
    await event.app.rest.create_message(config.player_channel_id, emb)


@plugin.listen(ongaku.WebsocketClosedEvent)
@plugin.inject_dependencies()
async def on_websocket_closed(
    event: ongaku.WebsocketClosedEvent, config: MusicConfig = arc.inject()
) -> None:
    """Когда веб сокет разорвал соединение."""
    emb = hikari.Embed(
        title="Разорвано соединение",
        description=f"`{event.code}`: {event.reason}",
        color=hikari.Color(0xFF66CC),
    )
    await event.app.rest.create_message(config.player_channel_id, emb)


@plugin.listen(ongaku.QueueEmptyEvent)
@plugin.inject_dependencies()
async def on_queue_empty(
    event: ongaku.QueueEmptyEvent, config: MusicConfig = arc.inject()
) -> None:
    """Когда переходит на новый трек."""
    await event.app.rest.create_message(
        config.player_channel_id, "Больше нечего играть, спасибо за внимание."
    )


@plugin.listen(ongaku.QueueNextEvent)
@plugin.inject_dependencies()
async def on_next_track(
    event: ongaku.QueueNextEvent, config: MusicConfig = arc.inject()
) -> None:
    """Когда переходит на новый трек."""
    await event.app.rest.create_message(
        config.player_channel_id, now_playing_embed(event.track)
    )


@plugin.set_error_handler()
@plugin.inject_dependencies()
async def error_handler(
    ctx: ChioContext, exc: Exception, client: Client = arc.inject()
) -> None:
    """Если плеер упал."""
    if isinstance(exc, arc.GuildOnlyError):
        await ctx.respond(
            "Может я на сервере вам спою?..",
            flags=hikari.MessageFlag.EPHEMERAL,
        )
        return

    if isinstance(exc, ongaku.PlayerMissingError):
        await ctx.respond(
            "Для начала нам нужен плеер.",
            flags=hikari.MessageFlag.EPHEMERAL,
        )
        return

    if isinstance(exc, ongaku.errors.RestRequestError):
        logger.exception(exc)
        logger.error(client.session_handler.sessions)

    raise exc


# определение команд
# ==================


@plugin.include
@arc.slash_command("play", description="Сыграть песню.")
async def play_song(
    ctx: ChioContext,
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
            "Пожалуйста зайдите в голосовой канал чтобы я смогла спеть.",
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
        await player.play(requestor=ctx.author)

    if player.is_paused:
        await player.pause(False)

    emb = query_track_embed(res, ctx.author)
    await ctx.respond(emb)


@plugin.include
@arc.with_hook(arc_ensure_player)
@arc.slash_command("np", "Что сейчас играет.")
async def now_playing(
    ctx: ChioContext,
    player: ongaku.Player = arc.inject(),
) -> None:
    """Какая песня сейчас играет."""
    if len(player.queue) == 0:
        await ctx.respond("Сейчас я отдыхаю.")
        return
    await ctx.respond(now_playing_embed(player.queue[0]))


@plugin.include
@arc.with_hook(arc_ensure_player)
@arc.slash_command("pause", "Приостановить/возобновить воспроизведение.")
async def player_pause(
    ctx: ChioContext,
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
@arc.slash_command("autoplay", "Приостановить/возобновить воспроизведение.")
async def player_aytoplay(
    ctx: ChioContext,
    player: ongaku.Player = arc.inject(),
) -> None:
    """Останавливает/возобновляет воспроизведение музыку."""
    status = player.set_autoplay()
    if status:
        await ctx.respond("✅ Авто-проигрывание включено.")
    else:
        await ctx.respond("❌ Авто-проигрывание отключено.")


@plugin.include
@arc.with_hook(arc_ensure_player)
@arc.slash_command("loop", "Приостановить/возобновить воспроизведение.")
async def player_loop(
    ctx: ChioContext,
    player: ongaku.Player = arc.inject(),
) -> None:
    """Останавливает/возобновляет воспроизведение музыку."""
    status = player.set_loop()
    if status:
        await ctx.respond("✅ Зацикливание включено.")
    else:
        await ctx.respond("❌ Зацикливание отключено.")


@plugin.include
@arc.with_hook(arc_ensure_player)
@arc.slash_command("volume", "Установить громкость плеера.")
async def player_volume(
    ctx: ChioContext,
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
    ctx: ChioContext,
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
    ctx: ChioContext,
    player: ongaku.Player = arc.inject(),
) -> None:
    """Останавливает воспроизведение в канале."""
    await player.stop()
    await ctx.respond("Буду рада ещё спеть.")


@plugin.include
@arc.with_hook(arc_ensure_player)
@arc.slash_command("leave", "Завершить плеер.")
async def leave_player(
    ctx: ChioContext,
    player: ongaku.Player = arc.inject(),
) -> None:
    """Останавливает воспроизведение в канале."""
    await player.disconnect()
    await ctx.respond("Увидимся позже.")


# Информация о плеере
# ===================

player_group = plugin.include_slash_group("player", "Информация о плеере")


@player_group.include
@arc.with_hook(arc_ensure_player)
@arc.slash_subcommand("status", "Состояние плеера.")
async def player_status(
    ctx: ChioContext, player: ongaku.Player = arc.inject()
) -> None:
    """Основная информация о плеере."""
    guild = ctx.get_guild()
    if guild is None:
        raise arc.GuildOnlyError

    if player.channel_id:
        channel = guild.get_channel(player.channel_id)
        if channel is not None:
            in_channel = channel.mention
        else:
            in_channel = f"`{player.channel_id}`"
    else:
        in_channel = "< без канала >"

    emb = hikari.Embed(
        title="плеер",
        description=(
            f"в канале {in_channel}\n"
            f"Громкость: {player.volume}\n"
            f"Позиция: {format_time(player.position)}\n"
            f"В очереди: {len(player.queue)} треков\n"
            f"⚡ {'стоит' if player.is_paused else 'мурлычет'}\n"
            f"⚡ {'живой' if player.is_alive else 'откис'}\n"
            f"⚡ Автоплей: {'имеется' if player.autoplay else 'отключили'}\n"
            f"⚡ Петля: {'зациклен' if player.loop else 'не зациклен'}\n"
        ),
        color=hikari.Color(0x66FFCC),
    )
    await ctx.respond(emb)


@player_group.include
@arc.slash_subcommand("info", "Информация о плеере.")
async def player_info(
    ctx: ChioContext, ongaku_client: ongaku.Client = arc.inject()
) -> None:
    """Основная информация о плеере."""
    info = await ongaku_client.rest.fetch_info()
    emb = hikari.Embed(
        title="О плеере",
        description=(
            f"версия: `{info.version.semver}`\n"
            f"Собран: `{info.build_time}`\n"
            f"Jvm: {info.jvm}\n"
            f"Lavaplayer: {info.lavaplayer}\n"
        ),
        color=hikari.Color(0x66FFCC),
    )
    emb.add_field(
        "Git",
        f"[{info.git.branch}]: `{info.git.commit}\nОт: {info.git.commit_time}",
    )
    emb.add_field("Источники", ", ".join(info.source_managers))
    emb.add_field("Фильтры", ", ".join(info.source_managers))

    plugins_list = ""
    for plugin in info.plugins:
        plugins_list += f"\n- {plugin.name}: `{plugin.version}`"
    emb.add_field("Плагины", plugins_list)
    await ctx.respond(emb)


@player_group.include
@arc.slash_subcommand("stats", "Статистика плеера.")
async def player_stats(
    ctx: ChioContext, ongaku_client: ongaku.Client = arc.inject()
) -> None:
    """Основная информация о плеере."""
    stats = await ongaku_client.rest.fetch_stats()
    emb = hikari.Embed(
        title="Статистика плеера",
        description=(
            f"Плееров:  {stats.playing_players}/{stats.players}\n"
            f"Время работы: {format_time(stats.uptime)}\n"
        ),
        color=hikari.Color(0x66FFCC),
    )
    emb.add_field(
        "Память",
        (
            f"Свободно: {stats.memory.free}\n"
            f"Использовано: {stats.memory.used}\n"
            f"Выделено: {stats.memory.allocated}\n"
            f"Зарезервировано: {stats.memory.reservable}\n"
        ),
    )
    emb.add_field(
        "Процессор",
        (
            f"Ядер: {stats.cpu.cores}\n"
            f"Загрузка: {stats.cpu.system_load}\n"
            f"Плеером: {stats.cpu.lavalink_load}\n"
        ),
    )
    if stats.frame_stats is not None:
        emb.add_field(
            "Frames",
            (
                f"Sent: {stats.frame_stats.sent}\n"
                f"Nulled: {stats.frame_stats.nulled}\n"
                f"Deficit: {stats.frame_stats.deficit}\n"
            ),
        )
    await ctx.respond(emb)


# Управление очередью треков
# ==========================

queue = plugin.include_slash_group(
    "queue", "Управление очередью воспроизведения"
)


@queue.include
@arc.with_hook(arc_ensure_player)
@arc.slash_subcommand("list", "Очередь воспроизведения.")
async def player_queue(
    ctx: ChioContext,
    player: ongaku.Player = arc.inject(),
) -> None:
    """Очередь воспроизведения."""
    if len(player.queue) == 0:
        await ctx.respond("Очередь пуста. Играть нечего.")
        return
    await ctx.respond(list_track_embed(player.queue, ctx.author))


@queue.include
@arc.with_hook(arc_ensure_player)
@arc.slash_subcommand("add", description="Добавить песни в очередь.")
async def add_track(
    ctx: ChioContext,
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


@queue.include
@arc.with_hook(arc_ensure_player)
@arc.slash_subcommand("remove", description="удалить трек из очереди.")
async def remove_track(
    ctx: ChioContext,
    track: arc.Option[  # type: ignore
        int, arc.IntParams("Какую песню удалить.")
    ],
    player: ongaku.Player = arc.inject(),
) -> None:
    """Удаляет трек из очереди проигрывания."""
    track_info = player.queue[track]
    player.remove(track)
    await ctx.respond(f"Удалено из очереди {track_info.info.title}.")


@queue.include
@arc.with_hook(arc_ensure_player)
@arc.slash_subcommand("clear", description="Очистить очередь.")
async def clear_queue(
    ctx: ChioContext,
    player: ongaku.Player = arc.inject(),
) -> None:
    """Удаляет трек из очереди проигрывания."""
    await player.clear()
    await ctx.respond("Очередь очищена.")


@queue.include
@arc.with_hook(arc_ensure_player)
@arc.slash_subcommand("shuffle", description="Перемещать очередь.")
async def shuffle_queue(
    ctx: ChioContext,
    player: ongaku.Player = arc.inject(),
) -> None:
    """Удаляет трек из очереди проигрывания."""
    player.shuffle()
    await ctx.respond("Очередь перемешана.")


# Загрузчики и выгрузчики плагина
# ===============================


@plugin.listen(arc.StartedEvent)
async def on_start(event: arc.StartedEvent[ChioClient]) -> None:
    """Подключаемся к сессии."""
    logger.info("Create ongaku session")
    ongaku_client = ongaku.Client.from_arc(event.client)
    config = event.client.config.get(MusicConfig)
    ongaku_client.create_session(
        name=config.name,
        ssl=config.ssl,
        host=config.host,
        port=config.port,
        password=config.password,
    )


@arc.loader
def loader(client: ChioClient) -> None:
    """Действия при загрузке плагина."""
    plugin.set_config(MusicConfig)
    client.add_plugin(plugin)
