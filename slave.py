#!/usr/bin/env python3
# SPDX-License-Identifier: 0BSD
"""A discord bot."""

from logging import basicConfig, ERROR
from asyncio import wait_for, Runner
from time import sleep
from os import environ

from uvloop import new_event_loop
from discord import (
    Intents,
    Client,
    Embed,
    Color,
    ClientUser,
    Message,
    HTTPException,
    Forbidden
)


class SlaveBot(Client):
    user: ClientUser
    INTENTS = Intents.default()
    INTENTS.message_content = True

    def __init__(self) -> None:
        super().__init__(chunk_guilds_at_startup=False, intents=self.INTENTS)
        self.sekai = SekaiManager()

    async def on_message(self, message: Message) -> None:
        await self.sekai.update_room_code(message)


class SekaiManager:
    def __init__(self) -> None:
        error = FileNotFoundError
        master_id = ""
        for _ in range(30):
            try:
                with open("master_id", "r") as file:
                    master_id += file.read()
            except error:
                sleep(1)
            if master_id:
                break
        if not master_id:
            raise error
        self.master_id = int(master_id)

    async def update_room_code(self, message: Message) -> None:
        """Backup sekai room code highlighting."""
        author = message.author
        if author.id != self.master_id:
            return
        message_text = message.content.split()
        if len(message_text) <= 1:
            return
        if int(message_text[0]) != self.master_id:
            return
        channel = message.channel
        name = message_text[1]
        if name == channel.name:
            return
        new_room_code = message_text[2]
        content = embed = None
        try:
            description = f"# `{new_room_code}`\nНовый код румы"
            color = Color.green()
            async with channel.typing():
                await wait_for(channel.edit(name=name), timeout=2.0)
        except (TimeoutError, HTTPException):
            content = (
                "# :warning: Используй эту команду:"
                f"```%rm {new_room_code}```"
            )
        except Forbidden:
            description = "**У меня нет прав** на управление каналами"
            color = Color.red()
        if not content:
            embed = Embed(description=description, color=color)
        await message.reply(content=content, embed=embed, mention_author=False)


bot = SlaveBot()


async def main() -> None:
    token = environ["SLAVE_TOKEN"]
    async with bot:
        await bot.start(token)


if __name__ == "__main__":
    basicConfig(level=ERROR)
    with Runner(loop_factory=new_event_loop) as runner:
        runner.run(main())
