# Copyright (C) 2021-present by X-SyntaxError, < https://github.com/X-SyntaxError


import time
import asyncio
from Main import TGubot
from pyrogram import Client, filters
from Main.core.types.message import Message
from Main.utils.essentials import Essentials


MENTIONED = []
afk_sanity_check: dict = {}


@TGubot.register_on_cmd(
    "afk",
    bot_mode_unsupported=True,
    cmd_help={
        "help": "Setel AFK.",
        "example": "afk saya mau berak ",
        "user_args": {
            "Sembunyikan yang terakhir terlihat di afk.", 
            "dlm": "Tidak mencatat pesan yang disebutkan.",
        },
    },
)
async def afk(c: Client, m: Message):
    user_args = m.user_args
    afk_time = int(time.time())
    reason = m.user_input
    result = await TGubot.db.settings_col.find_one(
        {"_id": "AFK", "client_id": c.myself.id}
    )
    if result:
        await TGubot.db.settings_col.update_one(
            {"_id": "AFK", "client_id": c.myself.id},
            {
                "$set": {
                    "afk_time": afk_time,
                    "reason": reason,
                    "dlm": "-dlm" in user_args,
                    "hls": "-hls" in user_args,
                }
            },
        )
    else:
        await TGubot.db.settings_col.insert_one(
            {
                "_id": "AFK",
                "client_id": c.myself.id,
                "afk_time": afk_time,
                "reason": reason,
                "dlm": "-dlm" in user_args,
                "hls": "-hls" in user_args,
            }
        )
    await m.handle_message("GOING_AFK", del_in=7)


async def user_afk(filter, c: TGubot, m: Message):
    afk = await TGubot.db.settings_col.find_one(
        {"_id": "AFK", "client_id": c.myself.id}
    )
    return bool(afk)


@TGubot.on_message(
    filters.create(user_afk) & filters.mentioned & ~filters.bot,
    bot_mode_unsupported=True,
)
async def afk_mentioned(c: Client, m: Message):
    global MENTIONED
    user = m.from_user
    user_id = int(user.id)
    if user_id not in afk_sanity_check.keys():
        afk_sanity_check[user_id] = 1
    else:
        afk_sanity_check[user_id] += 1
    if afk_sanity_check[user_id] == 4:
        afk_sanity_check[user_id] += 1
        return
    if afk_sanity_check[user_id] > 3:
        return
    result = await TGubot.db.settings_col.find_one(
        {"_id": "AFK", "client_id": c.myself.id}
    )
    afk_time = result["afk_time"]
    hls = result["hls"]
    dlm = result["dlm"]
    if hls:
        afk_since = TGubot.get_string("AFK_SINCE")
    else:
        afk_since = Essentials.get_readable_time(time.time() - afk_time)
    if reason := result["reason"]:
        await m.reply_msg("USER_AFK", string_args=(afk_since, reason))
    else:
        await m.reply_msg("USER_AFK_NO_REASON", string_args=(afk_since))
    if not dlm:
        chat = m.chat
        chat_id = str(chat.id)[4:] if "-" in str(chat.id) else str(chat.id)
        MENTIONED.append(
            {
                "user": user.first_name,
                "chat": chat.title,
                "chat_id": chat_id,
                "id": m.id,
            }
        )


@TGubot.on_message(
    filters.create(user_afk) & filters.outgoing, bot_mode_unsupported=True
)
async def set_unafk(c: Client, m: Message):
    global MENTIONED
    await TGubot.db.settings_col.delete_one({"_id": "AFK", "client_id": c.myself.id})
    _m_ = await c.send_message(m.chat.id, TGubot.get_string("NO_AFK"))
    await asyncio.sleep(7)
    await _m_.delete()
    if MENTIONED:
        if not TGubot.log_chat:
            return
        text = TGubot.get_string("AFK_MENTION", args=(len(MENTIONED)))
        for msg in MENTIONED:
            text += TGubot.get_string(
                "AFK_MENTION_DETAILS",
                args=(msg["chat_id"], msg["id"], msg["user"], msg["chat"]),
            )
        await c.send_message(TGubot.log_chat, text)
        MENTIONED = []
    afk_sanity_check.clear()
