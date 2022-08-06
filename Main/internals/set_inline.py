import asyncio
from Main import TGubot
from pyrogram import Client as client


async def set_inline_in_botfather(Client: client):
    await Client.send_message("botfather", "/cancel")
    await asyncio.sleep(1)
    message = await Client.send_message("botfather", "/setinline")
    await asyncio.sleep(1)
    await message.reply(f"@{TGubot.bot_info.username}")
    await asyncio.sleep(1)
    await message.reply("Powered by X-SyntaxError")
    await asyncio.sleep(1)
