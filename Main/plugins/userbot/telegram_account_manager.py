# Copyright (C) 2021-present by X-SyntaxError, < https://github.com/X-SyntaxError

import os
from os import remove
from Main import TGubot
from pyrogram import Client
from Main.core.types.message import Message
from pyrogram.raw.types import Authorization
from pyrogram.raw.functions.account import CheckUsername, GetAuthorizations


@TGubot.register_on_cmd(
    ["set", "modify"],
    bot_mode_unsupported=True,
    cmd_help={
        "help": "Untuk mengubah pengaturan akun Anda yang berbeda",
        "example": "set -f <newname>",
        "user_args": {
            "f": "Untuk mengubah nama depan Anda.", "l": "Untuk mengubah nama belakang Anda.", "b": "Untuk mengubah bio Anda.", "p": "Untuk mengatur foto profil baru Anda.", "s": "Untuk mendapatkan sesi akun.", "u": "Untuk mengubah nama pengguna Anda.",
        },
    },
)
async def set(c: Client, m: Message):
    msg = await m.handle_message("PROCESSING")
    args = m.user_args
    if not args:
        return await m.handle_message("INPUT_REQUIRED")
    if "-f" in args:
        if not m.user_input:
            return await msg.edit("INPUT_REQUIRED")
        fname = m.text.split(None, 2)[2]
        await c.update_profile(first_name=fname)
        await m.handle_message(TGubot.get_string("CHANGE").format("FirstName", fname))
    elif "-l" in args:
        if not m.user_input:
            return await msg.edit("INPUT_REQUIRED")
        lname = m.text.split(None, 2)[2]
        await c.update_profile(last_name=lname)
        await m.handle_message(TGubot.get_string("CHANGE").format("LastName", lname))
    elif "-b" in args:
        if not m.user_input:
            return await msg.edit("INPUT_REQUIRED")
        bio = m.text.split(None, 2)[2]
        await c.update_profile(bio=bio)
        await m.handle_message(TGubot.get_string("CHANGE").format("Bio", bio))
    elif "-u" in args:
        if not m.user_input:
            return await msg.edit("INPUT_REQUIRED")
        uname = m.text.split(None, 2)[2].replace("@", "")
        check = await c.invoke(CheckUsername(username=uname))
        if not check:
            return await m.handle_message(
                TGubot.get_string("USERNAME_TAKEN").format(f"@{uname}")
            )
        await c.set_username(uname)
        await m.handle_message(TGubot.get_string("CHANGE").format("Username", uname))
    elif "-p" in args:
        if not m.reply_to_message:
            return await m.handle_message("REPLY_REQUIRED")
        reply = m.reply_to_message
        if not reply.photo:
            return await msg.edit("REPLY_PHOTO")
        pic = await c.download_media(reply.photo.file_id)
        await c.set_profile_photo(photo=pic)
        await m.handle_message("CHNG_PHOTO")
        if os.path.exists(pic):
            remove(pic)
    elif "-s" in args:
        sessions = (await c.invoke(GetAuthorizations())).authorizations
        text_ = f"<b>Sessions :</b> ({len(sessions)}) \n\n"
        for session in sessions:
            session: Authorization = session
            text_ += f"> <b>Device :</b> <code>{session.device_model} {session.platform} V{session.system_version}</code> \n<b>App :</b> <code>{session.app_name} V{session.app_version}</code> \n<b>Region :</b> <code>{session.country} - {session.region} ({session.ip})</code> \n\n"
        await m.handle_message(text_)
