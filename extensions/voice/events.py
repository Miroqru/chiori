"""Расширенная поддержка голосовых событий.

Позволяет обрабатывать события:
- UserStartVoice
- UserUpdateVoice
- UserStopVoice
- GuildStartVoice
- GuildUpdateVoice
- GuildStopVoice

Version: v1.0 (1)
Author: Milinuri Nirvalen
"""

import arc
import hikari
from loguru import logger

from chioricord.client import ChioClient
from chioricord.plugin import ChioPlugin
from libs import voice_events

plugin = ChioPlugin("Voice events")


@plugin.listen(hikari.VoiceStateUpdateEvent)
@plugin.inject_dependencies()
async def on_voice_update(
    event: hikari.VoiceStateUpdateEvent,
    storage: voice_events.VoiceStorage = arc.inject(),
) -> None:
    """Обрабатывает события входа и выхода из голосового канала."""
    before = event.old_state
    after = event.state
    member = event.state.member

    if member is None or member.is_bot:
        return

    if before is None:
        storage.start(after)
        return

    if after.channel_id is None:
        logger.warning("stop")
        storage.stop(before)
    elif not storage.in_voice(after):
        storage.start(after)
    else:
        storage.update(before, after)


@arc.loader
def loader(client: ChioClient) -> None:
    """Actions on plugin load."""
    storage = voice_events.VoiceStorage(client)
    client.set_type_dependency(voice_events.VoiceStorage, storage)
    client.add_plugin(plugin)
