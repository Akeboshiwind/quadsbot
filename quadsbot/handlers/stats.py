import logging
import json
import pkgutil
import re

from telegram import Update
from telegram.ext import CallbackContext

from quadsbot.date_utils import get_date_strings
from quadsbot.user import User


version_regex = re.compile(r'''^version = "([^"]*)"''', re.MULTILINE)


def version() -> str:
    """
    Get the project version by parsing the pyproject.toml file
    We have to do this because the project isn't "installed" by poetry
    """
    data = pkgutil.get_data("quadsbot", "../pyproject.toml")
    match = version_regex.search(data.decode("utf-8"))
    if match:
        return match.group(1)


def stats_handler(update: Update, context: CallbackContext) -> None:
    """
    Given a text message, plans what to do with it. Then executes that plan.
    """
    logging.info("/stats call")

    with User(update, context) as user_info:
        user_timezone = user_info["tz"]
        update.message.reply_text(
            f"Version: {version()}"
            f"\nDate strings: {get_date_strings(update.message.date, user_timezone)}"
            f"\nStats: {json.dumps(context.bot_data, indent=4, sort_keys=True)}"
            f"\nUser Data: {json.dumps(context.dispatcher.user_data, indent=4, sort_keys=True)}"
        )
