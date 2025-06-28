"""Nekos.life api wrapper.

Author: Nekos-life
Version: v2.1
License: MIT
Repo: https://github.com/Nekos-life/nekos.py
"""

from dataclasses import dataclass
from urllib.parse import quote

from aiohttp import ClientSession

API_URL = "https://nekos.life/api/v2"


@dataclass
class Endpoint:
    """API ручка для получения данных."""

    url: str
    get: str

    async def fetch(
        self, session: ClientSession, query: str | None = None
    ) -> str:
        """Получает данные из указанного источника."""
        url = f"{API_URL}/{self.url}"
        if url.endswith("?") and query is not None:
            url = f"{url}text={quote(query)}"

        async with session.get(url) as res:
            resp: str = (await res.json()).get(self.get)
        return resp


@dataclass
class Endpoints:
    """Перечисление всех доступных ручек."""

    # Fun endpoints
    cat = Endpoint("/cat", "cat")
    fact = Endpoint("/fact", "fact")
    name = Endpoint("/name", "name")
    owoify = Endpoint("/owoify?", "owo")
    spoiler = Endpoint("/spoiler?", "owo")
    why = Endpoint("/why", "why")

    # Images endpoints
    eightball = Endpoint("/8ball", "url")
    smug = Endpoint("/img/smug", "url")
    woof = Endpoint("/img/woof", "url")
    cuddle = Endpoint("/img/cuddle", "url")
    goose = Endpoint("/img/goose", "url")
    avatar = Endpoint("/img/avatar", "url")
    slap = Endpoint("/img/slap", "url")
    pat = Endpoint("/img/pat", "url")
    gecg = Endpoint("/img/gecg", "url")
    feed = Endpoint("/img/feed", "url")
    fox_girl = Endpoint("/img/fox_girl", "url")
    hug = Endpoint("/img/hug", "url")
    neko = Endpoint("/img/neko", "url")
    meow = Endpoint("/img/meow", "url")
    kiss = Endpoint("/img/kiss", "url")
    wallpaper = Endpoint("/img/wallpaper", "url")
    tickle = Endpoint("/img/tickle", "url")
    lizard = Endpoint("/img/lizard", "url")
    ngif = Endpoint("/img/ngif", "url")
    waifu = Endpoint("/img/waifu", "url")

    # NSFW
    gasm = Endpoint("/img/gasm", "url")
    spank = Endpoint("/img/spank", "url")
