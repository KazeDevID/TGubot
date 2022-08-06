# Copyright (C) 2021-present by X-SyntaxError, < https://github.com/X-SyntaxError


import asyncio
import logging
import contextlib
from Main import TGubot
from pyrogram import Client, filters
from Main.core.decorators import log_errors
from pyrogram.types import (
    Message, ForceReply, CallbackQuery, KeyboardButton, ReplyKeyboardMarkup,
    ReplyKeyboardRemove)
from pyrogram.errors import (
    FloodWait, ApiIdInvalid, UsernameInvalid, PhoneCodeExpired,
    PhoneCodeInvalid, UsernameOccupied, PhoneNumberInvalid,
    UsernameNotModified, SessionPasswordNeeded)


async def client_session(api_id, api_hash):
    return Client(
        "new_session", api_id=int(api_id), api_hash=str(api_hash), in_memory=True
    )


@TGubot.bot.on_callback_query(filters.regex("^session_no"))
@log_errors
async def add_session_cb_handler(_, cb: CallbackQuery):
    with contextlib.suppress(Exception):
        await cb.message.delete()
    await cb.message.reply(
        "Baiklah... Bagikan kontak Anda dengan saya untuk mengambil nomor telepon Anda.\n<i>Instance TGubot ini hanya milik Anda sehingga Anda tidak perlu khawatir dengan data Anda.</i>\n\nGunakan /cancel untuk membatalkan operasi saat ini.",
        reply_markup=ReplyKeyboardMarkup(
            [[KeyboardButton("Share Contact", request_contact=True)]],
            resize_keyboard=True,
            one_time_keyboard=True,
        ),
    )
    while True:
        response: Message = await cb.from_user.listen(timeout=60)
        if response.contact:
            phone_number = response.contact.phone_number
            TGubot.log(f"{phone_number=}", level=logging.DEBUG)
            break
        elif response.text == "/cancel":
            await cb.message.reply(
                "Proses saat ini dibatalkan.", reply_markup=ReplyKeyboardRemove()
            )
            return
        await response.reply("jenis pesan tidak valid. Silakan coba lagi.", quote=True)
    process_msg = await response.reply(
        "<i>Harap tunggu sampai saya membuat sesi untuk akun ini!</i>"
    )

    try:
        app = await client_session(
            api_id=TGubot.config.API_ID, api_hash=TGubot.config.API_HASH
        )
    except Exception as err:
        await process_msg.reply(f"Ada yang tidak beres!\n{err}")
        await process_msg.delete()
        return
    try:
        await app.connect()
    except ConnectionError:
        await app.disconnect()
        await app.connect()
    try:
        sent_code = await app.send_code(phone_number)
    except FloodWait as e:
        await process_msg.reply(
            f"Tidak dapat membuat sesi!.\nAnda memiliki waktu tunggu <code>{e.value} detik</code>."
        )
        await process_msg.delete()
        return
    except PhoneNumberInvalid:
        await process_msg.reply(
            "Telegram mengatakan bahwa nomor telepon yang Anda berikan tidak valid.\nhmm... aneh"
        await process_msg.delete()
        return
    except ApiIdInvalid:
        await process_msg.reply(
            "Telegram mengatakan bahwa ID API yang Anda berikan tidak valid.\nhmm... aneh"
        )
        await process_msg.delete()
        return
    ans = await cb.from_user.ask(
        "Sekarang, Kirimkan saya kode Anda dalam format <code>1-2-3-4-5</code> dan bukan <code>12345</code>",
        reply_markup=ForceReply(selective=True),
    )
    await process_msg.delete()
    if ans.text == "/cancel":
        await process_msg.reply("Membatalkan tindakan saat ini!", quote=True)
        return
    try:
        await app.sign_in(phone_number, sent_code.phone_code_hash, ans.text)
    except SessionPasswordNeeded:
        await asyncio.sleep(3)
        ans = await cb.from_user.ask(
            "Nomor Telegram yang dimasukkan dilindungi dengan 2FA. Harap masukkan kode autentikasi faktor kedua Anda.\n<i>Pesan ini hanya akan digunakan untuk membuat sesi string Anda, dan tidak akan pernah digunakan untuk tujuan lain selain yang diminta.</i>",
            reply_markup=ForceReply(selective=True),
            filters=filters.text,
        )
        if ans.text == "/cancel":
            await process_msg.reply("Membatalkan tindakan saat ini!", quote=True)
            return
        try:
            await app.check_password(ans.text)
        except Exception as err:
            await ans.reply(f"Ada yang tidak beres!\n{err}")
            return
    except PhoneCodeInvalid:
        await ans.reply("Kode yang Anda kirim sepertinya Tidak Valid, Coba lagi.")
        return
    except PhoneCodeExpired:
        await ans.reply("Kode yang Anda kirim tampaknya Kedaluwarsa. Coba lagi.")
        return
    if (await app.get_me()).username is None:
        ask_name = await cb.from_user.ask(
            "Sempurna! sekarang kirimkan saya nama pengguna untuk akun ini tanpa '@'\nAnda juga dapat /skip langkah ini",
            reply_markup=ForceReply(selective=True),
        )
        while True:
            try:
                if ask_name.text.lower == "/skip":
                    break
                username = ask_name.text.replace(" ", "_")[:32].lstrip("@")
                if len(username) < 5:
                    await cb.from_user.ask("Nama pengguna ini terlalu pendek.. kirim lagi")
                else:
                    await app.set_username(username=username)
                    break
            except UsernameOccupied:
                ask_name = await cb.from_user.ask(
                    "Nama pengguna ini sudah terisi.. kirim lagi"
                )
            except UsernameInvalid:
                ask_name = await cb.from_user.ask(
                    "Nama pengguna ini tidak valid.. kirim lagi"
                )
            except UsernameNotModified:
                break
    try:
        app_session = await app.export_session_string()
    except Exception:
        TGubot.log(level=40)
        await ans.reply("Ada yang salah!")
        return
    await app.send_message(
        "me",
        f"<b>Sesi untuk akun ini.</b>\n<code>{app_session}</code>\n\n<b>Catatan:</b> Jangan bagikan sesi ini dengan siapa pun. Dengan ini, mereka dapat dengan mudah masuk ke akun Anda.\n(c) @KazeDevID",
    )
    status_msg = await process_msg.reply("<code>Processing..</code>")
    try:
        await TGubot.add_session(app_session, status_msg)
    except Exception:
        TGubot.log(level=40)
        await status_msg.edit("Ada yang salah!")
