import logging

from telegram import Update
from telegram.ext import CallbackContext
from telegram.ext.filters import User as UserFilter


def make_setadmin_handler(admin_filter: UserFilter):
    def setadmin_handler(update: Update, context: CallbackContext) -> None:
        """
        Set the admin for the bot.
        Restricts permissions to some commands.
        """
        logging.info("/setadmin call")
        admin_id = update.effective_message.from_user.id
        context.bot_data["admin_id"] = admin_id
        admin_filter.add_user_ids(admin_id)

        update.message.reply_text("Set as Admin")

    return setadmin_handler
