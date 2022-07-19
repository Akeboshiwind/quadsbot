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

    persistence_location = os.environ.get("PERSISTENCE_FILE", "/data/stats")
    persistence = PicklePersistence(filename=persistence_location)

    # >> Setup the Bot

    updater = Updater(token=os.environ["TELEGRAM_BOT_TOKEN"], persistence=persistence)
    dispatcher = updater.dispatcher

    # >> Handle bot_data migration
    # The previous version used the entire bot_data dict to store the user
    # stats. We want this to be under a sub_key so we can store other things
    # too.

    if "user_stats" not in dispatcher.bot_data:
        print("Running migration")

        import copy

        stats = copy.deepcopy(dispatcher.bot_data)
        dispatcher.bot_data.clear()
        dispatcher.bot_data["user_stats"] = stats
        dispatcher.update_persistence()

    # >> Setup bot_data

    if "user_stats" not in dispatcher.bot_data:
        dispatcher.bot_data.setdefault("user_stats", {})
        dispatcher.update_persistence()

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
