import logging
import json

from telegram import Update
from telegram.ext import CallbackContext


def clear_handler(update: Update, context: CallbackContext) -> None:
    """
    Clears the stored stats
    """
    logging.info("/clear call")
    context.bot_data["user_stats"].clear()
    user_stats = json.dumps(context.bot_data["user_stats"])
    update.message.reply_text(f"Stats: {user_stats}")
