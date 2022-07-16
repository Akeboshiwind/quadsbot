import logging
import json

from telegram import Update
from telegram.ext import CallbackContext


def clear_handler(update: Update, context: CallbackContext) -> None:
    """
    Clears the stored stats
    """
    logging.info("/clear call")
    context.bot_data.clear()
    update.message.reply_text(f"Stats: {json.dumps(context.bot_data)}")
