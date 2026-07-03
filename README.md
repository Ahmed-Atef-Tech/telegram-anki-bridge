# Telegram → Anki Bridge

Send a message to a private Telegram bot from your phone, and it turns into an Anki flashcard automatically. No laptop, no opening Anki - just message the bot and review/save the card when you're ready.

## How it works

1. Message your bot: `Question,Answer` (or several lines for several cards, plus an optional 3rd column for tags).
2. Optionally override the deck/note type for that message with header lines:
   ```
   #deck: My Deck Name
   #notetype: Basic
   ```
3. Open the app (or let it run automatically at Windows logon) - it fetches new messages, shows a Review screen so you can approve/reject, and saves to Anki via [AnkiConnect](https://ankiweb.net/shared/info/2055492159).
4. Turn on **Auto Mode** in Settings to skip the review screen and save automatically.

You can also attach a `.csv`/`.txt`/`.tsv` file instead of typing the cards in the message body.

## Download

Grab the latest `TelegramAnkiBridge.exe` from the [Releases page](https://github.com/Ahmed-Atef-Tech/telegram-anki-bridge/releases/latest) - no Python install required.

## Setup

1. Install [AnkiConnect](https://ankiweb.net/shared/info/2055492159) in Anki.
2. Create a Telegram bot via [@BotFather](https://t.me/BotFather) and copy its token.
3. Run `TelegramAnkiBridge.exe`, open Settings, paste the token, send any message to your bot, then click **Detect from last message** to fill in your Chat ID.
4. Check the in-app **Guide** tab for the full walkthrough and ready-made AI prompts for generating cards from study material.

## Running from source

```
pip install -r requirements.txt
python gui_app.py            # normal run: fetch + review
python gui_app.py --settings # open settings directly
python gui_app.py --startup  # used by the Windows Startup shortcut
```

Building the executable:

```
pyinstaller --noconfirm --onefile --windowed --name TelegramAnkiBridge --icon icons8-anki-480.ico --collect-all qfluentwidgets --collect-all qframelesswindow --collect-all darkdetect gui_app.py
```

## Built with

PyQt6, [PyQt6-Fluent-Widgets](https://qfluentwidgets.com), AnkiConnect, python-telegram Bot API.

---

Built by [Ahmed Atef](https://ahmed-atef-tech.github.io).
