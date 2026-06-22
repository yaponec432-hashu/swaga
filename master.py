#!/usr/bin/env python3
# SPDX-License-Identifier: 0BSD
"""A discord bot."""

from logging import basicConfig, ERROR
from asyncio import wait_for, Runner
from os import environ

from uvloop import new_event_loop
from discord import (
    app_commands,
    Intents,
    Client,
    Embed,
    Color,
    Interaction,
    TextChannel,
    ClientUser,
    Message,
    Member,
    HTTPException,
    Forbidden
)


class MasterBot(Client):
    user: ClientUser
    SYNC_ENABLED = int(environ["BOT_SYNC_ENABLED"])
    INTENTS = Intents.default()
    INTENTS.message_content = True

    def __init__(self) -> None:
        super().__init__(chunk_guilds_at_startup=False, intents=self.INTENTS)
        self.tree = app_commands.CommandTree(self)
        self.sekai = SekaiManager()

    async def setup_hook(self) -> None:
        if self.SYNC_ENABLED:
            await self.tree.sync()

    async def on_message(self, message: Message) -> None:
        await self.sekai.update_room_code(message, self.user.id)


class SekaiManager:
    MANAGER_ROLES = {"Раннер ростера", "Лид-менеджер", "Менеджер", "Интерн"}
    CHANNEL_NAME_SEPARATOR = "-"
    CLOSED_ROOM_CODE = "xxxxx"
    ROOM_CODE_LEN = 5

    def is_manager(self, author: Member) -> bool:
        roles = reversed(author.roles)
        return any(role.name in self.MANAGER_ROLES for role in roles)

    def is_room_code(self, text: str) -> bool:
        if len(text) == self.ROOM_CODE_LEN:
            return text.isdecimal() or text == self.CLOSED_ROOM_CODE
        return False

    async def update_room_code(self, message: Message, bot_id: int) -> None:
        """Highlight the sekai room code."""
        author = message.author
        if author.bot:
            return
        channel = message.channel
        if not isinstance(channel, TextChannel):
            return
        message_text = message.content
        if not self.is_room_code(message_text):
            return
        channel_name = channel.name.split(self.CHANNEL_NAME_SEPARATOR)
        if len(channel_name) < 2:
            return
        current_room_code = channel_name[1]
        if not self.is_room_code(current_room_code):
            return
        if current_room_code == message_text:
            return
        if not self.is_manager(author):
            return
        channel_name[1] = message_text
        name = self.CHANNEL_NAME_SEPARATOR.join(channel_name)
        content = embed = None
        try:
            description = f"# `{message_text}`\nНовый код румы"
            color = Color.green()
            async with channel.typing():
                await wait_for(channel.edit(name=name), timeout=2.0)
        except (TimeoutError, HTTPException):
            content = f"{bot_id} {name} {message_text}"
        except Forbidden:
            description = "**У меня нет прав** на управление каналами"
            color = Color.red()
        if not content:
            embed = Embed(description=description, color=color)
        await message.reply(content=content, embed=embed, mention_author=False)


class LayoutTranslator:
    QWERTY = (
        "qwertyuiop[]asdfghjkl;'zxcvbnm,./"
        'QWERTYUIOP{}ASDFGHJKL:"ZXCVBNM<>?'
    )
    RUSSIAN = (
        "йцукенгшщзхъфывапролджэячсмитьбю."
        "ЙЦУКЕНГШЩЗХЪФЫВАПРОЛДЖЭЯЧСМИТЬБЮ,"
    )
    TRANSLATION_TABLE = "".maketrans(QWERTY, RUSSIAN)

    def translate(self, text: str) -> str:
        return text.translate(self.TRANSLATION_TABLE)


bot = MasterBot()
translator = LayoutTranslator()


@bot.tree.context_menu(name="Перевести с кристалийского")
async def translate_from_crystalian(
    ctx: Interaction,
    message: Message
) -> None:
    description = message.jump_url + "\n"
    message_text = message.content
    if message_text:
        description += translator.translate(message_text)
        color = Color.green()
    else:
        description += "Пусто"
        color = Color.red()
    embed = Embed(description=description, color=color)
    await ctx.response.send_message(embed=embed)


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
    basicConfig(level=ERROR)
    with Runner(loop_factory=new_event_loop) as runner:
        runner.run(main())
