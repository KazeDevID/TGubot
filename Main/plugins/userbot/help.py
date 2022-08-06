import asyncio
from Main import TGubot
from pyrogram import Client
from difflib import get_close_matches


@TGubot.register_on_cmd(
    ["lang", "language", "set language"], bot_mode_unsupported=True
)
async def lang_modify(c: Client, m):
    rm = m.reply_to_message
    results = await c.get_inline_bot_results(TGubot.bot_info.username, "change_lang")
    return await asyncio.gather(
        *[
            c.send_inline_bot_result(
                m.chat.id,
                query_id=results.query_id,
                result_id=results.results[0].id,
                reply_to_message_id=rm.id if rm else m.id,
            ),
            m.delete_if_self(),
        ]
    )


@TGubot.register_on_cmd(["help"], bot_mode_unsupported=True)
async def help_normal(c: Client, m):
    cmd_lists = TGubot.CLIST
    user_input = m.user_input
    chat = m.chat.id
    rm = m.reply_to_message
    if (not c.myself.is_bot) and "-basic" not in m.user_args:
        results = await c.get_inline_bot_results(TGubot.bot_info.username, "help")
        await c.send_inline_bot_result(
            chat_id=chat,
            query_id=results.query_id,
            result_id=results.results[0].id,
            reply_to_message_id=rm.id if rm else m.id,
        )
        return await m.delete_if_self()
    else:
        if user_input and cmd_lists.get(user_input):
            await m.handle_message(
                f"<b>Help for</b> <code>{user_input}</code>\n\n{cmd_lists[user_input].strip()}"
            )
        elif not user_input:
            cmd_list = "<i><b>Plugins Available</i></b>\n\n"
            for plugins in cmd_lists.keys():
                cmd_list += f"<code>{plugins}</code>  "
            cmd_list = cmd_list[:-2]
            cmd_list += f"\n\n<i>Use</i> <code>{TGubot.user_command_handler}help plugin name</code> <i>to know more!</i>"
            await m.handle_message(cmd_list)
        elif user_input and not cmd_lists.get(user_input):
            if (
                len(get_close_matches(user_input, cmd_lists.keys(), n=4, cutoff=0.3))
                > 0
            ):
                preds = "".join(
                    f"{i}, "
                    for i in get_close_matches(
                        user_input, cmd_lists.keys(), n=4, cutoff=0.3
                    )
                )
                return await m.handle_message(
                    f"<i>Command not found in the list, did you mean?</i> : <code>{preds[:-2]}</code>"
                )
            await m.handle_message("<i>This command is not in the command list!</i>")
