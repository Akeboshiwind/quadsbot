import logging
import re
import os
import json
from enum import Enum
from typing import Tuple, Optional

from telegram import Update
from telegram.ext import (
    Updater,
    MessageHandler,
    CommandHandler,
    Filters,
    CallbackContext,
    PicklePersistence,
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
    (r"^........(.)\1{3}", "quads"),  # 2022-03-01T22:22:00
    (r"^........(.)\1{5}", "sexts"),  # 2022-03-01T22:22:22
    (r"^......(.)\1{7}", "octs"),  # 2022-03-22T22:22:22
    (r"^....(.)\1{9}", "decs"),  # 2022-11-11T11:11:11
    (r"^..(.)\1{11}", "dodecs"),  # 2011-11-11T11:11:11
    # TODO: Disable after april fools
    (r"11235?8?(13)?", "fibs"),  # 2022-03-11T23:58:13
    (r"12345?6?7?", "incs"),  # 2022-03-11T23:45:67
]

State = Enum("State", "DELETE PASS CHECKED")


def check(dates: list[int], message_text: str) -> Tuple[State, Optional[str]]:
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
            date_match = re.search(date_re, date_digits)
            if date_match:
                delete_message = False
                if re.search(message_re, message_text):
                    # Extract the prefix of the match
                    # The string upto the end of the match
                    # This is useful for de-duping checks later on
                    date_prefix = message_text[: date_match.end()]

                    # Return:
                    # - The message_re as a key
                    # - The date prefix to help dedupe checks in the stats
                    return State.CHECKED, (message_re, date_prefix)

    if delete_message:
        return State.DELETE, None
    else:
        return State.PASS, None


def message_handler(update: Update, context: CallbackContext) -> None:
    """
    Given a text message, plans what to do with it. Then executes that plan.
    """
    dates = get_date_strings(update.message.date)
    state, check_info = check(dates, update.message.text)

    user_stats = context.bot_data.get(
        update.message.from_user.id,
        {
            "username": update.effective_user.username,
            "checked_total": 0,
            "checked_unique": 0,
            "deleted": 0,
            "passed": 0,
            "messages_total": 0,
        },
    )

    if state == State.CHECKED:
        user_stats["checked_total"] += 1

        # Unpack check_info
        (matcher, date_prefix) = check_info

        # Dedupe checks
        matched_prefixes = context.user_data.get(matcher, [])
        if date_prefix not in matched_prefixes:
            user_stats["checked_unique"] += 1

            matched_prefixes.append(date_prefix)
            context.user_data[matcher] = matched_prefixes

        logger.info(f"Checked `{dates}` with `{matcher}`")
        update.message.reply_text("Checked", quote=True)
    elif state == State.DELETE:
        user_stats["deleted"] += 1
        logger.info("Deleted Message")
        update.message.delete()
    elif state == State.PASS:
        user_stats["passed"] += 1
        logger.info("Passed")
        pass

    user_stats["messages_total"] += 1
    user_stats["username"] = update.effective_user.username

    context.bot_data[update.message.from_user.id] = user_stats


def stats_handler(update: Update, context: CallbackContext) -> None:
    """
    Given a text message, plans what to do with it. Then executes that plan.
    """
    logger.info("/stats call")
    update.message.reply_text(
        f"Date strings: {get_date_strings(update.message.date)}"
        f"\nStats: {json.dumps(context.bot_data)}"
    )


def clear_handler(update: Update, context: CallbackContext) -> None:
    """
    Clears the stored stats
    """
    logger.info("/clear call")
    context.user_data.clear()
    context.bot_data.clear()
    update.message.reply_text(f"\nStats: {json.dumps(context.bot_data)}")


def leaderboard_handler(update: Update, context: CallbackContext) -> None:
    """
    Clears the stored stats
    """
    logger.info("/leaderboard call")

    score_field = "checked_unique"
    scores = [score for _, score in context.bot_data.items()]
    scores = sorted(scores, key=lambda s: s[score_field], reverse=True)

    message = "<b>Leaderboard</b>\n"

    if len(scores) >= 1:
        top = scores[0]
        top_score = top[score_field]
        top_user = top['username']

        message += f"1. {top_score} - 👑 <b>{top_user}</b> 👑"

        for idx, entry in enumerate(scores[1:]):
            # Convert to correct numbering
            idx += 2
            score = entry[score_field]
            user = entry['username']
            message += f"\n{idx}. {score} - {user}"
    else:
        message += "<i>Empty...</i>"

    update.message.reply_html(message)


def main() -> None:
    # Here we use persistence to store stats that we use to calculate the leaderboard
    # and debug
    # We don't store `user_data` as we want that to just be a temporary store for
    # de-duping purposes
    persistence_location = os.environ.get("PERSISTENCE_FILE", "/data/stats")
    persistence = PicklePersistence(
        filename=persistence_location, store_user_data=False
    )
    updater = Updater(token=os.environ["TELEGRAM_BOT_TOKEN"], persistence=persistence)

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

    dispatcher.add_handler(
        CommandHandler("leaderboard", leaderboard_handler, Filters.chat_type.private)
    )

    dispatcher.add_handler(
        CommandHandler("clear", clear_handler, Filters.chat_type.private)
    )

    # Start the Bot
    updater.start_polling()

    # Block until the user presses Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == "__main__":
    main()
