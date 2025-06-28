"""Обработчик для neko.life.

Отправляет различные весёлые картиночки.

Предоставляет
-------------

- /nya <member> - Някнуть участника

Version: v1.0 (1)
Author: Milinuri Nirvalen
"""

import aiohttp
import arc
import hikari

from libs.neko import Endpoints

plugin = arc.GatewayPlugin("Neko life")

neko_img = plugin.include_slash_group(
    name="nekoimg",
    description="Различные милые картиночки.",
    default_permissions=hikari.Permissions.ADMINISTRATOR,
)

neko = plugin.include_slash_group(
    name="neko",
    description="Различные милые команды.",
    default_permissions=hikari.Permissions.ADMINISTRATOR,
)


# Генерация картиночек
# ====================


@neko_img.include
@arc.slash_subcommand("avatar", description="Аниме аватарка.")
async def neko_avatar(ctx: arc.GatewayContext) -> None:
    """Отправляет аниме аватарку."""
    async with aiohttp.ClientSession() as session:
        emb = hikari.Embed(title="🩷 Аватар", color=hikari.Color(0xFF99CC))
        emb.set_image(await Endpoints.avatar.fetch(session))
        await ctx.respond(emb)


@neko_img.include
@arc.slash_subcommand("cuddle", description="прижаться.")
async def neko_cuddle(ctx: arc.GatewayContext) -> None:
    """Отправляет картинку обнимашек."""
    async with aiohttp.ClientSession() as session:
        emb = hikari.Embed(title="🩷 прижаться", color=hikari.Color(0xFF99CC))
        emb.set_image(await Endpoints.cuddle.fetch(session))
        await ctx.respond(emb)


@neko_img.include
@arc.slash_subcommand("eightball", description="8 шар ответит на ваш вопрос.")
async def neko_eightball(ctx: arc.GatewayContext) -> None:
    """Отправляет картинку 8шара."""
    async with aiohttp.ClientSession() as session:
        emb = hikari.Embed(title="🩷 8 шар", color=hikari.Color(0xFF99CC))
        emb.set_image(await Endpoints.eightball.fetch(session))
        await ctx.respond(emb)


@neko_img.include
@arc.slash_subcommand("smug", description="Довольная мордочка.")
async def neko_smug(ctx: arc.GatewayContext) -> None:
    """Отправляет самодовольную мордашку."""
    async with aiohttp.ClientSession() as session:
        emb = hikari.Embed(
            title="🩷 Довольная мордочка", color=hikari.Color(0xFF99CC)
        )
        emb.set_image(await Endpoints.smug.fetch(session))
        await ctx.respond(emb)


@neko_img.include
@arc.slash_subcommand("woof", description="Собачка.")
async def neko_woof(ctx: arc.GatewayContext) -> None:
    """Отправляет фото собачки."""
    async with aiohttp.ClientSession() as session:
        emb = hikari.Embed(title="🩷 Гав", color=hikari.Color(0xFF99CC))
        emb.set_image(await Endpoints.woof.fetch(session))
        await ctx.respond(emb)


@neko_img.include
@arc.slash_subcommand("goose", description="Фото гуся.")
async def neko_goose(ctx: arc.GatewayContext) -> None:
    """Отправляет фото собачки."""
    async with aiohttp.ClientSession() as session:
        emb = hikari.Embed(title="🩷 Гусь", color=hikari.Color(0xFF99CC))
        emb.set_image(await Endpoints.goose.fetch(session))
        await ctx.respond(emb)


@neko_img.include
@arc.slash_subcommand("slap", description="Шлепок.")
async def neko_slap(ctx: arc.GatewayContext) -> None:
    """Отправляет фото собачки."""
    async with aiohttp.ClientSession() as session:
        emb = hikari.Embed(title="🩷 Шлепок", color=hikari.Color(0xFF99CC))
        emb.set_image(await Endpoints.slap.fetch(session))
        await ctx.respond(emb)


@neko_img.include
@arc.slash_subcommand("pat", description="Погладить.")
async def neko_pat(ctx: arc.GatewayContext) -> None:
    """Отправляет фото поглаживаний."""
    async with aiohttp.ClientSession() as session:
        emb = hikari.Embed(
            title="🩷 Поглаживания", color=hikari.Color(0xFF99CC)
        )
        emb.set_image(await Endpoints.pat.fetch(session))
        await ctx.respond(emb)


