import logging

from telegram.ext import CallbackContext


def delete_message(context: CallbackContext) -> None:
    """
    A job which will delete the given message
    The context (in context.job.context) is a dict that looks like this:
    {
        "chat_id": 1234,
        "message_id": 1234,
    }
    """
    logging.info("Deleting delayed message")

    chat_id = context.job.context["chat_id"]
    message_id = context.job.context["message_id"]
    logging.info(f"Chat ID: {chat_id}")
    logging.info(f"Message ID: {message_id}")

    context.bot.delete_message(chat_id, message_id)
