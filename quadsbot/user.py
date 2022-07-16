import os

from telegram import Update
from telegram.ext import CallbackContext

default_tz = os.environ.get("TZ", "Europe/London")


class User():
    """
    A ContextManager that:
    - Set's up the defaults of the user data
    - Saves the user data on context exit

    # Usage
    ```python
    with User(update, context) as user_info:
        print(user_info["username"])
        user_info["messages_total"] += 1
        user_info["some_new_value"] = "Hi!"
    ```
    """

    def __init__(self, update: Update, context: CallbackContext):
        # Because we're basically a wrapper around bot_data, store the bot_data
        # and user_id
        self._bot_data = context.bot_data

        # If the message was forwarded use the forwarded user
        if update.effective_message.forward_from:
            user = update.effective_message.forward_from
        else:
            user = update.effective_message.from_user
        self._user_id = user.id

        # Get the currently stored user_info
        user_info = self._bot_data.get(self._user_id, {})

        # Always update username
        username = user.username
        if not username:
            username = user.first_name
            if user.last_name:
                username += f" {user.last_name}"
        user_info["username"] = username

        # Set defaults for the usual values
        # (Doesn't override the current value)
        user_info.setdefault("checked_total", 0)
        user_info.setdefault("checked_unique", 0)
        user_info.setdefault("deleted", 0)
        user_info.setdefault("passed", 0)
        user_info.setdefault("messages_total", 0)
        user_info.setdefault("tz", default_tz)
        user_info.setdefault("check_id_cache", [])

        # Update the stored user_info
        self._bot_data[self._user_id] = user_info

        # Store a reference to the object we'll give to the user
        self.user_info = user_info

    def __enter__(self):
        return self.user_info

    def __exit__(self, type, value, traceback):
        # Limit size of the check_id_cache for memory usage
        self.user_info["check_id_cache"] = self.user_info["check_id_cache"][-10:]

        # Update the stored user_info
        self._bot_data[self._user_id] = self.user_info