@neko_img.include
@arc.slash_subcommand(name="gecg", description="gecg.")
async def neko_gecg(ctx: arc.GatewayContext) -> None:
    """Отправляет фото ???."""
    async with aiohttp.ClientSession() as session:
        emb = hikari.Embed(
            title="🩷 Every dollar spent on a...", color=hikari.Color(0xFF99CC)
        )
        emb.set_image(await Endpoints.gecg.fetch(session))
        await ctx.respond(emb)


@neko_img.include
@arc.slash_subcommand(name="feed", description="Покормить.")
async def neko_feed(ctx: arc.GatewayContext) -> None:
    """Отправляет фото собачки."""
    async with aiohttp.ClientSession() as session:
        emb = hikari.Embed(title="🩷 Покормить", color=hikari.Color(0xFF99CC))
        emb.set_image(await Endpoints.feed.fetch(session))
        await ctx.respond(emb)


@neko_img.include
@arc.slash_subcommand(name="fox_girl", description="Девочка-лисичка.")
async def neko_fox_girl(ctx: arc.GatewayContext) -> None:
    """Отправляет фото девочки лисички."""
    async with aiohttp.ClientSession() as session:
        emb = hikari.Embed(title="🩷 Лисичка", color=hikari.Color(0xFF99CC))
        emb.set_image(await Endpoints.fox_girl.fetch(session))
        await ctx.respond(emb)


@neko_img.include
@arc.slash_subcommand(name="hug", description="Обнимашки.")
async def neko_hug(ctx: arc.GatewayContext) -> None:
    """Отправляет фото обнимашек."""
    async with aiohttp.ClientSession() as session:
        emb = hikari.Embed(title="🩷 Обнимашки", color=hikari.Color(0xFF99CC))
        emb.set_image(await Endpoints.hug.fetch(session))
        await ctx.respond(emb)


@neko_img.include
@arc.slash_subcommand(name="neko", description="Кошкодевочка.")
async def neko_neko(ctx: arc.GatewayContext) -> None:
    """Отправляет фото обнимашек."""
    async with aiohttp.ClientSession() as session:
        emb = hikari.Embed(
            title="🩷 Кошкодевочка", color=hikari.Color(0xFF99CC)
        )
        emb.set_image(await Endpoints.neko.fetch(session))
        await ctx.respond(emb)


@neko_img.include
@arc.slash_subcommand(name="meow", description="Котик.")
async def neko_meow(ctx: arc.GatewayContext) -> None:
    """Отправляет фото котика."""
    async with aiohttp.ClientSession() as session:
        emb = hikari.Embed(title="🩷 Котик", color=hikari.Color(0xFF99CC))
        emb.set_image(await Endpoints.meow.fetch(session))
        await ctx.respond(emb)


@neko_img.include
@arc.slash_subcommand(name="kiss", description="Поцелуй.")
async def neko_kiss(ctx: arc.GatewayContext) -> None:
    """Отправляет фото поцелуя."""
    async with aiohttp.ClientSession() as session:
        emb = hikari.Embed(title="🩷 Поцелуй", color=hikari.Color(0xFF99CC))
        emb.set_image(await Endpoints.kiss.fetch(session))
        await ctx.respond(emb)


@neko_img.include
@arc.slash_subcommand(name="wallpaper", description="Аниме обои.")
async def neko_wallpaper(ctx: arc.GatewayContext) -> None:
    """Отправляет фото аниме обоев для рабочего стола."""
    async with aiohttp.ClientSession() as session:
        emb = hikari.Embed(title="🩷 Аниме обои", color=hikari.Color(0xFF99CC))
        emb.set_image(await Endpoints.wallpaper.fetch(session))
        await ctx.respond(emb)


@neko_img.include
@arc.slash_subcommand(name="tickle", description="Щекотка.")
async def neko_tickle(ctx: arc.GatewayContext) -> None:
    """Отправляет фото щекотки."""
    async with aiohttp.ClientSession() as session:
        emb = hikari.Embed(title="🩷 Щекотка", color=hikari.Color(0xFF99CC))
        emb.set_image(await Endpoints.tickle.fetch(session))
        await ctx.respond(emb)


