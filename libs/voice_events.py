"""Более детальные события голосового канала.

Предоставляет такие события как:
- Начало, окончание, обновление состояния голосового канала.

Version: v1.1 (5)
Author: Milinuri Nirvalen
"""

from dataclasses import dataclass
from time import time

import hikari

from chioricord.client import ChioClient

Timestamp = int


@dataclass(frozen=True, slots=True)
class VoiceState:
    """Состояние голосового канала."""

    start_time: Timestamp
    users: dict[int, Timestamp]


@dataclass(frozen=True, slots=True)
class VoiceEvent(hikari.Event):
    """Базовое событие изменения звонка."""

    client: ChioClient
    channel_id: hikari.Snowflake
    guild_id: hikari.Snowflake

    @property
    def app(self) -> hikari.RESTAware:
        """Приложение, для которого запускается событие."""
        return self.client.app


@dataclass(frozen=True, slots=True)
class UserVoiceEvent(VoiceEvent):
    """Пользовательское событие звонка."""

    state: hikari.VoiceState
    start_time: Timestamp


@dataclass(frozen=True, slots=True)
class GuildVoiceEvent(VoiceEvent):
    """Пользовательское событие звонка."""

    state: VoiceState


class UserStartVoice(UserVoiceEvent):
    """Начинается новый звонок пользователя."""


@dataclass(frozen=True, slots=True)
class UserUpdateVoice(UserVoiceEvent):
    """Обновляется информация о звонке пользователя."""

    old_state: hikari.VoiceState | None = None


@dataclass(frozen=True, slots=True)
class UserChangeVoice(UserVoiceEvent):
    """Обновляется информация о звонке пользователя."""

    old_state: hikari.VoiceState | None = None


class UserEndVoice(UserVoiceEvent):
    """Заканчивается звонок пользователя."""


class GuildStartVoice(GuildVoiceEvent):
    """Начинается новый звонок на сервере."""


class GuildUpdateVoice(GuildVoiceEvent):
    """Обновляется информация о звонке на сервере."""


class GuildEndVoice(GuildVoiceEvent):
    """Заканчивается звонок на сервер."""


State = dict[hikari.Snowflake, VoiceState]


# TODO: Отслеживать время для каждого участника.
class VoiceStorage:
    """Хранилище состояние голосового канала."""

    def __init__(self, client: ChioClient) -> None:
        self.state: State = {}
        self.client = client

    def in_voice(self, state: hikari.VoiceState) -> bool:
        """Проверяет, находится ли участник в голосовом канале."""
        if state.channel_id is None:
            return False

        voice_state = self.state.get(state.channel_id)
        if voice_state is None:
            return False

        return state.user_id in voice_state.users

    def start(self, state: hikari.VoiceState) -> None:
        """Записывает начало звонка."""
        if state.channel_id is None:
            raise ValueError("User leaving from voice")

        now = int(time())
        voice_state = self.state.get(state.channel_id)
        if voice_state is None:
            voice_state = VoiceState(now, {})
            self.state[state.channel_id] = voice_state
            self.client.app.event_manager.dispatch(
                GuildStartVoice(
                    self.client, state.channel_id, state.guild_id, voice_state
                )
            )
        else:
            self.client.app.event_manager.dispatch(
                GuildUpdateVoice(
                    self.client, state.channel_id, state.guild_id, voice_state
                )
            )

        self.state[state.channel_id].users[state.user_id] = now
        self.client.app.event_manager.dispatch(
            UserStartVoice(
                self.client, state.channel_id, state.guild_id, state, now
            )
        )

    def stop(self, state: hikari.VoiceState) -> None:
        """Записывает окончание звонка."""
        if state.channel_id is None:
            raise ValueError("User leaving from voice")

        start_time = self.state[state.channel_id].users.pop(state.user_id)
        self.client.app.event_manager.dispatch(
            UserEndVoice(
                self.client,
                state.channel_id,
                state.guild_id,
                state,
                start_time,
            )
        )

        if len(self.state[state.channel_id].users) == 0:
            voice_state = self.state.pop(state.channel_id)
            self.client.app.event_manager.dispatch(
                GuildEndVoice(
                    self.client, state.channel_id, state.guild_id, voice_state
                )
            )
        else:
            self.client.app.event_manager.dispatch(
                GuildUpdateVoice(
                    self.client,
                    state.channel_id,
                    state.guild_id,
                    self.state[state.channel_id],
                )
            )

    def update(
        self, old_state: hikari.VoiceState | None, state: hikari.VoiceState
    ) -> None:
        """Отправляет событие изменения состояния пользователя."""
        if state.channel_id is None:
            raise ValueError("User leaves from voice channel")

        start_time = self.state[state.channel_id].users[state.user_id]
        self.client.app.event_manager.dispatch(
            UserUpdateVoice(
                self.client,
                state.channel_id,
                state.guild_id,
                state,
                start_time,
                old_state,
            )
        )

    def move(self, before: hikari.VoiceState, after: hikari.VoiceState) -> None:
        """Перемещает пользователя в другой канал."""
        if after.channel_id is None or before.channel_id is None:
            raise ValueError("User leaving from voice")

        start_time = self.state[before.channel_id].users.pop(before.user_id)
        if len(self.state[before.channel_id].users) == 0:
            voice_state = self.state.pop(before.channel_id)
            self.client.app.event_manager.dispatch(
                GuildEndVoice(
                    self.client, before.channel_id, before.guild_id, voice_state
                )
            )
        else:
            self.client.app.event_manager.dispatch(
                GuildUpdateVoice(
                    self.client,
                    before.channel_id,
                    before.guild_id,
                    self.state[before.channel_id],
                )
            )

        voice_state = self.state.get(after.channel_id)
        if voice_state is None:
            voice_state = VoiceState(start_time, {})
            self.state[after.channel_id] = voice_state
            self.client.app.event_manager.dispatch(
                GuildStartVoice(
                    self.client, after.channel_id, after.guild_id, voice_state
                )
            )
        else:
            self.client.app.event_manager.dispatch(
                GuildUpdateVoice(
                    self.client, after.channel_id, after.guild_id, voice_state
                )
            )

        self.state[after.channel_id].users[after.user_id] = start_time
        self.client.app.event_manager.dispatch(
            UserChangeVoice(
                self.client,
                after.channel_id,
                after.guild_id,
                after,
                start_time,
                before,
            )
        )
