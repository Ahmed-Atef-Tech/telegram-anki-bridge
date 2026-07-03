# Anki Inbox

Turn a message on your phone or a file on your laptop into an Anki flashcard automatically - no opening Anki, no typing it in by hand.

## How it works

1. **From your phone:** message your private Telegram bot with `Question,Answer` (or several lines for several cards, plus an optional 3rd column for tags).
   **From your laptop:** use the Import tab - paste CSV/TSV text, browse a file, or drag-and-drop a `.csv`/`.txt`/`.tsv` file.
2. Optionally override the deck/note type for that batch with header lines:
   ```
   #deck: My Deck Name
   #notetype: Basic
   ```
3. Open the app (or let it run automatically at Windows logon) - it shows a Review screen so you can approve/reject before anything is saved to Anki via [AnkiConnect](https://ankiweb.net/shared/info/2055492159).
4. Turn on **Auto Mode** in Settings to skip the review screen and save automatically.

Duplicate cards can be preserved, updated in place, or always added as new copies (Settings > Duplicate Handling), and every saved batch shows up in the **History** tab for browsing or deleting later.

## Download

Grab the latest `AnkiInbox.exe` from the [Releases page](https://github.com/Ahmed-Atef-Tech/telegram-anki-bridge/releases/latest) - no Python install required.

## Setup

1. Install [AnkiConnect](https://ankiweb.net/shared/info/2055492159) in Anki.
2. Create a Telegram bot via [@BotFather](https://t.me/BotFather) and copy its token.
3. Run `AnkiInbox.exe`, open Settings, paste the token, send any message to your bot, then click **Detect from last message** to fill in your Chat ID.
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
pyinstaller --noconfirm --onefile --windowed --name AnkiInbox --icon app_icon.ico --collect-all qfluentwidgets --collect-all qframelesswindow --collect-all darkdetect gui_app.py
```

## Built with

PyQt6, [PyQt6-Fluent-Widgets](https://qfluentwidgets.com), AnkiConnect, python-telegram Bot API.

---

Built by [Ahmed Atef](https://ahmed-atef-tech.github.io).
