"""Музыкальный бот.

Version: v0.1 (1)
Author: Milinuri Nirvalen
"""

import arc
import hikari
import miru

# Глобальные переменные
# =====================

plugin = arc.GatewayPlugin("Music")

# Музыкальные компоненты
# ======================

class MusicPlayer:
    def __init__(self, bot: hikari.GatewayBot, guild: hikari.Guild):
        self.bot = bot
        self.guild = guild
        self._voice_channel: int | None = None


    @property
    def is_connect(self) -> bool:
        return self.voice_channel is not None


    async def connect(self, channel_id: int) -> None:
        await self.bot.update_voice_state(self.guild, channel_id, self_deaf=True)
        self._voice_channel = channel_id

    async def disconnect(self) -> None:
        await self.bot.update_voice_state(self.guild, None)
        self._voice_channel = None


class MusicControlPanel(miru.View):
    pass

# class PlayerManager:
#     def __init__(self, bot: hikari.GatewayBot):
#         self._players: dict[int, MusicPlayer] = {}

# Нам нужны команды

# /play
# /pause
# /stop
# /np

# /connect
# /disconnect

# определение команд
# ==================

@plugin.include
@arc.slash_command("play", description="Начать играть песню")
async def connect_handler(
    ctx: arc.GatewayContext,
) -> None:
    if ctx.guild_id is None:
        return await ctx.respond("А мы разве на сервере?")

    voice_state = ctx.client.cache.get_voice_state(
        ctx.get_guild(), ctx.user
    )
    if voice_state is None or not voice_state.channel_id:
        return await ctx.respond(
            "А вы в голосовом канале?",
            flags=hikari.MessageFlag.EPHEMERAL
        )

    player = MusicPlayer(ctx.client.app, ctx.get_guild())
    await player.connect(voice_state.channel_id)
    await ctx.respond("Готово")

@plugin.include
@arc.slash_command("play", description="Начать играть песню")
async def stop_handler(ctx: arc.GatewayContext):
    pass


# Загрузчики и выгрузчики плагина
# ===============================

@arc.loader
def loader(client: arc.GatewayClient) -> None:
    """Действия при загрузке плагина."""
    client.add_plugin(plugin)

@arc.unloader
def unloader(client: arc.GatewayClient) -> None:
    """Действия при выгрузке плагина."""
    client.remove_plugin(plugin)
