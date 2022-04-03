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
from timezonefinder import TimezoneFinder
from datetime import datetime

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

logger = logging.getLogger(__name__)

# Formats the date as a series of human readable numbers
# 2020-10-22T12:51:24 -> 20201022125124
# NOTE: Must be in 24 -> 12 hour order for the check_id below
format_strings = [
    "%Y%m%d%H%M%S",  # 24 hour
    "%Y%m%d%I%M%S",  # 12 hour
]
default_tz = os.environ.get("TZ", "Europe/London")
tzf = TimezoneFinder()


def get_date_strings(date: datetime, tz: str) -> list[int]:
    # Convert date to bot timezone
    date = date.astimezone(pytz.timezone(tz))

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
]

# TODO: Remove after april fools
joke_matchers = [
    (r"11235?8?(13)?", "fibs"),  # 2022-03-11T23:58:13
    (r"12345?", "incs"),  # 2022-03-11T23:45:31
    (r"69", "sixty nine"),  # Not possible I think?
    (r"^........0420", r"(blaze it|blazeit)"),  # 2022-03-01T04:20:00
    (r"^........1337", r"(leet|l33t|1337)"),  # 2022-03-01T13:37:00
    (r"^........0230", r"(tooth hurty|ow)"),  # 2022-03-01T02:30:00
    (r"^........0002", r"(poop|poopie|number 2|no\. 2)"),  # 2022-03-01T00:02:00
    (r"^........0001", r"(peepee|pee pee|number 1|no\. 1)"),  # 2022-03-01T00:01:00
    (r"^........0314", r"(pi|pie)"),  # 2022-03-01T03:14:00
]

State = Enum("State", "DELETE PASS CHECKED")


def isAprilFoolsDay(date: datetime, tz) -> bool:
    now = date.astimezone(pytz.timezone(tz))
    return now.month == 4 and now.day == 1


def check(date: datetime, tz: str, message_text: Optional[str]) -> Tuple[State, Optional[Tuple[str, str]]]:
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

    dates = get_date_strings(date, tz)
    if not message_text:
        message_text = ""
    message_text = message_text.lower()

    more_matchers = matchers
    if isAprilFoolsDay(date, tz):
        more_matchers = matchers + joke_matchers

    for (date_re, message_re) in more_matchers:
        for date_idx, date_digits in enumerate(dates):
            date_match = re.search(date_re, date_digits)
            if date_match:
                delete_message = False
                if re.search(message_re, message_text):
                    # The string upto the end of the match
                    date_prefix = date_digits[: date_match.end()]

                    # The id for this specific check
                    # We use the date prefix to identify when the match happened
                    # (it includes the match itself so we don't id other matches)
                    # We use the index of the date_digits to differentiate between 24
                    # and 12 hour dates
                    check_id = date_prefix + str(date_idx)

                    # Return:
                    # - The message_re as a key
                    # - The check_id to help dedupe checks in the stats
                    logger.info(f"Checked `{dates}` with `{message_text}` using `{message_re}`")
                    return State.CHECKED, (message_re, check_id)

    if delete_message:
        logger.info(f"Deleted `{dates}` with `{message_text}`")
        return State.DELETE, None
    else:
        logger.info(f"Passed `{dates}` with `{message_text}`")
        return State.PASS, None


def message_handler(update: Update, context: CallbackContext) -> State:
    """
    Given a text message, plans what to do with it. Then executes that plan.
    """
    logger.info("Handling Message")

    user_info = context.bot_data.get(
        update.message.from_user.id,
        {
            "username": update.effective_user.username,
            "checked_total": 0,
            "checked_unique": 0,
            "deleted": 0,
            "passed": 0,
            "messages_total": 0,
            "tz": default_tz,
        },
    )

    # Migrate users which don't have a timezone set
    # TODO: Remove?
    if not user_info.get("tz"):
        user_info["tz"] = default_tz

    state, check_info = check(update.effective_message.date, user_info["tz"], update.effective_message.text)

    if state == State.CHECKED:
        user_info["checked_total"] += 1

        # Unpack check_info
        (matcher, check_id) = check_info

        # Dedupe checks
        # We use the `user_data` as a temporary cache
        matched_prefixes = context.user_data.get(matcher, [])
        if check_id not in matched_prefixes:
            logger.info("Check identified as unique")
            user_info["checked_unique"] += 1

            matched_prefixes.append(check_id)
            context.user_data[matcher] = matched_prefixes

        update.message.reply_text("Checked", quote=True)
    elif state == State.DELETE:
        user_info["deleted"] += 1
        update.message.delete()
    elif state == State.PASS:
        user_info["passed"] += 1
        pass

    user_info["messages_total"] += 1
    user_info["username"] = update.effective_user.username

    context.bot_data[update.message.from_user.id] = user_info

    return state


