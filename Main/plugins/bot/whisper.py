# Copyright (C) 2021-present by X-SyntaxError, < https://github.com/X-SyntaxError


import uuid
from Main import TGubot
from Main.core.decorators import log_errors
from pyrogram import Client, enums, filters
from Main.plugins.userbot.channel_utils import digit_wrap
from pyrogram.types import (
    InlineQuery, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup,
    InputTextMessageContent, InlineQueryResultArticle)


MSGS_DICT = {}


@TGubot.bot.on_inline_query(filters.regex("^whisper"))
@log_errors
async def whisper(c: Client, iq: InlineQuery):
    if " " not in iq.query:
        return
    text = (iq.query.split("whisper ", 1)[1]).strip()
    if not text or "," not in text or (len(text.split(",", 1)) != 2):
        return
    _id = uuid.uuid1().int
    user, msg = text.split(",", 1)
    user = digit_wrap(user)
    user_trail = user
    if isinstance(user, int):
        user_trail = f"[User](tg://user?id={user})"
    elif not user.startswith("@"):
        user_trail = f"@{user}"
    MSGS_DICT[int(_id)] = dict(user=user, msg=msg)
    ans = [
        InlineQueryResultArticle(
            title=f"Whisper to {user_trail}",
            input_message_content=InputTextMessageContent(
                "<b>Bisikan Telah Dikirim Untuk {user}</b>\nKlik Di Bawah Untuk Memeriksa Pesan!\n<i>Catatan : Hanya Dia yang Dapat Membukanya!</i>".format(
                    user=user_trail
                ),
                parse_mode=enums.ParseMode.HTML,
            ),
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "Show Message",
                            callback_data=f"whisper_{_id}",
                        ),
                    ]
                ]
            ),
        )
    ]
    await iq.answer(ans, 0)


@TGubot.bot.on_callback_query(filters.regex("^whisper_(.*)"))
@log_errors
async def whisper_callback(c: Client, cq: CallbackQuery):
    _id = digit_wrap(cq.matches[0].group(1))
    if _id not in MSGS_DICT:
        return await cq.answer(TGubot.get_string("CACHE_LOST"), True)
    msg_dict = MSGS_DICT[_id]
    user_id_or_username = digit_wrap(msg_dict.get("user"))
    MSG = msg_dict.get("msg")
    if cq.from_user.id in TGubot.auth_users:
        return await cq.answer(MSG, True)
    if isinstance(user_id_or_username, int):
        if cq.from_user.id == int(user_id_or_username):
            return await cq.answer(MSG, True)
    elif cq.from_user.username:
        if user_id_or_username.startswith("@"):
            user_id_or_username = user_id_or_username.split("@", 1)[1]
        if cq.from_user.username in user_id_or_username:
            return await cq.answer(MSG, True)
    else:
        await cq.answer(TGubot.get_string("WHISPER_INVALID_USER"))
