"""
guide_content.py
-----------------
النصوص الطويلة لشاشة الترحيب وتاب الـ Guide وبرومبتات الـ AI - في ملف منفصل
عشان gui_app.py يفضل قابل للقراءة.
"""

WELCOME_TEXT = """Welcome to Anki Inbox!

THE PROBLEM THIS SOLVES
You're reading something - on your phone or your laptop - and want to turn a
fact into an Anki flashcard right now, without opening Anki and typing it in
manually. Send a message to a private Telegram bot from your phone, or paste/
drop a file into the Import tab on your laptop, and the card appears in your
Anki deck automatically.

HOW TO USE IT
1. From your phone: message your Telegram bot with a card, like this:
     Question,Answer
   From your laptop: use the Import tab the same way (paste, browse, or
   drag-and-drop a .csv/.txt/.tsv file).
   You can send several cards at once (one per line), and optionally add tags:
     Question,Answer,tag1 tag2
   You can also override the deck/note type for that batch by adding these
   as the first lines:
     #deck: My Deck Name
     #notetype: Basic

2. This app checks your bot automatically when you log into Windows, or you
   can open it manually anytime. If it finds new cards, it shows you a Review
   screen so you approve or reject before anything is saved to Anki. Turn on
   "Auto Mode" in Settings if you'd rather it save automatically with no review.

SETTING UP YOUR OWN BOT (only needed once, already done for you)
1. Open Telegram, search for @BotFather.
2. Send /newbot, give it a name, then a username ending in "bot".
3. BotFather gives you a token - paste it into Settings > Bot Token.
4. Send any message to your new bot, then open this app - it detects your
   Chat ID automatically and shows it in the log so only you can use the bot.

Check the Guide tab any time you need this again - it also has ready-made
prompts you can copy into ChatGPT/Claude/Gemini to turn any text into
correctly formatted cards.
"""

GUIDE_SECTIONS = [
    (
        "What problem does this solve?",
        "You're reading something on your phone and want to turn a fact into an Anki "
        "flashcard right now - without touching a laptop. Send a message to your private "
        "Telegram bot, and the card shows up in Anki automatically.",
    ),
    (
        "How to send a card",
        "Message your bot with:\n"
        "  Question,Answer\n"
        "One card per line for multiple cards. Add tags as a 3rd column:\n"
        "  Question,Answer,tag1 tag2\n"
        "Override the deck or note type for that message with optional header lines "
        "at the very top:\n"
        "  #deck: My Deck Name\n"
        "  #notetype: Basic\n"
        "You can also attach a .csv/.txt/.tsv file instead of typing in the message.",
    ),
    (
        "How the app checks for new cards",
        "It runs automatically at Windows logon. If it finds new messages, it shows a "
        "Review screen so you approve or reject before anything touches Anki. Turn on "
        "Auto Mode (Settings) to skip the review screen and save automatically.",
    ),
    (
        "Importing from your laptop",
        "Use the Import tab to add cards straight from your PC - paste CSV/TSV text, browse for "
        "a file, or drag-and-drop a .csv/.txt/.tsv file onto the window. It goes through the same "
        "Review screen as Telegram messages before anything is saved.",
    ),
    (
        "Duplicate handling & History",
        "Settings > Duplicate Handling controls what happens when a card already exists: "
        "Preserve skips it, Update overwrites the existing card's fields, and Duplicate always "
        "adds a new copy. Match Scope decides whether \"already exists\" is checked within the "
        "target deck or across your whole collection. Every batch you save shows up in the "
        "History tab, where you can jump to those cards in Anki's Browser or delete the whole "
        "batch in one click.",
    ),
    (
        "Setting up a Telegram bot (already done for you)",
        "1. Open Telegram, search @BotFather.\n"
        "2. Send /newbot, give it a name, then a username ending in \"bot\".\n"
        "3. Copy the token BotFather gives you into Settings > Bot Token.\n"
        "4. Send any message to your bot, then open this app - your Chat ID is "
        "detected automatically.",
    ),
    (
        "Finding your Chat ID again",
        "Send any message to your bot from Telegram, then open this app (or click "
        "\"Detect from last message\" next to the Chat ID field in Settings).",
    ),
]

PROMPTS = [
    (
        "Basic",
        "Basic Q&A cards - a question on the front, an answer on the back.",
        """You are a flashcard generator. Convert the study material I give you into Anki flashcards in this EXACT plain-text format, ready to paste into a Telegram bot:

#deck: <pick an appropriate deck name, or Default>
#notetype: Basic
Question 1,Answer 1,optional-tag
Question 2,Answer 2

Rules:
- Separate the front and back with a comma. If a field itself contains a comma, wrap that field in double quotes.
- One card per line.
- Keep each question and answer concise and clear - no walls of text.
- The 3rd column (tags) is optional; separate multiple tags with a space.
- Output ONLY the formatted lines above (plus the #deck/#notetype header) - no explanations, no markdown code fences, no numbering.

Here is the material:
[PASTE YOUR MATERIAL HERE]""",
    ),
    (
        "Basic (reversed)",
        "Same as Basic, but Anki also quizzes you backwards (back → front). Good for vocab/definitions.",
        """You are a flashcard generator. Convert the study material I give you into Anki flashcards in this EXACT plain-text format, ready to paste into a Telegram bot:

#deck: <pick an appropriate deck name, or Default>
#notetype: Basic (and reversed card)
Term 1,Definition 1,optional-tag
Term 2,Definition 2

Rules:
- Front = term/word, Back = its definition/translation (Anki will quiz both directions automatically).
- Separate the front and back with a comma. If a field itself contains a comma, wrap that field in double quotes.
- One card per line.
- The 3rd column (tags) is optional; separate multiple tags with a space.
- Output ONLY the formatted lines above (plus the #deck/#notetype header) - no explanations, no markdown code fences, no numbering.

Here is the material:
[PASTE YOUR MATERIAL HERE]""",
    ),
    (
        "Cloze",
        "Fill-in-the-blank cards - the key term inside the sentence is hidden and quizzed.",
        """You are a flashcard generator. Convert the study material I give you into Anki Cloze deletion cards in this EXACT plain-text format, ready to paste into a Telegram bot:

#deck: <pick an appropriate deck name, or Default>
#notetype: Cloze
The mitochondria is the {{c1::powerhouse}} of the cell.,,optional-tag
{{c1::Paris}} is the capital of France.,,geography

Rules:
- First column = the full sentence with the key term(s) wrapped in {{c1::term}}. Use {{c2::...}} for a second blank in the same sentence if needed.
- Second column is left empty (still needs the comma) unless you want to add an extra hint/context there.
- Third column (tags) is optional.
- One cloze card per line. Don't cram more than 1-2 blanks into a single sentence.
- Output ONLY the formatted lines above (plus the #deck/#notetype header) - no explanations, no markdown code fences, no numbering.

Here is the material:
[PASTE YOUR MATERIAL HERE]""",
    ),
]
