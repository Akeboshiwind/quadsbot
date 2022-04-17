import re
import logging
from enum import Enum
from typing import Tuple, Optional

from telegram import Update
from telegram.ext import CallbackContext

from quadsbot.date_utils import get_date_strings, is_april_fools_day
from quadsbot.user import User

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
    if is_april_fools_day(date, tz):
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
                    logging.info(f"Checked `{dates}` with `{message_text}` using `{message_re}`")
                    return State.CHECKED, (message_re, check_id)

    if delete_message:
        logging.info(f"Deleted `{dates}` with `{message_text}`")
        return State.DELETE, None
    else:
        logging.info(f"Passed `{dates}` with `{message_text}`")
        return State.PASS, None


def message_handler(update: Update, context: CallbackContext) -> State:
    """
    Given a text message, plans what to do with it. Then executes that plan.
    """
    logging.info("Handling Message")

    with User(update, context) as user_info:
        state, check_info = check(
            update.effective_message.date,
            user_info["tz"],
            update.effective_message.text
        )

        if state == State.CHECKED:
            user_info["checked_total"] += 1

            # Unpack check_info
            (matcher, check_id) = check_info

            # Dedupe checks
            # We use the `user_data` as a temporary cache
            matched_prefixes = context.user_data.get(matcher, [])
            if check_id not in matched_prefixes:
                logging.info("Check identified as unique")
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
        return state
