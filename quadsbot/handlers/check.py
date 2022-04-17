import logging
from datetime import datetime

from telegram import Update
from telegram.ext import CallbackContext

from quadsbot.user import User
from quadsbot.handlers.message import check


def check_handler(update: Update, context: CallbackContext) -> None:
    """
    Manually run check
    """
    logging.info("/check call")

    date = update.message.date

    with User(update, context) as user_info:
        user_timezone = user_info["tz"]

        # Let the user manually enter a date and timezone
        # /check 2022-01-22T22:01:01 Europe/London quads
        if len(context.args) >= 1:
            maybe_date = context.args[0]

            if len(context.args) >= 2:
                user_timezone = context.args[1]

            try:
                date = datetime.strptime(maybe_date, "%Y-%m-%dT%H:%M:%S")
            except ValueError:
                update.message.reply_text(
                    f"Failed to parse date `{maybe_date}`\n"
                    "Must be of format `%Y-%m-%dT%H:%M:%S`"
                )

        state, check_info = check(date, user_timezone, update.message.text)

        message = f"TZ: {user_timezone}"
        message += f"\nState: {state}"
        message += f"\nCheck Info: {check_info}"
        update.message.reply_text(message)
