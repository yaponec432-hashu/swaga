#!/usr/bin/env python3
# SPDX-License-Identifier: 0BSD
"""A discord bot."""

from asyncio import create_subprocess_exec, subprocess, Runner
from tempfile import NamedTemporaryFile
from logging import basicConfig, ERROR
from os import environ, remove
from io import BytesIO

from uvloop import new_event_loop
from discord import (
    app_commands,
    Interaction,
    Attachment,
    ClientUser,
    Message,
    Intents,
    Client,
    Member,
    File
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


@bot.tree.command(description="Сделать файл тг стикера")
@app_commands.describe(file="Видео/анимация")
async def tg_sticker(ctx: Interaction, file: Attachment) -> None:
    await ctx.response.defer()

    data = await file.read()
    with NamedTemporaryFile(delete=False) as temp_file:
        temp_file.write(data)
        path = temp_file.name

    try:
        decoder_flag = decoder = ""
        if file.filename.lower().endswith(".webm"):
            decoder_flag = "-c:v"
            decoder = "libvpx-vp9"

        proc = await create_subprocess_exec(
            "ffprobe", 
            "-v", "24",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            "-i", path,
            stdout=subprocess.PIPE
        )
        stdout, _ = await proc.communicate()
        duration = float(stdout.decode())
        speed = duration/2.9 if duration > 3.0 else 1.0

        cmd = (
            "ffmpeg",
            "-v", "24",
            decoder_flag, decoder,
            "-i", path,
            "-an",
            "-c:v", "libvpx-vp9",
            "-minrate", "416k",
            "-b:v", "416k",
            "-maxrate", "416k",
            "-deadline", "best",
            "-row-mt", "1",
            "-vf", f"setpts=PTS/{speed},scale=512:512,fps=30",
            "-pix_fmt", "yuva420p",
            "-fps_mode", "cfr",
            "-frame-parallel", "0",
            "-aspect", "1:1",
            "-g", "90",
            "-f", "webm",
            "--", "pipe:1"
        )

        cmd = tuple(i for i in cmd if i)
        proc = await create_subprocess_exec(*cmd, stdout=subprocess.PIPE)
        stdout, _ = await proc.communicate()
        buffer = BytesIO(stdout)
        text = "Лови аптечку"
        output_file=File(buffer, filename=file.filename + ".webm")
    except Exception:
        text = "Обшибка, попробуй другой формат файла"
        output_file = None
    finally:
        remove(path)
    await ctx.followup.send(text, file=output_file)


@bot.tree.command(description="Id чела")
@app_commands.describe(member="Чел")
async def ds_id(ctx: Interaction, member: Member) -> None:
    text = f"```{member.id}```"
    await ctx.response.send_message(text)


@bot.tree.command(description="Аватарка чела")
@app_commands.describe(member="Чел")
async def avatarka(ctx: Interaction, member: Member) -> None:
    text = member.display_avatar
    await ctx.response.send_message(text)


@bot.tree.command(description="Посчитать длину строки")
@app_commands.describe(text="3 хаммама прогревай быстрей")
async def length(ctx: Interaction, text: str) -> None:
    text = len(text)
    await ctx.response.send_message(text)


@bot.tree.command(description="Проверить синхронизацию")
async def check_sync(ctx: Interaction) -> None:
    text = "Ага" if bot.SYNC_ENABLED else "Нет нихуя"
    await ctx.response.send_message(text)


async def main() -> None:
    async with bot:
       await bot.start(environ["MASTER_TOKEN"])


if __name__ == "__main__":
    basicConfig(level=ERROR)
    with Runner(loop_factory=new_event_loop) as runner:
        runner.run(main())
