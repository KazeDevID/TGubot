# Copyright (C) 2021-present by X-SyntaxError, < https://github.com/X-SyntaxError


import asyncio
from Main import TGubot
from style import ping_format as pf
from pyrogram import Client, filters
from Main.core.types.message import Message
from Main.core.decorators import log_errors, iuser_check, inline_check
from pyrogram.types import (
    Message, InlineQuery, CallbackQuery, InlineKeyboardButton,
    InlineKeyboardMarkup, InputTextMessageContent, InlineQueryResultArticle)


@TGubot.bot.on_callback_query(filters.regex("^(restart|reload)_confirm"))
@log_errors
@iuser_check
async def restart_cb_handler(_, cb: CallbackQuery):
    await cb.answer("Hang on..", show_alert=True)
    _type = cb.matches[0].group(1)
    if _type == "restart":
        text = "<i>Restart baru akan dimulai dalam beberapa detik.</i>"
        soft = False
    else:
        text = "<i>Pemuatan ulang akan dimulai dalam beberapa detik.</i>"
        soft = True
    await cb.edit_message_text(text)
    await TGubot.reboot(soft, last_msg=cb)


@TGubot.bot.on_callback_query(filters.regex("^(restart|reload)_cancel"))
@log_errors
@iuser_check
async def restart_cb_handler(c: Client, cb: CallbackQuery):
    await cb.answer("Alright", show_alert=True)
    _type = cb.matches[0].group(1)
    soft = _type != "restart"
    await cb.edit_message_text(
        f"<i>Aborted {'reload' if soft else 'restart'}.</i>",
    )


@TGubot.bot.on_message(
    filters.command(["restart", "reload"], "/") & filters.user(TGubot.config.OWNER_ID)
)
@log_errors
async def restart_command_handler(_, m: Message):
    reload_only = m.command[0] == "reload"
    await m.reply(
        f"<b>Apakah Anda yakin tentang {'reload' if reload_only else 'restarting'} TGubot?</b>\n\n<i>Ini akan menghentikan semua proses yang sedang berlangsung dan {'reload' if reload_only else 'restart'} akan memakan waktu beberapa waktu.</i>",
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "Yes", f"{'reload' if reload_only else 'restart'}_confirm"
                    ),
                    InlineKeyboardButton(
                        "No", f"{'reload' if reload_only else 'restart'}_cancel"
                    ),
                ]
            ]
        ),
    )


@TGubot.bot.on_inline_query(filters.regex("^(restart|reload)"))
@log_errors
@iuser_check
async def ping_inline_handler(_, iq: InlineQuery):
    soft = iq.query.lower() == "reload"
    await iq.answer(
        [
            InlineQueryResultArticle(
                id=1,
                title=f"{'Reload' if soft else 'Restart'} confirmation mesage",
                description=TGubot.get_string(
                    "INTERNAL_FUNCTION", args=pf["ping_emoji2"]
                ),
                input_message_content=InputTextMessageContent(
                    f"<b>Apakah Anda yakin tentang {'reload' if soft else 'restart'} TGubot?</b>\n\n<i>Ini akan menghentikan semua proses yang sedang berlangsung dan restart akan memakan waktu.</i>",
                ),
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                "Yes", f"{'reload' if soft else 'restart'}_confirm"
                            ),
                            InlineKeyboardButton(
                                "No", f"{'reload' if soft else 'restart'}_cancel"
                            ),
                        ]
                    ]
                ),
            )
        ],
        cache_time=0,
        is_personal=True,
        switch_pm_text="Internal Function",
        switch_pm_parameter="inline_help",
    )


@TGubot.register_on_cmd(
    ["restart", "reload"],
    bot_mode_unsupported=True,
    cmd_help={
        "help": "Mulai ulang bot pengguna",
        "example": "restart",
        "user_args": {
            "r": "Cukup muat ulang plugin alih-alih melakukan restart penuh."
        },
    },
)
@inline_check
async def restart_ub_cmd(c: Client, m: Message):
    reload = m.command == "reload"
    rm = m.reply_to_message
    results = await c.get_inline_bot_results(
        TGubot.bot_info.username, "reload" if reload else "restart"
    )
    await asyncio.gather(
        *[
            c.send_inline_bot_result(
                chat_id=m.chat.id,
                query_id=results.query_id,
                result_id=results.results[0].id,
                reply_to_message_id=rm.id if rm else m.id,
            ),
            m.delete_if_self(),
        ]
    )
