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
    Output some stats
    """
    logging.info("/stats call")

    with User(update, context) as user_info:
        user_timezone = user_info["tz"]
        date_strings = get_date_strings(update.message.date, user_timezone)
        bot_data = json.dumps(context.bot_data, indent=4, sort_keys=True)

        message_text = f"Version: {version()}"
        message_text += f"\nDate strings: {date_strings}"
        message_text += f"\nBot Data: {bot_data}"

        msgs = [message_text[i : i + 4096] for i in range(0, len(message_text), 4096)]
        for text in msgs:
            update.message.reply_text(text)
