# Copyright (C) 2022-present by X-SyntaxError, < https://github.com/X-SyntaxError

import os
import sys
import glob
import time
import yaml
import shlex
import random
import shutil
import asyncio
import inspect
import logging
import aiofiles
import importlib
import traceback
import contextlib
import multiprocessing
from pathlib import Path
from functools import wraps
from Main.core.apm import APM
from datetime import datetime
from cachetools import TTLCache
from traceback import format_exc
from Main.core.cache import Cache
from Main.utils.paste import Paste
from ..utils._updater import Updater
from pyrogram.session import Session
from .config import Config, BaseConfig
from ..utils.essentials import Essentials
from .database import MongoDB, LocalDatabase
from pyrogram.handlers import MessageHandler
from ..utils.custom_filters import user_filters
from ..utils.startup_helpers import concatenate
from Main.utils.heroku_ import prepare_heroku_url
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, List, Union, Optional
from pyrogram.types import User, Message, CallbackQuery
from ..utils.multi_lang_helpers import get_all_files_in_path
from pyrogram import (
    Client, StopPropagation, ContinuePropagation, idle, filters,
    __version__ as pyrogram_version)
from pyrogram.errors.exceptions.bad_request_400 import (
    MessageEmpty, PeerIdInvalid, MessageTooLong, MessageIdInvalid,
    MessageNotModified, UserNotParticipant)


