# Copyright (C) 2021-present by X-SyntaxError, < https://github.com/X-SyntaxError


import re
import glob
import asyncio
import contextlib
from Main import TGubot
from pyrogram import filters
from Main.core.decorators import log_errors
from pyrogram.types import (
    Message, ForceReply, CallbackQuery, KeyboardButton, ReplyKeyboardMarkup,
    ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup)


@TGubot.bot.on_message(filters.command("start", "/") & filters.private)
@log_errors
async def start_command_handler(_, m: Message):
    payload = m.text.replace("/start", "").strip()
    if not payload:
        path_ = "./cache/bot_st_media.*"
        file = (
            glob.glob(path_)[0] if glob.glob(path_) else "./Main/assets/images/logo.jpg"
        )
        await m.reply_file(
            file,
            caption=TGubot.get_string("BOT_ST_MSG").format(
                m.from_user.mention, TGubot.config.CUSTOM_BT_START_MSG or ""
            ),
            reply_markup=ReplyKeyboardRemove(),
            send_msg_if_file_invalid=True,
        )
        if TGubot.traning_wheels_protocol and m.from_user.id in TGubot.auth_users:
            await m.reply(
                "Anda harus menambahkan sesi pengguna untuk menonaktifkan TWP, apakah Anda ingin melanjutkan?",
                reply_markup=ReplyKeyboardMarkup(
                    [[KeyboardButton("Yeah sure")]],
                    resize_keyboard=True,
                    one_time_keyboard=True,
                ),
            )
            _ = await m.from_user.listen()
            await m.reply(
                "Baiklah, mari kita mulai.", reply_markup=ReplyKeyboardRemove()
            )
            await asyncio.sleep(1)
            await m.reply(
                "Apakah Anda sudah membuat sesi string?.",
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton("Yes", callback_data="session_yes"),
                            InlineKeyboardButton("No", callback_data="session_no"),
                        ]
                    ]
                ),
            )
    elif payload == "add_session":
        await m.reply("Baiklah, mari kita mulai.", reply_markup=ReplyKeyboardRemove())
        await asyncio.sleep(1)
        await m.reply(
            "Apakah Anda sudah membuat sesi string?.",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton("Yes", callback_data="session_yes"),
                        InlineKeyboardButton("No", callback_data="session_no"),
                    ]
                ]
            ),
        )


@TGubot.bot.on_callback_query(filters.regex("^add_session"))
@log_errors
async def add_session_menu_cb_handler(_, cb: CallbackQuery):
    await cb.message.edit(
        "Alright, let's get started.", reply_markup=ReplyKeyboardRemove()
    )
    await asyncio.sleep(1)
    await cb.message.reply(
        "Apakah Anda sudah membuat sesi string?.",
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("Yes", callback_data="session_yes"),
                    InlineKeyboardButton("No", callback_data="session_no"),
                ]
            ]
        ),
    )


@TGubot.bot.on_callback_query(filters.regex("^session_yes"))
@log_errors
async def add_session_cb_handler(_, cb: CallbackQuery):
    with contextlib.suppress(Exception):
        await cb.message.delete()
    await cb.message.reply(
        "Baiklah... kirimi saya sesi string Anda.\nGunakan /batal untuk membatalkan operasi saat ini.",
        reply_markup=ForceReply(),
    )
    # session = await cb.from_user.listen(filters.regex(r"(\S{300,400})",
    # timeout=600))
    while True:
        session: Message = await cb.from_user.listen(filters.text, timeout=600)
        if session.text.startswith("/"):
            await cb.message.reply("Proses saat ini dibatalkan.")
            return
        if match := re.search(r"(\S{300,400})", session.text):
            session = match[1]
            break
        else:
            await session.reply("Tolong kirimkan saya sesi string yang valid.", quote=True)
    status = await cb.message.reply(
        "<code>Memproses sesi string yang diberikan...</code>" )
    new_session = await TGubot.add_session(session, status)
    await new_session.send_message(
        TGubot.bot.info.id,
        "<b>telah berhasil terhubung dengan akun Anda!</b> \nSilakan kunjungi @KazeDevID untuk setiap support atau help!",
    )
