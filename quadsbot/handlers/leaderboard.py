import logging

from telegram import Update
from telegram.ext import CallbackContext

from quadsbot.handlers.message import message_handler, State


def leaderboard(user_stats) -> str:
    # Get user objects, sorted by score
    score_field = "checked_unique"
    scores = [score for _, score in user_stats.items()]
    scores = sorted(scores, key=lambda s: s[score_field], reverse=True)

    # Create message w/ Header
    message = "<b>Leaderboard</b>\n"

    if len(scores) >= 1:
        # Format top scorer specially
        top = scores[0]
        top_score = top[score_field]
        top_user = top["username"]

        message += f"1. {top_score} - 👑 <b>{top_user}</b> 👑"

        # Add the rest of the scorers
        for idx, entry in enumerate(scores[1:]):
            # Convert to correct numbering
            place = idx + 2
            score = entry[score_field]
            username = entry["username"]
            message += f"\n{place}. {score} - {username}"
    else:
        message += "<i>Empty...</i>"

    return message


def leaderboard_handler(update: Update, context: CallbackContext) -> None:
    """
    Display a leaderboard of scores
    """
    logging.info("/leaderboard call")

    if update.message.chat.type != "private":
        # Process the message as normal in a channel
        state = message_handler(update, context)

        # Only output the leaderboard if the messages wouldn't be deleted
        if state in [State.DELETE, State.CHECK_THEN_DELETE]:
            return

    # Reply with the leaderboard
    message = leaderboard(context.bot_data["user_stats"])
    update.message.reply_html(message)
