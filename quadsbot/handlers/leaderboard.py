import logging

from telegram import Update
from telegram.ext import CallbackContext

from quadsbot.handlers.message import message_handler, State


def leaderboard_handler(update: Update, context: CallbackContext) -> None:
    """
    Display a leaderboard of scores
    """
    logging.info("/leaderboard call")

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
