import logging

from telegram import Update
from telegram.ext import CallbackContext

from timezonefinder import TimezoneFinder

from quadsbot.user import User
from quadsbot.message_utils import delete_message
from quadsbot.handlers.message import message_handler

tzf = TimezoneFinder()


def location_handler(update: Update, context: CallbackContext) -> None:
    """
    Handles locations
    When a live location is sent, we want to set an override for the user's location
    This will be used when working with dates in the bot
    """
    logging.info("Handling Location")

    if update.message.location.live_period:
        logging.info("Got Live Location")

        # Calculate Timezone
        latitude = update.message.location.latitude
        longitude = update.message.location.longitude
        user_timezone = tzf.timezone_at(lat=latitude, lng=longitude)

        # Set the timezone in user_info
        with User(update, context) as user_info:
            user_info['tz'] = user_timezone

        # Send Confirmation & delete after 2 seconds
        confirm_message = update.message.chat.send_message(
                f"Set your timezone to {user_timezone}"
        )
        context.job_queue.run_once(delete_message, 2, context={
            "chat_id": confirm_message.chat_id,
            "message_id": confirm_message.message_id,
        })

        # Always delete message
        update.message.delete()
    else:
        logging.info("Got Normal Location -- Doing nothing")

        # Handle message like normal
        message_handler(update, context)
