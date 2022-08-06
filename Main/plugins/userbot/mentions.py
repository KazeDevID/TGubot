from Main import TGubot
from Main.core.types.message import Message
from pyrogram import Client, enums, filters
from pyrogram.types import (
    Message as RawMessage, InlineKeyboardButton, InlineKeyboardMarkup)


@TGubot.register_on_cmd(
    ["mentions"],
    cmd_help={
        "help": "To toggle notify mentions globally.",
        "example": "mentions (on/off)",
    },
    group_only=False,
    requires_input=True,
)
async def mention_settings_handler(c: Client, m: Message):
    msg = await m.handle_message("PROCESSING")
    value = False
    if m.user_input.lower() in ["on", "yes"]:
        value = True
        await msg.edit_msg("TURNED_ON_MENTIONS_GLOBALLY")
    elif m.user_input.lower() in ["off", "no"]:
        value = False
        await msg.edit_msg("TURNED_OFF_MENTIONS_GLOBALLY")
    else:
        return await msg.edit_msg("INVALID_INPUT")
    await TGubot.db.settings_col.update_one(
        {"_id": "MENTION_LOG", "client_id": c.myself.id},
        {
            "$set": {
                "value": value,
            }
        },
        upsert=True,
    )


@TGubot.on_message(
    filters.mentioned & filters.group & ~filters.user(TGubot.bot_info.id)
)
async def send_mention_log_handler(c: Client, m: RawMessage):
    link = f"https://t.me/{m.chat.username}" if m.chat.username else ""
    db_res = await TGubot.db.settings_col.find_one(
        {"_id": "MENTION_LOG", "client_id": c.myself.id}
    )
    if db_res and db_res.get("value"):
        await TGubot.bot.send_message(
            TGubot.log_chat,
            f"{c.myself.mention(style=enums.ParseMode.HTML)} [\u2063]({m.link}) was mentioned in <a href={link}>{m.chat.title}</a>",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton(f"🔗 Link", url=m.link)]]
            ),
        )
