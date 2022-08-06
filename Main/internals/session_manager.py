# Copyright (C) 2021-present by X-SyntaxError, < https://github.com/X-SyntaxError


from Main import TGubot
from pyrogram import filters
from Main.core.decorators import log_errors
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup


@TGubot.bot.on_message(filters.command("add", "/") & filters.user(TGubot.auth_users))
@log_errors
async def add_session_command_handler(_, m: Message):
    if m.from_user.id not in TGubot.auth_users:
        return await m.reply_text("Hei, aku hanya bot. Didukung oleh @KazeDevID.")
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
