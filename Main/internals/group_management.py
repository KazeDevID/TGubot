# Copyright (C) 2021-present by X-SyntaxError, < https://github.com/X-SyntaxError


import time
import contextlib
from Main import TGubot
from pyrogram.client import Client
from ..core.decorators import check_perm
from Main.core.types.message import Message
from pyrogram.errors import UserAdminInvalid
from Main.plugins.userbot.channel_utils import digit_wrap
from pyrogram.types import ChatPrivileges, ChatPermissions


@TGubot.register_on_cmd(
    "pin",
    cmd_help={"help": "Sematkan pesan balasan", 
    "example": "pin (membalas pesan)"},
    requires_reply=True,
)
@check_perm("can_pin_messages")
async def pin(c: Client, msg: Message):
    _m = await msg.handle_message("PROCESSING")
    try:
        await c.pin_chat_message(msg.chat.id, msg.reply_to_message.id)
    except Exception as exception_:
        return await _m.edit_msg("UNABLE_TO_PIN", string_args=(exception_))
    await _m.edit_msg("PINNED")


@TGubot.register_on_cmd(
    "unpin",
    cmd_help={
        "help": "Lepas sematan pesan yang dibalas", 
        "example": "unpin (balas_ke_pesan)",
    requires_reply=True,
)
@check_perm("can_pin_messages")
async def unpin(c: Client, msg: Message):
    m = await msg.handle_message("PROCESSING")
    try:
        await c.unpin_chat_message(msg.chat.id, msg.reply_to_message.id)
    except Exception as exception_:
        return await m.edit_msg("UNABLE_TO_UNPIN", string_args=(exception_))
    await m.edit_msg("UNPINNED")


@TGubot.register_on_cmd(
    "ban",
    cmd_help={
        "help": "Larang pengguna dari obrolan dan batasi izinnya",
        "example": "ban (reply|username|id)",
    },
    group_only=True,
)
@check_perm("can_restrict_members")
async def ban(c: Client, m: Message):
    ms = await m.handle_message("PROCESSING")
    user_, reason_, is_chnnl = m.get_user
    if not user_:
        return await ms.edit_msg("INVALID_USER")
    dur, input_dur = m.extract_time
    try:
        u_ = await m.chat.ban_member(digit_wrap(user_), until_date=dur)
    except UserAdminInvalid:
        return await ms.edit_msg("NOT_PROPER_RIGHTS")
    except Exception as exception_:
        return await ms.edit_msg("UNABLE_TO_BAN", string_args=(exception_))
    input_dur = input_dur or "Forever"
    await ms.edit_msg(
        "BANNED_USER",
        string_args=(
            u_.left_chat_member.mention,
            reason_ or "Not specified",
            input_dur,
        ),
    )


@TGubot.register_on_cmd(
    "unban",
    cmd_help={
        "help": "Batalkan larangan pengguna dari obrolan dan pulihkan izinnya",
        "example": "unban (reply|username|id)",
    },
    group_only=True,
)
@check_perm("can_restrict_members")
async def unban(c: Client, m: Message):
    ms = await m.handle_message("PROCESSING")
    user_, reason, is_chnnl = m.get_user
    if not user_:
        return await ms.edit_msg("INVALID_USER")
    try:
        await m.chat.unban_member(digit_wrap(user_))
    except UserAdminInvalid:
        return await ms.edit_msg("NOT_PROPER_RIGHTS")
    except Exception as exception_:
        return await ms.edit_msg("UNABLE_TO_BAN", string_args=(exception_))
    u_ser = await c.get_users(user_)
    await ms.edit_msg("UNBANNED_USER", string_args=(u_ser.mention))


@TGubot.register_on_cmd(
    "mute",
    cmd_help={
        "help": "Larang pengguna mengirim pesan dalam obrolan",
        "example": "mute (reply|username|id)",
    },
    group_only=True,
)
@check_perm("can_restrict_members")
async def mute(c: Client, m: Message):
    ms = await m.handle_message("PROCESSING")
    user_, reason_, is_chnnl = m.get_user
    if not user_:
        return await ms.edit_msg("INVALID_USER")
    dur, input_dur = m.extract_time
    try:
        await c.restrict_chat_member(
            m.chat.id,
            digit_wrap(user_),
            ChatPermissions(can_send_messages=False),
            until_date=dur,
        )
    except UserAdminInvalid:
        return await ms.edit_msg(TGubot.get_string("NOT_PROPER_RIGHTS"))
    except Exception as exception_:
        return await ms.edit_msg(
            TGubot.get_string("UNABLE_TO_MUTE").format(exception_)
        )
    user_info = await c.get_users(user_)
    input_dur = input_dur or "Forever"
    await ms.edit_msg(
        "MUTED_USER",
        string_args=(user_info.mention, reason_ or "Not specified", input_dur),
    )


@TGubot.register_on_cmd(
    "unmute",
    cmd_help={
        "help": "Izinkan kembali pengguna untuk mengirim pesan dalam obrolan",
        "example": "unmute <reply/username/id>",
    },
    group_only=True,
)
@check_perm("can_restrict_members")
async def unmute(c: Client, m: Message):
    ms = await m.handle_message("PROCESSING")
    user_, reason_, is_chnnl = m.get_user
    if not user_ or not is_chnnl:
        return await ms.edit_msg("INVALID_USER")
    try:
        await c.restrict_chat_member(
            m.chat.id, digit_wrap(user_), ChatPermissions(can_send_messages=True)
        )
    except UserAdminInvalid:
        return await ms.edit_msg("NOT_PROPER_RIGHTS")
    except Exception as exception_:
        return await ms.edit_msg("UNABLE_TO_UNMUTE", string_args=(exception_))
    user_info = await c.get_users(user_)
    await m.edit_msg("UNMUTED_USER", string_args=(user_info.mention))


@TGubot.register_on_cmd(
    "kick",
    cmd_help={
        "help": "Kick pengguna dari chat, Dia dapat bergabung kembali jika diinginkan",
        "example": "kick (reply|username|id)",
    },
    group_only=True,
)
@check_perm("can_restrict_members")
async def kick(c: Client, m: Message):
    ms = await m.handle_message("PROCESSING")
    user_, reason_, is_chnnl = m.get_user
    if not user_:
        return await ms.edit_msg("INVALID_USER")
    try:
        u_ = await m.chat.ban_member(digit_wrap(user_))
        await m.chat.unban_member(digit_wrap(user_))
    except UserAdminInvalid:
        return await ms.edit_msg("NOT_PROPER_RIGHTS")
    except Exception as exception_:
        return await ms.edit_msg("UNABLE_TO_KICK", string_args=(exception_))
    await ms.edit_msg("ALREADY_KICKED") if u_ is True else await ms.edit_msg(
        "KICKED_USER",
        string_args=(u_.left_chat_member.mention, reason_ or "Not specified"),
    )


@TGubot.register_on_cmd(
    "promote",
    cmd_help={
        "help": "mempromosikan pengguna dalam obrolan grup dengan izin khusus.",
        "example": "promote (username | reply to user)",
        "user_args": {
            "cci": "Bisa ganti info", 
            "cdm": "Dapat menghapus pesan", 
            "ciu": "Dapat mengundang anggota.", 
            "cpm": "Dapat menyematkan pesan", 
            "crm": "Dapat membatasi anggota", 
            "pro": "Dapat mempromosikan anggota", 
            "cmvc": "Dapat mengatur obrolan suara", 
            "anon": "Jadikan pengguna anonim",
        },
    },
    group_only=True,
    disallow_if_sender_is_channel=True,
)
@check_perm("can_promote_members", return_perm=True)
async def promote(c: Client, m: Message, my_perms: ChatPermissions):
    ms = await m.handle_message("PROCESSING")
    user_, a_title, is_chnnl = m.get_user
    args = m.user_args
    permissions = ChatPrivileges(
        can_change_info="-cci" in args or my_perms["can_change_info"],
        can_delete_messages="-cdm" in args or my_perms["can_delete_messages"],
        can_invite_users="-ciu" in args or my_perms["can_invite_users"],
        can_pin_messages="-cpm" in args or my_perms["can_pin_messages"],
        can_promote_members="-pro" in args or my_perms["can_promote_members"],
        can_restrict_members="-crm" in args or my_perms["can_restrict_members"],
        can_manage_chat="-cmc" in args or my_perms["can_manage_chat"],
        can_manage_video_chats="-cmvc" in args or my_perms["can_manage_voice_chats"],
        is_anonymous="-anon" in args,
    )
    if not user_:
        return await ms.edit_msg("INVALID_USER")
    try:
        await c.promote_chat_member(
            m.chat.id, digit_wrap(user_), privileges=permissions
        )
    except Exception as e:
        return await ms.edit_msg("PROMOTE_FAILED", string_args=(e))
    if a_title and m.chat.type == "supergroup":
        with contextlib.suppress(Exception):
            await c.set_administrator_title(m.chat.id, user_, a_title)
    user_info, a_title = await c.get_users(user_), a_title or "Admin"
    await ms.edit_msg("PROMOTED", string_args=(user_info.mention, a_title))


@TGubot.register_on_cmd(
    "demote",
    cmd_help={
        "help": "turunkan pengguna di obrolan grup",
        "example": "demote (username | reply to user)",
    },
    group_only=True,
    disallow_if_sender_is_channel=True,
)
@check_perm("can_promote_members")
async def promote(c: Client, m: Message):
    ms = await m.handle_message("PROCESSING")
    user_, a_title, is_chnnl = m.get_user
    if not user_:
        return await ms.edit_msg("INVALID_USER")
    try:
        await c.promote_chat_member(
            m.chat.id,
            digit_wrap(user_),
            ChatPrivileges(
                is_anonymous=False,
                can_change_info=False,
                can_edit_messages=False,
                can_manage_video_chats=False,
                can_manage_chat=False,
                can_delete_messages=False,
                can_restrict_members=False,
                can_invite_users=False,
                can_pin_messages=False,
                can_promote_members=False,
            ),
        )
    except Exception as e:
        return await ms.edit_msg("DEMOTE_FAILED", string_args=(e))
    user_info = await c.get_users(user_)
    await ms.edit_msg("DEMOTED", string_args=(user_info.mention))


@TGubot.register_on_cmd(
    "purge",
    cmd_help={
        "help": "Bersihkan pesan dalam obrolan grup",
        "example": "purge (replying to start message)",
    },
    requires_reply=True,
)
@check_perm("can_delete_messages")
async def purge(c: Client, m: Message):
    start_time = time.time()
    ms = await m.handle_message("PROCESSING")
    no_of_msg_purged = 0
    ids = []
    for msg_id in range(m.reply_to_message.id, m.id):
        if msg_id not in [m.id, ms.id]:
            no_of_msg_purged += 1
            ids.append(msg_id)
            if len(ids) >= 100:
                await c.delete_messages(chat_id=m.chat.id, message_ids=ids, revoke=True)
                ids.clear()
    if ids:
        await c.delete_messages(chat_id=m.chat.id, message_ids=ids, revoke=True)
    end_time = time.time()
    time_taken = round((end_time - start_time) * 1000, 2)
    await ms.edit_msg("PURGED", string_args=(time_taken, no_of_msg_purged))
    time.sleep(5)
    await ms.delete()
