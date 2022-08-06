# Copyright (C) 2022-present by X-SyntaxError, < https://github.com/X-SyntaxError

import logging
from ..core.config import Config as config


heroku3_installed = True

try:
    import heroku3
except ImportError:
    heroku3_installed = False


async def prepare_heroku_url():
    if not heroku3_installed:
        return None
    if not config.HEROKU_APP_NAME or not config.HEROKU_API_KEY:
        return None
    heroku = heroku3.from_key(config.HEROKU_API_KEY)
    try:
        heroku_applications = heroku.apps()
    except Exception:
        return None
    heroku_app = next(
        (app for app in heroku_applications if app.name == config.HEROKU_APP_NAME),
        None,
    )
    if not heroku_app:
        logging.info(
            "Looks like the api key is correct but, heroku app name isn't in the list of apps."
        )
        return None
    return heroku_app.git_url.replace(
        "https://", f"https://api:{config.HEROKU_API_KEY}@"
    )
