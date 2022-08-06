import os
import aiohttp
from ._validators import is_url


def concatenate(i: any, max_value: any, to_add: str, from_end=True):
    if from_end:
        return str(i) + (len(str(max_value)) - len(str(i))) * to_add
    return (len(str(max_value)) - len(str(i))) * to_add + str(i)


def monkeypatch(obj):
    def wrapper(sub):
        for (func_name, func_) in sub.__dict__.items():
            if func_name[:2] != "__":
                setattr(obj, func_name, func_)
        return sub

    return wrapper


async def write_file_from_url(url, file_name):
    with open(file_name, mode="wb") as f:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as r:
                f.write(await r.read())


async def custom_init(url, suffix_file="", to_path=""):
    if not url or not await is_url(url):
        return None
    basename = os.path.basename(url)
    ext = basename.split(".", 1)[1] if basename and "." in basename else "jpg"
    file_name = to_path + suffix_file + "." + ext
    if os.path.exists(file_name):
        return file_name
    try:
        await write_file_from_url(url, file_name)
    except Exception:
        return
    return file_name
