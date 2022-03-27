import logging
import re
import os
from enum import Enum

from telegram import Update
from telegram.ext import (
    Updater,
    MessageHandler,
    CommandHandler,
    Filters,
    CallbackContext,
)
import pytz

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

logger = logging.getLogger(__name__)

# Formats the date as a series of human readable numbers
# 2020-10-22T12:51:24 -> 20201022125124
# NOTE: I'm not sure if this will handle timezones nicely
format_strings = [
    "%Y%m%d%H%M%S",  # 24 hour
    "%Y%m%d%I%M%S",  # 12 hour
]
tz = pytz.timezone(os.environ.get("TZ", "Europe/London"))


def get_date_strings(date) -> list[int]:
    # Convert date to bot timezone
    date = date.astimezone(tz)

    return [date.strftime(format_string) for format_string in format_strings]


# A list of tuples
# The first value is a regex matcher for the above time format
# The second value is either a regex matcher for text contents
#
# The first one that matches is replied to with "Checked"
matchers = [
    (r"(\d)\1{3}", "quads"),  # 2022-03-01T22:22:00
    (r"(\d)\1{5}", "sexts"),  # 2022-03-01T22:22:22
    (r"(\d)\1{7}", "octs"),  # 2022-03-22T22:22:22
    (r"(\d)\1{9}", "decs"),  # 2022-11-11T11:11:11
    (r"11235?8?(13)?", "fibs"),  # 2022-03-11T23:58:13
]

State = Enum("State", "DELETE PASS CHECKED")


def check(dates: list[int], message_text: str) -> State:
    """
    Calculate what to do with the given message.

    If one of the provided `dates` (in digit form) matches one of the matchers
    AND the `message_text` matches that same matcher.
    Then we want to reply "Checked".

    If one of the dates matches, but the text doesn't we want to neither reply,
    nor delete the message.

    If neither the message, nor the date matches. Then we want to delete the
    message.

    This is reflected in the output state as CHECKED, PASS and DELETE.
    """
    delete_message = True

    message_text = message_text.lower()

    for (date_re, message_re) in matchers:
        for date_digits in dates:
            if re.search(date_re, date_digits):
                delete_message = False
                if re.search(message_re, message_text):
                    return State.CHECKED

    if delete_message:
        return State.DELETE
    else:
        return State.PASS


def message_handler(update: Update, context: CallbackContext) -> None:
    """
    Given a text message, plans what to do with it. Then executes that plan.
    """
    dates = get_date_strings(update.message.date)
    state = check(dates, update.message.text)

    if state == State.CHECKED:
        update.message.reply_text("Checked", quote=True)
    elif state == State.DELETE:
        update.message.delete()
    elif state == State.PASS:
        pass


def stats_handler(update: Update, context: CallbackContext) -> None:
    """
    Given a text message, plans what to do with it. Then executes that plan.
    """
    update.message.reply_text(f"Date strings: {get_date_strings(update.message.date)}")


def main() -> None:
    updater = Updater(token=os.environ["TELEGRAM_BOT_TOKEN"])

    dispatcher = updater.dispatcher

    dispatcher.add_handler(
        MessageHandler(
            Filters.text & ~Filters.update.edited_message & ~Filters.chat_type.private,
            message_handler,
        )
    )

    dispatcher.add_handler(
        CommandHandler("stats", stats_handler, Filters.chat_type.private)
    )

    # Start the Bot
    updater.start_polling()

    # Block until the user presses Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == "__main__":
    main()
