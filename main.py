#!/usr/bin/env python3
# SPDX-License-Identifier: 0BSD
"""A discord bot."""

from asyncio import create_subprocess_exec, subprocess, Runner
from tempfile import NamedTemporaryFile
from base64 import b64encode, b64decode
from logging import basicConfig, ERROR
from urllib.parse import quote_plus
from os import environ, remove

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
        basicConfig(level=ERROR)
        intents = Intents.default()
        intents.message_content = True
        super().__init__(chunk_guilds_at_startup=False, intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self) -> None:
        if self.SYNC_ENABLED:
            await self.tree.sync()


class LayoutTranslator:
    def __init__(self) -> None:
        qwerty = (
            """qwertyuiop[]asdfghjkl;'zxcvbnm,./"""
            """QWERTYUIOP{}ASDFGHJKL:"ZXCVBNM<>?"""
        )
        russian = (
            """йцукенгшщзхъфывапролджэячсмитьбю."""
            """ЙЦУКЕНГШЩЗХЪФЫВАПРОЛДЖЭЯЧСМИТЬБЮ,"""
        )
        self.table = "".maketrans(qwerty, russian)

    def translate(self, text: str) -> str:
        return text.translate(self.table)


bot = Bot()
translator = LayoutTranslator()


@bot.tree.context_menu(name="Перевести с кристалийского")
async def translate_from_crystalian(
    ctx: Interaction,
    message: Message
) -> None:
    message_text = message.content
    text = message.jump_url + "\n"
    text += translator.translate(message_text) if message_text else "*Пусто*"
    await ctx.response.send_message(text)


@bot.tree.command(description="Сделать файл тг стикера")
@app_commands.describe(file="Видео/анимация")
async def tg_sticker(ctx: Interaction, file: Attachment) -> None:
    #await ctx.response.defer()
    with NamedTemporaryFile(suffix=".webm", delete=False) as temp_file:
        output_path = temp_file.name
    data = await file.read()
    with NamedTemporaryFile(delete=False) as temp_file:
        temp_file.write(data)
        input_path = temp_file.name

    try:
        process = await create_subprocess_exec(
            "ffprobe", 
            "-v", "24",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            "-i", input_path,
            stdout=subprocess.PIPE
        )
        stdout, _ = await process.communicate()
        if process.returncode != 0:
            raise RuntimeError("ffprobe")

        duration = float(stdout.decode())
        target = 2.95
        speed = duration/target if duration > target else 1.0

        decoder_flag = decoder = ""
        bitrate = "544k"
        # Keep transparency
        if file.filename.lower().endswith(".webm"):
            decoder_flag = "-c:v"
            decoder = "libvpx-vp9"

        cmd = (
            "ffmpeg", "-y",
            "-v", "24",
            decoder_flag, decoder,
            "-i", input_path,
            "-an",
            "-c:v", "libvpx-vp9",
            "-minrate", bitrate,
            "-b:v", bitrate,
            "-maxrate", bitrate,
            "-bufsize", bitrate,
            "-auto-alt-ref", "0",
            "-frame-parallel", "0",
            "-cpu-used", "2",
            "-row-mt", "1",
            "-fps_mode", "cfr",
            "-vf", f"setpts=PTS/{speed},format=yuva420p,scale=512:512,fps=30",
            "-aspect", "1:1",
            "-g", "90",
            "-passlogfile", output_path
        )
        cmd = tuple(i for i in cmd if i)

        process = await create_subprocess_exec(
            *cmd,
            "-pass", "1",
            "-f", "null",
            "--", "/dev/null"
        )
        await process.communicate()
        if process.returncode != 0:
            raise RuntimeError("ffmpeg 1")

        process = await create_subprocess_exec(
            *cmd,
            "-pass", "2",
            "--", output_file
        )
        await process.communicate()
        if process.returncode != 0:
            raise RuntimeError("ffmpeg 2")

        text = "Лови аптечку"
        sticker_file = {"file": File(output_path, filename=f"tg_{file.filename}.webm")}
    except Exception:
        text = "Обшибка, попробуй другой формат файла"
        sticker_file = {}
    finally:
        remove(input_path)
        remove(output_path)
        remove(output_path + "-0.log")
    await ctx.response.send_message(text, **sticker_file)


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


@bot.tree.command(description="Закодировать в base64")
@app_commands.describe(text="Печатай текст")
async def base64_encode(ctx: Interaction, text: str) -> None:
    text = f"```{b64encode(text.encode()).decode()}```"
    await ctx.response.send_message(text)


@bot.tree.command(description="Декодировать из base64")
@app_commands.describe(base64_text="Печатай текст")
async def base64_decode(ctx: Interaction, base64_text: str) -> None:
    try:
        text = b64decode(base64_text, validate=False).decode(errors="ignore")
        if not text:
            raise RuntimeError("Empty")
    except Exception:
        text = "Нормальный base64 печатай"
    await ctx.response.send_message(text)


@bot.tree.command(description="Сделать QR код")
@app_commands.describe(text="Текст QR кода")
async def qr(ctx: Interaction, text: str) -> None:
    text = (
        "https://zxing.org/w/chart?cht=qr&chs=350x350&chld=L&choe=UTF-8&chl="
        + quote_plus(text)
    )
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
    with Runner(loop_factory=new_event_loop) as runner:
        runner.run(main())
