import logging
import re
import os

from telegram import Update
from telegram.ext import Updater, MessageHandler, Filters, CallbackContext

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)

# Formats the date as a series of human readable numbers
# 2020-10-22T12:51:24 -> 20201022125124
format_string = '%Y%m%d%H%M%S'
format_string_12_hour = '%Y%m%d%I%M%S'

# A list of tuples
# The first value is a regex matcher for the above time format
# The second value is either a regex matcher for text contents
#
# The first one that matches is replied to with "Checked"
matchers = [
    (r'(\d)\1{3}', "quads"),        # 2022-03-01T22:22:00
    (r'(\d)\1{5}', "sexts"),        # 2022-03-01T22:22:22
    (r'(\d)\1{7}', "octs"),         # 2022-03-22T22:22:22
    (r'(\d)\1{9}', "decs"),         # 2022-11-11T11:11:11
    (r'11235?8?(13)?', "fibs"),     # 2022-03-11T23:58:13
]


def check(update: Update, context: CallbackContext) -> None:
    # We only delete messages when none of the matchers match
    delete_message = True

    # NOTE: I'm not sure if this will handle timezones nicely
    date_digits = update.message.date.strftime(format_string)
    date_digits_12_hour = update.message.date.strftime(format_string_12_hour)

    # Iterate over potential matches
    for (date_re, message_re) in matchers:
        # If matches date regex *and* message regex, then reply
        if re.search(date_re, date_digits) or \
                re.search(date_re, date_digits_12_hour):
            delete_message = False
            message_text = update.message.text.lower()
            if re.search(message_re, message_text):
                update.message.reply_text("Checked", quote=True)
                return

    if delete_message:
        update.message.delete()


def main() -> None:
    updater = Updater(os.environ["TELEGRAM_BOT_TOKEN"])

    dispatcher = updater.dispatcher
    dispatcher.add_handler(MessageHandler(
        Filters.text & ~Filters.update.edited_message,
        check))

    # Start the Bot
    updater.start_polling()

    # Block until the user presses Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()
