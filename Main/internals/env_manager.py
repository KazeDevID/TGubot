# Copyright (C) 2021-present by X-SyntaxError, < https://github.com/X-SyntaxError

from Main import TGubot
from Main.core.types.message import Message


@TGubot.register_on_cmd(
    "addenv",
    cmd_help={
        "help": "Menambahkan Env ke database!", 
        "contoh": "addenv env_varname env_value",
    },
    requires_input=True,
)
async def add_env_cmd_handler(c: TGubot, m: Message):
    ms = await m.handle_message("PROCESSING")
    input_ = m.user_input
    if " " not in input_:
        return await ms.edit_msg("PROPER_INPUT_REQ")
    env_key, value = input_.split(" ", maxsplit=1)
    await TGubot.config.sync_env_to_db(env_key, value)
    await ms.edit_msg("ENV_ADDED", string_args=(env_key, value))


@TGubot.register_on_cmd(
    "delenv",
    cmd_help={
        "help": "Hapus env dari database!", 
        "contoh": "delenv env_varname",
    },
    requires_input=True,
)
async def del_env_cmd_handler(c: TGubot, m: Message):
    ms = await m.handle_message("PROCESSING")
    input_ = m.user_input
    if not await TGubot.config.get_env(input_):
        return await ms.edit_msg("NO_ENV_FOUND", string_args=(input))
    await TGubot.config.del_env_from_db(input_)
    await ms.edit_msg("ENV_DELETED", string_args=(input_))


@TGubot.register_on_cmd(
    "getenv",
    cmd_help={"help": "Dapatkan env dari database!", "contoh": "getenv env_varname"},
    requires_input=True,
)
async def get_env_cmd_handler(c: TGubot, m: Message):
    ms = await m.handle_message("PROCESSING")
    input_ = m.user_input
    value = await TGubot.config.get_env(input_)
    if not value:
        return await ms.edit_msg("NO_ENV_FOUND", string_args=(input))
    await ms.edit_msg("ENV_VALUE", string_args=(input_, value))
