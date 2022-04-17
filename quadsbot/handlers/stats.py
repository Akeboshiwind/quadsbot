import logging
import json
import importlib.metadata

from telegram import Update
from telegram.ext import CallbackContext

from quadsbot.date_utils import get_date_strings
from quadsbot.user import User


def stats_handler(update: Update, context: CallbackContext) -> None:
    """
    Given a text message, plans what to do with it. Then executes that plan.
    """
    logging.info("/stats call")

    with User(update, context) as user_info:
        user_timezone = user_info["tz"]
        version = importlib.metadata.version("quadsbot")
        update.message.reply_text(
            f"Version: {version}"
            f"\nDate strings: {get_date_strings(update.message.date, user_timezone)}"
            f"\nStats: {json.dumps(context.bot_data)}"
        )
