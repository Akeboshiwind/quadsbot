# Quads Bot

A silly bot for my friend group's chat group in telegram

## Running it

```bash
$ export TELEGRAM_BOT_TOKEN="<your token here>"
$ export PERSISTENCE_FILE="./stats"
$ export TZ="<your timezone (pytz)>"
$ poetry install
$ poetry run python main.py
```

## Features

- Replies with "Checked" to valid "quads" and "sexts" messages
- If the bot has permissions to delete messages then all messages not sent on quads will be deleted
- Has a `/leaderboard` command which keeps track of the amount of unique "checks" a user has

## Caveats

- Needs permissions to reply to messages
- Optionally needs permissions to delete messages