@neko_img.include
@arc.slash_subcommand(name="lizard", description="Ящерица.")
async def neko_lizard(ctx: arc.GatewayContext) -> None:
    """Отправляет фото ящерицы."""
    async with aiohttp.ClientSession() as session:
        emb = hikari.Embed(title="🩷 Ящерица", color=hikari.Color(0xFF99CC))
        emb.set_image(await Endpoints.lizard.fetch(session))
        await ctx.respond(emb)


@neko_img.include
@arc.slash_subcommand(name="ngif", description="Неко гиф.")
async def neko_ngif(ctx: arc.GatewayContext) -> None:
    """Отправляет неко гиф картинку."""
    async with aiohttp.ClientSession() as session:
        emb = hikari.Embed(title="🩷 Неко гиф", color=hikari.Color(0xFF99CC))
        emb.set_image(await Endpoints.ngif.fetch(session))
        await ctx.respond(emb)


@neko_img.include
@arc.slash_subcommand(name="waifu", description="Ваша вайфу.")
async def neko_waifu(ctx: arc.GatewayContext) -> None:
    """Отправляет фото вайфу."""
    async with aiohttp.ClientSession() as session:
        emb = hikari.Embed(title="🩷 Вайфу", color=hikari.Color(0xFF99CC))
        emb.set_image(await Endpoints.waifu.fetch(session))
        await ctx.respond(emb)


@neko_img.include
@arc.slash_subcommand(name="gasm", description="Оргазм.")
async def neko_gasm(ctx: arc.GatewayContext) -> None:
    """Отправляет фото вайфу."""
    async with aiohttp.ClientSession() as session:
        emb = hikari.Embed(title="🩷 Оргазм", color=hikari.Color(0xFF99CC))
        emb.set_image(await Endpoints.gasm.fetch(session))
        await ctx.respond(emb)


@neko_img.include
@arc.slash_subcommand(name="spank", description="Шлепок.")
async def neko_spank(ctx: arc.GatewayContext) -> None:
    """Отправляет фото вайфу."""
    async with aiohttp.ClientSession() as session:
        emb = hikari.Embed(title="🩷 Шлепок", color=hikari.Color(0xFF99CC))
        emb.set_image(await Endpoints.spank.fetch(session))
        await ctx.respond(emb)


# Весёлые команды
# ===============


@neko.include
@arc.slash_subcommand("cat", description="Кошачья мордочка.")
async def neko_cat(ctx: arc.GatewayContext) -> None:
    """Отправляет кошачью мордочку."""
    async with aiohttp.ClientSession() as session:
        await ctx.respond(await Endpoints.cat.fetch(session))


@neko.include
@arc.slash_subcommand("fact", description="Интересный факт.")
async def neko_fact(ctx: arc.GatewayContext) -> None:
    """Отправляет интересный факт."""
    async with aiohttp.ClientSession() as session:
        await ctx.respond(await Endpoints.fact.fetch(session))


@neko.include
@arc.slash_subcommand("name", description="Случайное имя.")
async def neko_name(ctx: arc.GatewayContext) -> None:
    """Отправляет интересный факт."""
    async with aiohttp.ClientSession() as session:
        await ctx.respond(await Endpoints.name.fetch(session))


@neko.include
@arc.slash_subcommand("why", description="Вопрос дня.")
async def neko_nya(ctx: arc.GatewayContext) -> None:
    """Отправляет случайный вопрос."""
    async with aiohttp.ClientSession() as session:
        await ctx.respond(await Endpoints.why.fetch(session))


@neko.include
@arc.slash_subcommand("owoify", description="owoify your text.")
async def neko_owoify(
    ctx: arc.GatewayContext,
    text: arc.Option[str, arc.StrParams("Текст для перевода")],  # type: ignore
) -> None:
    """Отправляет весёлый текст."""
    async with aiohttp.ClientSession() as session:
        await ctx.respond(await Endpoints.owoify.fetch(session, text))


@neko.include
@arc.slash_subcommand(name="spoiler", description="Прячет текст под спойлером.")
async def neko_spoiler(
    ctx: arc.GatewayContext,
    text: arc.Option[str, arc.StrParams("Текст для спойлера")],  # type: ignore
) -> None:
    """Прячет текст под спойлером."""
    async with aiohttp.ClientSession() as session:
        await ctx.respond(await Endpoints.spoiler.fetch(session, text))


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
