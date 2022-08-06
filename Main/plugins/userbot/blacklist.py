# Copyright (C) 2022-present by X-SyntaxError, < https://github.com/X-SyntaxError

from Main import TGubot
from pyrogram import Client, filters
from Main.core.decorators import check_perm
from Main.core.types.message import Message


bl_db = TGubot.db.make_collection("BLACKLIST")
warn_count = {}


@TGubot.register_on_cmd(
    ["addblacklist", "abl"],
    cmd_help={
        "help": "Tambahkan pesan ke daftar hitam.",
        "example": "blacklist bokep",
        "user_args": {"w": "Set a warn limit for that blacklisted word"},
    },
    requires_input=True,
)
@check_perm("can_delete_messages")
async def add_blacklist_cmd_handler(c: Client, m: Message):
    user_args = m.user_args
    raw_text = m.user_input.lower().rstrip()
    my_id = c.myself.id
    if await bl_db.find_one(
        {"chat_id": m.chat.id, "bl_word": raw_text, "client_id": my_id}
    ):
        await m.handle_message(
            "ALREADY_BLACKLISTED", string_args=(raw_text, m.chat.title)
        )
        return ""
    warns = False
    if any("-w" in s for s in user_args):
        warns = [x for x in user_args if x.startswith("-w")][0][2:]
        if warns == "" or not warns.isdigit():
            return await m.handle_message("INVALID_BLACKLIST_SYNTAX")
        warns = int(warns)
    await bl_db.insert_one(
        {"chat_id": m.chat.id, "bl_word": raw_text, "warns": warns, "client_id": my_id}
    )
    await m.handle_message("WORD_BLACKLISTED", string_args=(raw_text))


@TGubot.register_on_cmd(
    ["blacklists", "listbl"],
    cmd_help={
        "help": "Menampilkan semua kata yang masuk daftar hitam dalam obrolan.",
        "example": "blacklists",
    },
)
async def list_blacklist_cmd_handler(c: Client, m: Message):
    processing_msg = await m.handle_message("PROCESSING")
    my_id = c.myself.id
    bldata = [i async for i in bl_db.find({"chat_id": m.chat.id, "client_id": my_id})]
    if not bldata:
        await processing_msg.edit_msg("NO_BLACKLIST")
        return ""
    result = TGubot.get_string("BLACKLIST_WORD", args=(m.chat.title))
    for bl_word in bldata:
        result += f"◍ <code>{bl_word['bl_word']}</code> \n"
    await processing_msg.edit(result)


@TGubot.register_on_cmd(
    ["delblacklist", "delbl", "rmbl"],
    cmd_help={
        "help": "Menghapus satu atau semua kata yang masuk daftar hitam dalam obrolan.",
        "example": "delbl test",
        "user_args": {"all": "Removes all blacklisted word in the chat"},
    },
)
async def delete_blacklist_cmd_handler(c: Client, m: Message):
    processing_msg = await m.handle_message("PROCESSING")
    user_args = m.user_args
    my_id = c.myself.id
    rmword = m.user_input.rstrip()
    bldata = [i async for i in bl_db.find({"chat_id": m.chat.id, "client_id": my_id})]
    if not bldata:
        await processing_msg.edit_msg("NO_BLACKLIST")
        return ""
    if "-all" in user_args:
        await bl_db.delete_many({"chat_id": m.chat.id, "client_id": my_id})
        await processing_msg.edit_msg("BL_REMOVE_ALL")
        return ""
    if not await bl_db.find_one(
        {"chat_id": m.chat.id, "bl_word": rmword, "client_id": my_id}
    ):
        await processing_msg.edit_msg("NOT_BLACKLISTED", string_args=(rmword))
        return ""
    await bl_db.delete_one(
        {"chat_id": m.chat.id, "bl_word": rmword, "client_id": my_id}
    )
    await processing_msg.edit_msg("BL_REMOVE", string_args=(rmword))


async def blchat(filter, c: Client, m: Message):
    chat = [
        i async for i in bl_db.find({"chat_id": m.chat.id, "client_id": c.myself.id})
    ]
    return bool(chat)


async def admin_or_sudo(c: Client, m: Message):
    status = (await c.get_chat_member(m.chat.id, m.from_user.id)).status
    return bool(
        status.ADMINISTRATOR or status.OWNER or m.from_user.id in TGubot.auth_users
    )


@TGubot.on_message(
    filters.create(blchat)
    & filters.incoming
    & filters.group
    & ~filters.bot
    & (filters.text | filters.caption)
)
async def del_blacklisted(c: Client, m: Message):
    msg = (m.text or m.caption).lower()
    my_id = c.myself.id
    split = msg.split(" ")
    for msg in split:
        data = await bl_db.find_one(
            {"chat_id": int(m.chat.id), "bl_word": msg, "client_id": my_id}
        )
        if data and await admin_or_sudo(c, m):
            if data["warns"]:
                if m.from_user.id not in warn_count.keys():
                    warn_count[m.from_user.id] = 1
                if warn_count[m.from_user.id] == data["warns"]:
                    await c.kick_chat_member(m.chat.id, m.from_user.id)
                    await c.send_message(
                        m.chat.id,
                        TGubot.get_string(
                            "BL_WARN_BAN", args=(m.from_user.first_name, m.from_user.id)
                        ),
                    )
                    del warn_count[m.from_user.id]
                if warn_count:
                    warn_count[m.from_user.id] += 1
            await m.delete()
