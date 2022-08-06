from Main import TGubot
from pyrogram import Client
import Main.core.types.message


if not hasattr(Client, "__send_custom__"):
    setattr(Client, "__send_custom__", Client.invoke)

import Main.core.types.client


if __name__ == "__main__":
    TGubot.run()
