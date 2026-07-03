"""
i18n.py
-------
جدول نصوص الواجهة (إنجليزي بس - qfluentwidgets مبيدعمش RTL كويس للواجهة نفسها)
+ كاشف اتجاه النص (RTL/LTR) لمحتوى الكروت (سؤال/جواب).
"""

import re

_ARABIC_RE = re.compile(r"[؀-ۿݐ-ݿࢠ-ࣿﭐ-﷿ﹰ-﻿]")

STRINGS = {
    "window_title": "Anki Inbox",
    "nav_review": "Review",
    "nav_settings": "Settings",
    "review_title": "{n} new message(s) with cards",
    "review_subtitle": "Uncheck anything you don't want, then click Save.",
    "deck_count": "Deck: {deck}  •  {n} card(s)",
    "more_cards": "  ... and {n} more",
    "btn_save": "Save selected to Anki",
    "btn_discard": "Discard all",
    "discard_confirm_title": "Confirm",
    "discard_confirm_body": "Discard all these messages without saving?",
    "discard_done_title": "Done",
    "discard_done_body": "All messages discarded.",
    "no_selection_title": "Nothing selected",
    "no_selection_body": "Nothing is checked to save.",
    "save_error_title": "Error",
    "save_error_body": "Failed to save to Anki: {error}",
    "save_success_title": "Saved",
    "save_success_body": "Added {success}/{total} card(s) to Anki.",
    "settings_title": "Settings",
    "label_token": "Bot Token",
    "placeholder_token": "Telegram bot token (from @BotFather)",
    "label_chat_id": "Chat ID",
    "placeholder_chat_id": "Your chat ID",
    "label_deck": "Default Deck",
    "label_notetype": "Default Note Type",
    "auto_mode_title": "Auto Mode",
    "auto_mode_desc": "When on, cards save to Anki automatically without a review screen.",
    "btn_save_settings": "Save Settings",
    "settings_saved_title": "Saved",
    "settings_saved_body": "Settings updated.",
}


def t(key: str, **kwargs) -> str:
    text = STRINGS.get(key, key)
    return text.format(**kwargs) if kwargs else text


def is_rtl_text(text: str) -> bool:
    """True لو النص فيه حروف عربية (يستخدم لمحاذاة محتوى الكروت مش الواجهة نفسها)."""
    return bool(_ARABIC_RE.search(text or ""))
