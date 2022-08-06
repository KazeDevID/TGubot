# Copyright (C) 2022-present by X-SyntaxError, < https://github.com/X-SyntaxError


import os
import glob
import time
from Main import TGubot
from pyrogram import Client
from Main.core.types.message import Message
from Main.utils.essentials import Essentials


@TGubot.register_on_cmd(
    "alive",
    cmd_help={"help": "Cek status UB", "example": "alive"},
)
async def alive(c: Client, m: Message):
    version = TGubot.__version__
    uptime = Essentials.get_readable_time(time.time() - TGubot.start_time)
    path_ = "./cache/alive.*"
    file = glob.glob(path_)[0] if glob.glob(path_) else ""
    if os.path.exists(file):
        await m.reply_file(
            file, caption=TGubot.get_string("ALIVE_TEXT").format(version, uptime)
        )
        return await m.delete_if_self()
    await m.handle_message(TGubot.get_string("ALIVE_TEXT").format(version, uptime))