def stats_handler(update: Update, context: CallbackContext) -> None:
    """
    Given a text message, plans what to do with it. Then executes that plan.
    """
    logger.info("/stats call")

    user_timezone = default_tz
    if context.bot_data.get(update.message.from_user.id):
        user_info = context.bot_data[update.message.from_user.id]
        user_timezone = user_info.get("tz", default_tz)

    update.message.reply_text(
        f"Date strings: {get_date_strings(update.message.date, user_timezone)}"
        f"\nStats: {json.dumps(context.bot_data)}"
    )


def clear_handler(update: Update, context: CallbackContext) -> None:
    """
    Clears the stored stats
    """
    logger.info("/clear call")
    context.user_data.clear()
    context.bot_data.clear()
    update.message.reply_text(f"Stats: {json.dumps(context.bot_data)}")


def check_handler(update: Update, context: CallbackContext) -> None:
    """
    Manually run check
    """
    logger.info("/check call")

    date = update.message.date

    user_timezone = default_tz
    if context.bot_data.get(update.message.from_user.id):
        user_info = context.bot_data[update.message.from_user.id]
        user_timezone = user_info.get("tz", default_tz)

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

    update.message.reply_text(f"TZ: {user_timezone}\nState: {state}\nCheck Info: {check_info}")


def leaderboard_handler(update: Update, context: CallbackContext) -> None:
    """
    Display a leaderboard of scores
    """
    logger.info("/leaderboard call")

    if update.message.chat.type != "private":
        # Process the message as normal in a channel
        state = message_handler(update, context)

        # Only output the leaderboard if the messages wouldn't be deleted
        if state == State.DELETE:
            return

    score_field = "checked_unique"
    scores = [score for _, score in context.bot_data.items()]
    scores = sorted(scores, key=lambda s: s[score_field], reverse=True)

    message = "<b>Leaderboard</b>\n"

    if len(scores) >= 1:
        top = scores[0]
        top_score = top[score_field]
        top_user = top["username"]

        message += f"1. {top_score} - 👑 <b>{top_user}</b> 👑"

        for idx, entry in enumerate(scores[1:]):
            # Convert to correct numbering
            idx += 2
            score = entry[score_field]
            user = entry["username"]
            message += f"\n{idx}. {score} - {user}"
    else:
        message += "<i>Empty...</i>"

    update.message.reply_html(message)


def delete_message(context: CallbackContext) -> None:
    logger.info("Deleting delayed message")

    chat_id = context.job.context["chat_id"]
    message_id = context.job.context["message_id"]
    logger.info(f"Chat ID: {chat_id}")
    logger.info(f"Message ID: {message_id}")

    context.bot.delete_message(chat_id, message_id)


def location_handler(update: Update, context: CallbackContext) -> None:
    """
    Handles locations
    When a live location is sent, we want to set an override for the user's location
    This will be used when working with dates in the bot
    """
    logger.info("Handling Location")

    # Handle message like normal
    # NOTE: We do this first to ensure that `bot_data` is setup correctly
    #       The only issue with this method is that this message will be handled
    #       incorrectly if the user is does this on quads in a different timezone
    message_handler(update, context)

    if update.message.location.live_period:
        logger.info("Got Live Location")

        # Calculate Timezone
        latitude = update.message.location.latitude
        longitude = update.message.location.longitude
        user_timezone = tzf.timezone_at(lat=latitude, lng=longitude)

        # Set the timezone in user_info
        user_info = context.bot_data[update.message.from_user.id]
        user_info['tz'] = user_timezone
        context.bot_data[update.message.from_user.id] = user_info

        # Send Confirmation & delete after 2 seconds
        confirm_message = update.message.reply_text(f"Set your timezone to {user_timezone}")
        context.job_queue.run_once(delete_message, 2, context={
            "chat_id": confirm_message.chat_id,
            "message_id": confirm_message.message_id,
        })
    else:
        logger.info("Got Normal Location -- Doing nothing")



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

    dispatcher.add_handler(CommandHandler("leaderboard", leaderboard_handler))

    dispatcher.add_handler(
        CommandHandler("stats", stats_handler, Filters.chat_type.private)
    )

    dispatcher.add_handler(
        CommandHandler("clear", clear_handler, Filters.chat_type.private)
    )

    dispatcher.add_handler(
        CommandHandler("check", check_handler, Filters.chat_type.private)
    )

    dispatcher.add_handler(MessageHandler(Filters.location, location_handler))

    dispatcher.add_handler(
        MessageHandler(
            ~Filters.update.edited_message & ~Filters.chat_type.private,
            message_handler,
        )
    )

    # Start the Bot
    updater.start_polling()

    # Block until the user presses Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == "__main__":
    main()
