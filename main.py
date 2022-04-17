import logging
import os

from quadsbot.handlers.leaderboard import leaderboard_handler
from quadsbot.handlers.stats import stats_handler
from quadsbot.handlers.clear import clear_handler
from quadsbot.handlers.check import check_handler
from quadsbot.handlers.location import location_handler
from quadsbot.handlers.message import message_handler

from telegram.ext import (
    Updater,
    MessageHandler,
    CommandHandler,
    Filters,
    PicklePersistence,
)

# Enable logging
logging.basicConfig(
    format="%(levelname)-7s %(asctime)s %(name)s %(message)s", level=logging.INFO
)


def main() -> None:
    # >> Setup persistance

    # Don't store `user_data`, we use it as a temporary store
    persistence_location = os.environ.get("PERSISTENCE_FILE", "/data/stats")
    persistence = PicklePersistence(
        filename=persistence_location, store_user_data=False
    )

    # >> Setup the Bot

    updater = Updater(
        token=os.environ["TELEGRAM_BOT_TOKEN"],
        persistence=persistence
    )
    dispatcher = updater.dispatcher

    # >> Command Hanlders

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

    # >> Location Handler

    dispatcher.add_handler(MessageHandler(Filters.location, location_handler))

    # >> Default Message Handler

    dispatcher.add_handler(
        MessageHandler(
            ~Filters.update.edited_message & ~Filters.chat_type.private,
            message_handler,
        )
    )

    # >> Start the Bot

    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()
