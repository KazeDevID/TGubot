import re
import Main
from pyrogram import filters
from pyrogram.types import Message
from .file_helpers import run_in_exc


@run_in_exc
def parse_(client, message: Message, cmd, disable_sudo=False):
    sudo_cmd_handler = Main.TGubot.sudo_cmd_handler
    sd_list = [] if disable_sudo else Main.TGubot.config.SUDO_USERS
    user_cmd_handler = Main.TGubot.user_command_handler
    try:
        if not message.text:
            return False
        reg = re.search(
            r"^([\!\"\#\$\%\&\'\(\)\*\+\,\-\.\/\:\;\<\>\=\?\@\[\]\{\}\\\\\^\_\`\~])(\w+)(?:(?:.|\n)+)?$",
            message.text,
        )
        if (
            (((message.from_user and message.from_user.is_self) or message.outgoing))
            and message.text
            and reg[1] == user_cmd_handler
            and reg[2] in cmd
        ):
            return True
        elif (
            message.from_user
            and message.from_user.id in sd_list
            and message.text
            and reg[1] == sudo_cmd_handler
            and reg[2] in cmd
        ):
            return True
        else:
            return False
    except Exception:
        return False


def user_filters(cmd, disable_sudo=False):
    async def s_f(f, client, message):
        f_out = await parse_(
            client=client, message=message, cmd=cmd, disable_sudo=disable_sudo
        )
        return f_out

    return filters.create(s_f)