class TGubotClient:
    def __init__(self, *args, **kwargs) -> None:
        self.ourselves: List[Dict[Any, Any]] = []
        self.bot_info = None
        self.clients: List[Client] = []
        self.cmd_list = {}
        self.all_lang_strings = {}
        self.auto_approve = False
        self.__version__ = "0.0.1"
        self.selected_lang = "english"
        self.local_lang_file = "./Main/localization"
        self.cmd_list = {}
        self.start_time = time.time()
        self.app_url_ = None
        self.disabled_sudo_plugin_list = []
        self.SELF_PERMISSION_CACHE = TTLCache(
            99999, ttl=60 * 60, timer=time.perf_counter
        )
        self.loaded_bot_cmds = False
        Session.notice_displayed = True
        self.cmd_list_s = []
        self.traning_wheels_protocol = False
        self._init_logger()
        self.config = BaseConfig
        self.local_db = LocalDatabase()
        self.loop = asyncio.get_event_loop()
        self.loop.run_until_complete(self._db_setup())
        self.executor = ThreadPoolExecutor(max_workers=multiprocessing.cpu_count() * 5)
        self.config = Config(self.db.env_col, loop=self.loop, executor=self.executor)
        self.log_chat = None
        self.CLIST = {}
        self.loop.run_until_complete(self._setup(restart=False, *args, **kwargs))

    async def update_cache(self):
        cache = Cache(self.config, self.db, self.clients)
        await cache.update_auto_post_cache()
        await cache.update_approved_list_on_startup()
        await cache.init_all_custom_files()

    @property
    def banner(self):
        return f"""
───▄▀▀▀▄▄▄▄▄▄▄▀▀▀▄───
───█▒▒░░░░░░░░░▒▒█───
────█░░█░░░░░█░░█────
─▄▄──█░░░▀█▀░░░█──▄▄─
█░░█─▀▄░░░░░░░▄▀─█░░█
█▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀█
█░░╦─╦╔╗╦─╔╗╔╗╔╦╗╔╗░░█
█░░║║║╠─║─║─║║║║║╠─░░█
█░░╚╩╝╚╝╚╝╚╝╚╝╩─╩╚╝░░█
█▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄█



╭━━━━┳━━━╮╱╱╭╮╱╱╱╱╭╮
┃╭╮╭╮┃╭━╮┃╱╱┃┃╱╱╱╭╯╰╮
╰╯┃┃╰┫┃╱╰╋╮╭┫╰━┳━┻╮╭╯
╱╱┃┃╱┃┃╭━┫┃┃┃╭╮┃╭╮┃┃
╱╱┃┃╱┃╰┻━┃╰╯┃╰╯┃╰╯┃╰╮
╱╱╰╯╱╰━━━┻━━┻━━┻━━┻━╯

 (C) Project with by X-SyntaxError | KazeDevID 2022-{datetime.today().year}
        """

    @property
    def ax(self) -> Optional[Client]:
        return random.choice(self.clients) if self.clients else None

    @property
    def auth_users(self):
        return list(
            set(
                self.config.SUDO_USERS
                + [int(acc.id) for acc in self.ourselves]
                + [self.config.OWNER_ID]
            )
        )

    @staticmethod
    def log(
        message: Optional[str] = None,
        level=logging.INFO,
        logger: logging.Logger = logging.getLogger(__module__),
    ) -> Optional[str]:
        logger.log(level, message or traceback.format_exc())
        return message or traceback.format_exc()

    def _init_logger(self) -> None:
        logging.getLogger("pyrogram").setLevel(logging.WARNING)
        logging.basicConfig(
            level=logging.INFO,
            datefmt="[%d/%m/%Y %H:%M:%S]",
            format="%(asctime)s - [TGubot] >> %(levelname)s << %(message)s",
            handlers=[logging.FileHandler("TGubot.log"), logging.StreamHandler()],
        )
        self.log("Initialized Logger successfully!")

    async def resolve_dns(self):
        import dns.resolver

        try:
            dns.resolver.resolve("www.google.com")
        except Exception:
            self.log("Resolving DNS. Setting to : 8.8.8.8")
            dns.resolver.default_resolver = dns.resolver.Resolver(configure=False)
            dns.resolver.default_resolver.nameservers = ["8.8.8.8"]

    async def _db_setup(self):
        with contextlib.suppress(Exception):
            await self.update_on_startup()
        await self.resolve_dns()
        self.db = MongoDB(self.config.DB_URI)
        self.log("Initialized Mongo successfully!")
        await self.db.ping()
        self.log("Pinged Mongo successfully!")
        self.app_url_ = await prepare_heroku_url()

    def run_in_exc(self, func_):
        @wraps(func_)
        async def wrapper(*args, **kwargs):
            loop = asyncio.get_running_loop()
            return await loop.run_in_executor(
                self.executor, lambda: func_(*args, **kwargs)
            )

        return wrapper

    async def setup_localization(self):
        lang = await self.config.get_env("UB_LANG")
        selected_lang = lang.lower() if lang else "english"
        all_files = get_all_files_in_path(self.local_lang_file)
        for filepath in all_files:
            with open(filepath, encoding="utf-8") as f:
                try:
                    data = yaml.safe_load(f)
                except Exception:
                    self.log()
                    continue
                language_to_load = data.get("language")
                if language_to_load == "template":
                    continue
                self.log(f"Loading : {language_to_load}", level=10)
                self.all_lang_strings[language_to_load] = data
        self.selected_lang = (
            selected_lang if selected_lang in self.all_lang_strings else "english"
        )
        if selected_lang not in self.all_lang_strings:
            self.log(
                f"{selected_lang} Not Found! Using The Default Language - English."
            )
        self.log("Localization setup complete!")

    def get_string(self, keyword: str, args: tuple = None):
        selected_lang = self.selected_lang
        if self.all_lang_strings.get(selected_lang) and self.all_lang_strings.get(
            selected_lang
        ).get(keyword):
            str_ing = self.all_lang_strings.get(selected_lang).get(keyword)
            return (
                (
                    str_ing.format(*args)
                    if isinstance(args, tuple)
                    else str_ing.format(args)
                )
                if args
                else str_ing
            )

    def on_message(self, custom_filters, group=1, bot_mode_unsupported=False):
        custom_filters &= ~filters.command(
            self.cmd_list_s, [self.user_command_handler, self.sudo_cmd_handler]
        )

        def decorator(func):
            async def wrapper(client, message: Message):
                if str(message.chat.type).lower().startswith("chattype."):
                    chat_type = str(
                        (str(message.chat.type).lower()).split("chattype.")[1]
                    )
                    message.chat.type = chat_type
                try:
                    await func(client, message)
                except StopPropagation as e:
                    raise StopPropagation from e
                except ContinuePropagation as e:
                    raise ContinuePropagation from e

            self.custom_add_handler(
                cmd=None,
                func_=wrapper,
                filter_s=custom_filters,
                group=group,
                bot_mode_unsupported=bot_mode_unsupported,
            )
            return wrapper

        return decorator

    async def update_on_startup(self):
        if self.config.UPDATE_ON_STARTUP:
            updater_ = Updater(
                repo=self.config.REPO, branch="main", app_url=self.app_url_
            )
            repo = await updater_.init_repo()
            up_rem = await updater_.create_remote_and_fetch(repo)
            await updater_.update_locally(up_rem, repo, None, self, True)

    async def install_apm_from_file(self):
        if os.path.exists("apm_req.txt"):
            async with aiofiles.open("apm_req.txt", "r") as f:
                apm_ = await f.readlines()
                APM_ = APM(self)
                for i in apm_:
                    try:
                        await APM_.install_package(i)
                    except Exception:
                        logging.error(
                            f"Failed to install {i} :: {traceback.format_exc()}"
                        )
                        continue
            return logging.info("Installed all Packages from [apm.txt]")

    async def install_all_apm_packages(self):
        custom_path = "./Main/plugins/custom_app/"
        if os.path.exists(custom_path):
            for it in os.scandir(custom_path):
                if it.is_dir():
                    await self.load_from_directory(f"{it.path}/*.py")
        await self.install_apm_from_file()
        mc = self.db.make_collection("packages")
        APM_ = APM(self)
        packages_ = await mc.find_one({"_id": "APM"})
        if (packages_) and packages_.get("installed_packages"):
            list_of_packages = packages_["installed_packages"]
            for package in list_of_packages:
                try:
                    await APM_.install_package(package)
                except Exception:
                    logging.error(
                        f"Failed to install {package} :: {traceback.format_exc()}"
                    )
                    continue
            if os.path.exists("./Main/plugins/temp_app/"):
                shutil.rmtree("./Main/plugins/temp_app/")
            return logging.info("Installed all Packages.")

    def register_on_cmd(
        self,
        cmd: Union[str, List[str]],
        cmd_help: dict = {},
        pm_only: bool = False,
        group_only: bool = False,
        channel_only: bool = False,
        just_exc: bool = False,
        requires_input: bool = False,
        requires_reply: bool = False,
        bot_mode_unsupported: bool = False,
        # Incase a command can't be performed by an bot.
        group=1,
        disallow_if_sender_is_channel=False,
    ):
        cmd_help_ = cmd_help.get("help") or "Not Given"
        cmd_help_ex = cmd_help.get("example") or "Not Given"
        user_args = dict(cmd_help.get("user_args")) if cmd_help.get("user_args") else {}
        cmd = cmd if isinstance(cmd, list) else [cmd]
        self.cmd_list_s.extend(cmd)
        previous_stack_frame = inspect.stack()[1]
        file_name = os.path.basename(previous_stack_frame.filename.replace(".py", ""))
        self.add_help_to_cmdlist(
            cmd=cmd,
            file_name=file_name,
            cmd_help=cmd_help_,
            example=cmd_help_ex,
            user_args=user_args,
            requires_input=requires_input,
            requires_reply=requires_reply,
            group_only=group_only,
            channel_only=channel_only,
            pm_only=pm_only,
        )

        def decorator(func):
            async def wrapper(client, message: Message):
                if str(message.chat.type).lower().startswith("chattype."):
                    chat_type = str(
                        (str(message.chat.type).lower()).split("chattype.")[1]
                    )
                    message.chat.type = chat_type
                chat_type = message.chat.type
                input_ = message.user_input
                if requires_input and input_ in ["", " ", None]:
                    return await message.handle_message("INPUT_REQUIRED")
                if requires_reply and not message.reply_to_message:
                    return await message.handle_message("REPLY_REQUIRED")
                if group_only and chat_type not in ["supergroup", "group"]:
                    return await message.handle_message("GROUP_ONLY")
                if channel_only and chat_type != "channel":
                    return await message.handle_message("CHANNEL_ONLY")
                if pm_only and chat_type != "private":
                    return await message.handle_message("PM_ONLY")
                if (
                    message.reply_to_message
                    and disallow_if_sender_is_channel
                    and message.reply_to_message.sender_chat
                    and message.reply_to_message.sender_chat.id
                ):
                    return await message.handle_message("DISALLOW_SENDER_CHAT")
                if just_exc:
                    await func(client, message)
                else:
                    try:
                        await func(client, message)
                    except StopPropagation as e:
                        raise StopPropagation from e
                    except (
                        MessageNotModified,
                        MessageIdInvalid,
                        UserNotParticipant,
                        MessageEmpty,
                    ):
                        pass
                    except ContinuePropagation as e:
                        raise ContinuePropagation from e
                    except Exception as _be:
                        try:
                            await self.send_error(
                                client, cmd, format_exc(), file_name=file_name
                            )
                        except Exception as e:
                            raise _be from e

            disabled_sudo = False
            if not self.traning_wheels_protocol:
                if disabled_sudo := (
                    all(
                        (
                            item in list(cmd)
                            for item in list(self.disabled_sudo_plugin_list)
                        )
                    )
                    if self.disabled_sudo_plugin_list
                    else False
                ):
                    self.log(f"Not Loading - Disabled : {cmd[0]} For sudo!")
            self.custom_add_handler(
                cmd,
                wrapper,
                disable_sudo=disabled_sudo,
                group=group,
                bot_mode_unsupported=bot_mode_unsupported,
            )
            return wrapper

        return decorator

    def add_help_to_cmdlist(
        self,
        cmd: List[str],
        file_name: str,
        cmd_help: dict,
        example,
        user_args,
        requires_input,
        requires_reply,
        group_only,
        channel_only,
        pm_only,
    ):
        example = self.config.CMD_HANDLER + example
        if isinstance(cmd, list):
            cmd = cmd[0]
        if file_name not in self.cmd_list:
            self.cmd_list[file_name] = [
                {
                    "cmd": cmd,
                    "cmd_help": cmd_help,
                    "example": example,
                    "requires_input": requires_input,
                    "user_args": user_args,
                    "requires_reply": requires_reply,
                    "group_only": group_only,
                    "channel_only": channel_only,
                    "pm_only": pm_only,
                }
            ]
        elif cmd not in [x.get("cmd", "_") for x in self.cmd_list[file_name]]:
            self.cmd_list[file_name].append(
                {
                    "cmd": cmd,
                    "cmd_help": cmd_help,
                    "example": example,
                    "requires_input": requires_input,
                    "user_args": user_args,
                    "requires_reply": requires_reply,
                    "group_only": group_only,
                    "channel_only": channel_only,
                    "pm_only": pm_only,
                }
            )

    def custom_add_handler(
        self,
        cmd=None,
        func_=None,
        filter_s=None,
        disable_sudo=False,
        group=0,
        bot_mode_unsupported=False,
    ):
        if not self.traning_wheels_protocol:
            self.config.CMD_HANDLER
            basic_f = (
                filter_s
                or user_filters(list(cmd), disable_sudo=disable_sudo)
                & ~filters.via_bot
                & ~filters.forwarded
            )
            for client in self.clients:
                client.add_handler(MessageHandler(func_, filters=basic_f), group=group)
        if self.bot_mode and not bot_mode_unsupported and not self.loaded_bot_cmds:
            bot_f = filter_s or filters.user(self.auth_users) & filters.command(
                list(cmd), ["!", "/", "|"]
            )
            self.bot.add_handler(MessageHandler(func_, filters=bot_f), group=group)

    async def _setup(self, restart=False, *args, **kwargs):
        if not os.path.isdir("cache"):
            os.mkdir("cache")
        await self.setup_localization()
        self.sudo_cmd_handler = await self.config.get_env("SUDO_CMD_HANDLER") or "!"
        self.user_command_handler = await self.config.get_env("CMD_HANDLER") or "."
        self.disabled_sudo_plugin_list = await self.config.get_env(
            "DISABLED_SUDO_CMD_LIST", []
        )
        self.log_chat = self.config.digit_wrap(await self.config.get_env("LOG_CHAT_ID"))
        self.bot_mode = (str(await self.config.get_env("BOT_MODE"))).lower() in {
            "yes",
            "true",
            "enable",
        }
        self.auto_approve = str((await self.config.get_env("AUTOAPPROVE"))).lower() in {
            "yes",
            "true",
            "ok",
        }
        if not restart:
            await self.initialize_telegram_sessions(*args, **kwargs)
        await self.update_cache()

    async def _run(self):
        await self.load_all_modules()
        print(self.banner)
        self.log(
            f"TGubot v{self.__version__} telah berhasil digunakan dengan versi pyrogram v{pyrogram_version}!"
        )
        if self.traning_wheels_protocol:
            self.log(
                "TGubot ada di [TWP], semua fitur userbot akan dinonaktifkan!",
                level=30,
            )
            self.log("Mulai bot untuk mempelajari cara menonaktifkannya.",
        await idle()

    async def _test(self):
        dev_chat_id = -1001692951318
        try:
            await self.load_all_modules()
            mess = None
            if self.traning_wheels_protocol:
                self.log("Tidak ada sesi pengguna yang ditemukan, Berjalan dalam mode [TWP].", level=50)
            else:
                self.log("Menguji sesi Pengguna.", level=30)
                for each in self.clients:
                    mess = await each.send_message(
                        dev_chat_id,
                        f"""commit: <a href='https://github.com/X-SyntaxError/TGubot/commit/{os.getenv("COMMIT_SHA")}'>{os.getenv('COMMIT_NAME')}</a> berhasil diuji!""",
                    )
                    await each.stop()
            self.log("Tes bot.", level=30)
            await self.bot.send_message(
                dev_chat_id,
                "Test completed.",
                reply_to_message_id=mess.id if mess else None,
            )
            self.log("Test completed.", level=30)
        except Exception:
            self.log(f"Test failed: {(await Paste(format_exc()).paste())[1]}", level=40)
            quit(1)

    async def initialize_telegram_sessions(self, *args, **kwargs) -> None:
        self.bot = Client(
            name="TGubot[bot]",
            api_id=self.config.API_ID,
            api_hash=self.config.API_HASH,
            bot_token=self.config.BOT_TOKEN,
            workdir="cache",
            *args,
            **kwargs,
        )
        await self.bot.start()
        self.bot_info = await self.bot.get_me()
        self.bot.info = self.bot_info
        self.log(f"Assistant : Logged in as @{self.bot_info.username}")
        if string_sessions := self.config.SESSIONS:
            self.log("Sesi pengguna ditemukan secara lokal, sinkronisasi sedang berlangsung...")
            await self.config.sync_env_to_db("SESSIONS", string_sessions)
        else:
            self.log("Mencari di DB untuk sesi pengguna...")
            string_sessions = await self.config.get_env_from_db("SESSIONS")
        if not string_sessions:
            self.traning_wheels_protocol = True
            self.log(
                ""Tidak ada Sesi Pengguna yang ditemukan, semua fitur userbot akan dinonaktifkan!",
                level=30,
            )
            try:
                self.ourselves.append(await self.bot.get_users(self.config.OWNER_ID))
            except PeerIdInvalid:
                self.log(
                    "Silakan mulai bot dengan akun yang ID-nya telah Anda tambahkan di bidang OWNER_ID.",
                    level=40,
                )
                quit()
            except Exception as e:
                self.log(
                    f"[{e}] - Silakan tambahkan sesi lain menggunakan bot asisten Anda [@{self.bot_info.username}]",
                    level=logging.CRITICAL,
                )
        else:
            self.log("Sesi Pengguna ditemukan, menggunakannya!")
            for count, each in enumerate(string_sessions):
                try:
                    client = await Client(
                        f"{count}_instance_TGubot",
                        api_id=self.config.API_ID,
                        api_hash=self.config.API_HASH,
                        session_string=each,
                        workdir="cache",
                    ).start()
                    client.myself = await client.get_me()
                    self.clients.append(client)
                    if not client.myself.id == self.config.OWNER_ID:
                        self.ourselves.append(client.myself)
                    self.log(f"[{count + 1}/{len(string_sessions)}] Sesi Dimuat.")
                except Exception as err:
                    self.log(
                        err,
                        level=50,
                    )
                    self.log(
                        f"Session {count + 1} menjadi tidak dapat digunakan, silakan tambahkan kembali sesi menggunakan asisten bot."
                    )
                    self.config.pop_session(count)
                    # if not popped:
                    #   popped = self.config.SESSIONS[count]
                    await self.config.pop_element_from_list("SESSIONS", each)
            if not self.clients:
                await self.config.del_env_from_db("SESSIONS")
                self.traning_wheels_protocol = True

    async def add_session(self, session: str, status: Message = None) -> Client:
        await self.config.add_element_to_list("SESSIONS", session)
        self.config.append_session(session)
        self.config.SESSIONS.append(session)
        self.log("Sesi pengguna berhasil ditambahkan!")
        if self.traning_wheels_protocol:
            self.log("[TWP] telah dinonaktifkan!")
        app = Client(
            "main_instance",
            api_id=self.config.API_ID,
            api_hash=self.config.API_HASH,
            session_string=session,
            workdir="cache",
        )
        self.clients.append(app)
        await app.start()
        session_user_info = await app.get_me()
        app.myself = session_user_info
        if not app.myself.id == self.config.OWNER_ID:
            self.ourselves.append(session_user_info)
        self.traning_wheels_protocol = False
        await self.load_all_modules()
        self.log("Plugin Userbot telah dimuat.")
        if status:
            await status.edit(
                "<b>Akun Berhasil ditambahkan!</b>",
            )
        return app

    async def remove_session(self, index: int) -> User:
        session = self.config.pop_session(index)
        await self.config.pop_element_from_list("SESSIONS", session)
        removed_session_info = self.ourselves.pop(index)
        await self.clients.pop(index).stop()
        if not self.ourselves:
            self.traning_wheels_protocol = True
            self.log("[TWP] telah diaktifkan!") 
            self.log("Sesi pengguna berhasil dihapus!")
        self.loop.create_task(self.load_all_modules())
        return removed_session_info

    async def _restart(
        self,
        soft=False,
        last_msg: Union[Message, CallbackQuery, None] = None,
        power_hard=False,
    ):
        self.loaded_bot_cmds = False
        _start = time.perf_counter()
        await self._setup(restart=True)
        if not soft:
            if power_hard:
                args = [sys.executable, "-m", "Main"]
                os.execle(sys.executable, *args, os.environ)
            if not self.traning_wheels_protocol and not self.clients:
                for each in self.clients:
                    await each.restart()
            await self.bot.restart()
            self.start_time = time.time()
        await self.load_all_modules()
        time_took = Essentials.get_readable_time(time.perf_counter() - _start)
        msg = f"<b>TGubot telah {'reloaded' if soft else 'restarted'}!</b>\ntelah mengambil {time_took}."
        await self.bot.send_message(self.config.OWNER_ID, msg)
        if isinstance(last_msg, Message):
            await last_msg.edit(msg)
        elif isinstance(last_msg, CallbackQuery):
            await last_msg.edit_message_text(msg)
        self.log(
            f"TGubot telah {'reloaded' if soft else 'restarted'} success!"
        )
        await idle()

    async def send_error(
        self,
        client: Client,
        cmd: Union[str, List[str]],
        error: str,
        file_name: str,
        **args,
    ):
        chat_id = self.log_chat
        cmd_handler = self.config.CMD_HANDLER
        headers = self.get_string("ERROR_")
        if isinstance(cmd, list):
            cmd = cmd[0]
        if not chat_id:
            return
        txt_ = self.get_string(
            "ERROR_REPORT", args=(cmd_handler, cmd, error, cmd_handler, file_name)
        )
        try:
            m = await client.send_message(chat_id, txt_, **args)
        except MessageTooLong:
            text = Essentials.md_to_text(txt_)
            service, paste_link = await Paste(text).paste()
            txt = headers.format(service.title(), paste_link)
            m = await client.send_message(chat_id, txt, **args)
        return m

    async def reboot(
        self, soft=False, last_msg: Union[Message, CallbackQuery, None] = None
    ):
        self.log(f"Sinyal yang diterima untuk {'Reload' if soft else'Restart'}!", level=30)
        await asyncio.sleep(2)
        self.loop.create_task(self._restart(soft=soft, last_msg=last_msg))

    async def custom_log(self, msg, level=logging.INFO, p_msg: Message = None):
        self.log(msg, level)
        if p_msg:
            return await p_msg.edit_msg(msg.strip())

    async def load_from_directory(self, path: str, log=True, msg=None):
        helper_scripts = glob.glob(path)
        if not helper_scripts:
            return await self.custom_log(
                f"Tidak ada plugin yang dimuat dari {path}", level=logging.INFO, p_msg=msg
            )
        plugin_count = str(len(helper_scripts))
        loaded_pc = 0
        for name in helper_scripts:
            loaded_pc += 1
            start_time = time.time()
            with open(name) as a:
                path_ = Path(a.name)
                plugin_name = path_.stem.replace(".py", "")
                plugins_dir = Path(path.replace("*", plugin_name))
                import_path = path.replace("/", ".")[:-4] + plugin_name
                import_type = import_path.split(".")[-2]
                spec = importlib.util.spec_from_file_location(import_path, plugins_dir)
                load = importlib.util.module_from_spec(spec)
                load.TGubot = self
                load.bot = self.bot
                load.asyncio = asyncio
                if import_type == "userbot":
                    import_type = "U"
                elif import_type == "bot":
                    import_type = "A"
                else:
                    import_type = "M"
                try:
                    spec.loader.exec_module(load)
                    sys.modules[import_path + plugin_name] = load
                    end_time = round(time.time() - start_time, 2)
                    if log:
                        string_load = (
                            f"[{import_type}] - ["
                            + concatenate(str(loaded_pc), "99", "0", False)
                            + "/"
                            + concatenate(plugin_count, "99", "0", False)
                            + "] Loaded "
                            + concatenate(plugin_name, " " * 30, " ")
                            + "["
                            + concatenate(str(end_time), "    ", "0")
                            + "s]"
                        )
                        if msg:
                            string_load = f"[{import_type}] - Loaded {plugin_name} in <i>{end_time}s</i>"
                        await self.custom_log(
                            string_load,
                            p_msg=msg,
                        )
                except Exception as err:
                    await self.custom_log(
                        f"[{import_type}] Failed To Load : {plugin_name} ({err})",
                        level=50,
                        p_msg=msg,
                    )

    async def run_cmd_async(self, cmd):
        _cmd_args = shlex.split(cmd)
        process = await asyncio.create_subprocess_exec(
            *_cmd_args, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        return (
            stdout.decode("utf-8").strip(),
            stderr.decode("utf-8").strip(),
            process.returncode,
            process.pid,
        )

    async def load_all_modules(self):
        await self.load_from_directory("Main/utils/*.py", log=False)
        await self.load_from_directory("Main/internals/*.py", log=False)
        self.log("Semua modul internal telah dimuat.") 
        self.log("Bersiap untuk memuat semua plugin.\n")
        await self.load_from_directory("Main/plugins/bot/*.py", log=True)
        if self.traning_wheels_protocol:
            self.log("Plugin Userbot akan dinonaktifkan karena [TWP]!")
            if self.bot_mode:
                await self.load_from_directory("Main/plugins/userbot/*.py", log=False)
                self.log("BOT_MODE: ON - Memuat semua Modul yang mungkin sebagai BOT.")
                self.loaded_bot_cmds = True
        else:
            await self.load_from_directory("Main/plugins/userbot/*.py", log=True)
            if self.bot_mode:
                self.log("BOT_MODE: ON - Memuat semua Modul yang mungkin sebagai BOT.")
                self.loaded_bot_cmds = True
            await self.install_all_apm_packages()
            if os.path.lexists("Main/plugins/external"):
                await self.load_from_directory("Main/plugins/externals/*.py", log=True)
            self.log("Semua plugin telah dimuat.")
            self.prepare_help()
        print("\n")

    def run(self):
        self.loop.run_until_complete(self._run())

    def test_run(self):
        self.loop.run_until_complete(self._test())

    def prepare_help(self):
        self.CLIST.clear()
        for cmd in self.cmd_list:
            module = self.cmd_list[cmd]
            cmd = cmd.lower()
            self.CLIST[cmd] = ""
            for cmds in module:
                self.CLIST[
                    cmd
                ] += f"""\n<b>Command :</b> <code>{self.user_command_handler}{cmds.get('cmd')}</code>
<b>Help :</b> <code>{cmds.get('cmd_help')}</code>
<b>Example :</b> <code>{cmds.get('example')}</code>"""
                if cmds.get("user_args"):
                    self.CLIST[cmd] += f"\n<b>Args :</b> \n"
                    user_args: dict = cmds.get("user_args")
                    for arg in user_args:
                        arg_ = arg
                        if not arg.startswith("-"):
                            arg_ = f"<code>-{arg}</code>"
                        self.CLIST[cmd] += f">> {arg_}: {user_args[arg]}\n"
                if cmds.get("requires_input"):
                    self.CLIST[cmd] += f"\n<b>Input Req:</b> <code>Yes</code>"
                if cmds.get("requires_reply"):
                    self.CLIST[cmd] += f"\n<b>Requires Reply :</b> <code>Yes</code>"
                self.CLIST[cmd] += "\n"
