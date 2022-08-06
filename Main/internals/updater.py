# Copyright (C) 2021-present by X-SyntaxError, < https://github.com/X-SyntaxError

from Main import TGubot
from ..utils._updater import *
from Main.core.types.message import Message


@TGubot.register_on_cmd(
    "update",
    cmd_help={
        "help": "Perbarui bot pengguna Anda.",
        "example": "update",
        "user_args": {"-changelog": "Generate and shows changelog."},
    },
)
async def update(client, message: Message):
    msg = await message.handle_message("PROCESSING")
    updater_ = Updater(
        repo=TGubot.config.REPO, branch="main", app_url=TGubot.app_url_
    )
    await msg.edit_msg("UPDATING")
    repo = await updater_.init_repo()
    if "-changelog" in message.user_args:
        repo = await updater_.init_repo()
        if cl := await updater_.gen_changelog(repo, message, TGubot.config.REPO):
            cl = f"<b>Change-log for TGubot <i>v{TGubot.__version__}</i></b> \n{cl}"
        else:
            cl = "NO_CHANGES"
        await msg.edit_msg(cl)
    uprem = await updater_.create_remote_and_fetch(repo)
    if TGubot.app_url_:
        await updater_.update_remotely_heroku(uprem, repo, msg)
    else:
        await updater_.update_locally(uprem, repo, msg)
    return await msg.edit_msg("UPDATER_SUCCESS", string_args=(TGubot.__version__))
