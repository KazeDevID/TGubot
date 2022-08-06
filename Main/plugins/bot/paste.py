# Copyright (C) 2022-present by X-SyntaxError, < https://github.com/X-SyntaxError


import os
from Main import TGubot
from pyrogram import filters
from Main.utils.paste import Paste
from Main.core.types.message import Message
from Main.utils.essentials import Essentials
from Main.utils.helpers import arrange_buttons
from Main.core.decorators import log_errors, iuser_check
from pyrogram.types import (
    InlineQuery, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup,
    InputTextMessageContent, InlineQueryResultArticle)


@TGubot.bot.on_message(
    filters.command("paste", "/") & filters.user(TGubot.config.OWNER_ID)
)
@log_errors
async def paste_bot_cmd_handler(_, m: Message):
    if mess := m.reply_to_message:
        if mess.text:
            text = mess.text
        elif mess.document:
            _file = await mess.download("temp/")
            text = open(_file, "rb").read()
            os.remove(_file)
        elif mess.caption:
            text = mess.caption
        else:
            return await m.reply(TGubot.get_string("REPLY_PASTE_NOT_SUPPORTED"))
    else:
        text = m.raw_user_input
    if not text:
        return await m.reply(TGubot.get_string("PASTE_SOURCE_NOT_PROVIDED"))
    service, link = await Paste(text, author=TGubot.ourselves[0].first_name).paste()
    await m.reply(TGubot.get_string("PASTE_TEXT").format(link, service))


@TGubot.bot.on_callback_query(filters.regex(r"paste_to_(\w+)#(\w+)"))
@log_errors
@iuser_check
async def paste_cb_handler(_, cb: CallbackQuery):
    await cb.answer(
        Essentials.clean_html(TGubot.get_string("PLEASE_WAIT")), show_alert=True
    )
    service = cb.matches[0].group(1)
    text = TGubot.local_db.get_from_col("paste", cb.matches[0].group(2))
    if not text:
        return await cb.edit_message_text(TGubot.get_string("DB_KEY_NOT_FOUND"))
    service, link = await Paste(
        text, author=TGubot.ourselves[0].first_name, service=service
    ).paste()
    await cb.edit_message_text(
        TGubot.get_string("PASTE_TEXT").format(link, service),
        disable_web_page_preview=True,
    )


@TGubot.bot.on_inline_query(
    filters.regex(
        r"(paste_url\:((?:(?:https?:\/\/)?[\w-]+(?:\.[\w-]+)+\.?(?::\d+)?(?:\/\S*)?))|paste_menu\:(\w+))"
    )
)
@log_errors
@iuser_check
async def paste_inline_handler(_, iq: InlineQuery):
    if iq.matches[0].group(1).startswith("paste_menu"):
        buttons = arrange_buttons(
            [
                InlineKeyboardButton(
                    service.title(),
                    callback_data=f"paste_to_{service}#{iq.matches[0].group(3)}",
                )
                for service in Paste().all_bins
            ]
        )
        await iq.answer(
            [
                InlineQueryResultArticle(
                    title="Paste menu",
                    description="Tempel teks ke Bin tertentu",
                    input_message_content=InputTextMessageContent(
                        "Layanan mana yang ingin Anda gunakan?" ),
                    reply_markup=InlineKeyboardMarkup(buttons),
                )
            ],
            cache_time=0,
            is_personal=True,
            switch_pm_text="Paste Menu",
            switch_pm_parameter="paste",
        )

    else:
        url = iq.matches[0].group(2)
        await iq.answer(
            [
                InlineQueryResultArticle(
                    title=f"Paste {url}",
                    description="Paste Internal Function",
                    thumb_url=TGubot.config.GEAR_THUMB,
                    input_message_content=InputTextMessageContent(
                        TGubot.get_string("PASTE_TEXT").format(url, "bin"),
                    ),
                    reply_markup=InlineKeyboardMarkup(
                        [[InlineKeyboardButton("URL", url=url)]]
                    ),
                )
            ],
            cache_time=0,
            is_personal=True,
            switch_pm_text="Paste Menu",
            switch_pm_parameter="paste",
        )
