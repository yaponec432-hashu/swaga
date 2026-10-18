#!/usr/bin/env python3
# SPDX-License-Identifier: 0BSD
"""A discord bot."""

from logging import basicConfig, ERROR
from io import BytesIO
from asyncio import (
    create_subprocess_exec,
    subprocess,
    wait_for,
    Runner
)
from os import environ

from uvloop import new_event_loop
from discord import (
    Attachment,
    app_commands,
    Intents,
    Client,
    Embed,
    Color,
    File,
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


@bot.tree.command(description="Сделать файл тг стикера")
@app_commands.describe(file="Видео/анимация")
async def tg_sticker(ctx: Interaction, file: Attachment) -> None:
    #await ctx.response.defer()
    data = await file.read()

    proc = await create_subprocess_exec(
        "ffmpeg",
        "-v", "24",
        "-stats",
        "-i", "pipe:0",
        "-f", "null",
        "/dev/null",
        stdin=subprocess.PIPE,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE
    )
    _, stderr = await proc.communicate(data)
    output = stderr.decode()
    duration = float(
        output.split("time=")[1].split()[0].split(":")[2]
    )
    speed = duration/2.9 if duration > 3.0 else 1.0

    decoder_flag = decoder = ""
    if file.filename.lower().endswith(".webm"):
        decoder_flag = "-c:v"
        decoder = "libvpx-vp9"

    proc = await create_subprocess_exec(
        "ffmpeg",
        "-v", "24",
        decoder_flag, decoder,
        "-i", "pipe:0",
        "-an",
        "-c:v", "libvpx-vp9",
        "-crf", "42",
        "-b:v", "704k",
        "-deadline", "best",
        "-row-mt", "1",
        "-vf", f"setpts=PTS/{speed},scale=512:512",
        "-aspect", "1:1",
        "-fpsmax", "30",
        "-g", "90",
        "-f", "webm",
        "--", "pipe:1",
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
    )
    stdout, _ = await proc.communicate(data)

    buffer = BytesIO(stdout)
    await ctx.response.send_message(
        file=File(buffer, filename=file.filename + ".webm")
    )


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
