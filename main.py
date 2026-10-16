#!/usr/bin/env python3
# SPDX-License-Identifier: 0BSD
"""A discord bot."""

from asyncio import wait_for, Runner
from os import environ

from uvloop import new_event_loop
from yt_dlp import YoutubeDL
from discord import (
    app_commands,
    Intents,
    Client,
    Embed,
    Color,
    Interaction,
    ClientUser,
    Message,
    Member
)


class Bot(Client):
    user: ClientUser
    SYNC_ENABLED = int(environ["BOT_SYNC_ENABLED"])

    def __init__(self) -> None:
        intents = Intents.default()
        super().__init__(chunk_guilds_at_startup=False, intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self) -> None:
        if self.SYNC_ENABLED:
            await self.tree.sync()


bot = Bot()


@bot.tree.command(description="Данные сервака")
@app_commands.choices(
    item=[
        app_commands.Choice(name="Иконка", value="icon"),
        app_commands.Choice(name="Баннер", value="banner"),
        app_commands.Choice(name="Сплэш инвайта", value="splash"),
        app_commands.Choice(name="ID", value="id")
    ]
)
@app_commands.describe(item="Докс сват спортики")
async def server_data(ctx: Interaction, item: str) -> None:
    data = getattr(ctx.guild, item)
    content = f"```{data}```" if item == "id" else "> " + str(data)
    await ctx.response.send_message(content=content)


@bot.tree.command(description="Данные профиля чела")
@app_commands.choices(
    item=[
        app_commands.Choice(name="Ава", value="display_avatar"),
        app_commands.Choice(name="Username", value="name"),
        app_commands.Choice(name="ID", value="id")
    ]
)
@app_commands.describe(member="Чел", item="Докс сват спортики")
async def member_data(ctx: Interaction, member: Member, item: str) -> None:
    data = getattr(member, item)
    content = "> " + str(data) if item == "display_avatar" else f"```{data}```"
    await ctx.response.send_message(content=content)


@bot.tree.command(description="Посчитать длину строки")
@app_commands.describe(text="Пиши свою строку")
async def length(ctx: Interaction, text: str) -> None:
    description = f"Длина {len(text)}"
    embed = Embed(description=description, color=Color.green())
    await ctx.response.send_message(embed=embed)


@bot.tree.command(description="Проверить синхронизацию")
async def check_sync(ctx: Interaction) -> None:
    description = "Ага" if bot.SYNC_ENABLED else "Нет нихуя"
    embed = Embed(description=description, color=Color.green())
    await ctx.response.send_message(embed=embed)


async def main() -> None:
    token = environ["MASTER_TOKEN"]
    async with bot:
       await bot.start(token)


if __name__ == "__main__":
    with Runner(loop_factory=new_event_loop) as runner:
        runner.run(main())
