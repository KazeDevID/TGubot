# Copyright (C) 2022-present by X-SyntaxError, < https://github.com/X-SyntaxError

from Main import TGubot
from pyrogram import Client
from Main.core.types.message import Message


bcast_db = TGubot.db.make_collection("Broadcast")


@TGubot.register_on_cmd(
    ["badd", "broadcastadd", "bcastadd"],
    bot_mode_unsupported=True,
    cmd_help={
        "help": "Add the chat to the db",
        "example": "badd <chatid>",
    },
)
async def bcast_add(c: Client, m: Message):
    msg = await m.handle_message("PROCESSING")
    my_id = c.myself.id
    if m.user_input:
        chat_id = m.user_input
        if not chat_id.isdigit():
            return await msg.edit("Invalid chat id")
    else:
        chat_id = m.chat.id
    check = await bcast_db.find_one({"chat_id": int(chat_id), "client_id": my_id})
    if check:
        return await msg.edit("This chat is already in database.")
    await bcast_db.insert_one({"chat_id": int(chat_id), "client_id": my_id})
    await msg.edit(f"Added <code>{chat_id}</code> to the database")


@TGubot.register_on_cmd(
    ["bremove", "brm", "broadcastremove", "broadcastrm", "bcastrm", "bcastremove"],
    bot_mode_unsupported=True,
    cmd_help={
        "help": "Hapus obrolan dari db",
        "example": "bcastrm <chatid>",
    },
)
async def bcast_remove(c: Client, m: Message):
    msg = await m.handle_message("PROCESSING")
    if m.user_input:
        chat_id = m.user_input
        if not chat_id.isdigit():
            return await msg.edit("Invalid chat id")
    else:
        chat_id = m.chat.id
    check = await bcast_db.find_one({"chat_id": int(chat_id), "client_id": c.myself.id})
    if not check:
        return await msg.edit("Obrolan ini tidak ada di db")
    await bcast_db.delete_one({"chat_id": int(chat_id), "client_id": c.myself.id})
    await msg.edit(f"Deleted <code>{chat_id}</code> from the database")


@TGubot.register_on_cmd(
    ["bcast", "broadcast"],
    bot_mode_unsupported=True,
    cmd_help={
        "help": "Untuk menyiarkan pesan balasan",
        "example": "bcast <replyt_o_msg>",
    },
    requires_reply=True,
)
async def broadcast(c: Client, m: Message):
    success = 0
    err = 0
    msg = await m.handle_message("PROCESSING")
    chats = []
    async for x in bcast_db.find({"client_id": c.myself.id}):
        chats.append(x["chat_id"])
    if not chats:
        return await msg.edit("Tidak ada obrolan yang disimpan di db")
    for chat in chats:
        try:
            await c.copy_message(
                chat_id=int(chat),
                from_chat_id=m.chat.id,
                message_id=m.reply_to_message.id,
            )
            success += 1
        except Exception:
            TGubot.log()
            err += 1
    await msg.edit(
        f"Berhasil disiarkan di obrolan <code>{success}</code> dan kesalahan di obrolan <code>{err}</code>!"
    )
