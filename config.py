"""
إعدادات المشروع - بتتحمّل من ملف .env المجاور (متسيبش أسرار في الكود نفسه).
عدّل القيم عن طريق save_setting() (بيستخدمها gui_app.py) مش بتعديل المتغيرات هنا مباشرة.
"""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv, set_key

# لو البرنامج متحول لـ exe (PyInstaller)، __file__ بيشاور على مجلد مؤقت بيتفك فيه الملفات،
# مش مكان الـ exe نفسه - عشان كده لازم نستخدم sys.executable في الحالة دي.
if getattr(sys, "frozen", False):
    BASE_DIR = Path(sys.executable).resolve().parent
else:
    BASE_DIR = Path(__file__).resolve().parent

ENV_FILE = BASE_DIR / ".env"
STATE_FILE = BASE_DIR / "telegram_offset.txt"
LOG_FILE = BASE_DIR / "bridge.log"

if not ENV_FILE.exists():
    ENV_FILE.touch()


def _load() -> None:
    load_dotenv(ENV_FILE, override=True)
    g = globals()

    g["TELEGRAM_BOT_TOKEN"] = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()

    chat_id_raw = os.getenv("YOUR_CHAT_ID", "").strip()
    g["YOUR_CHAT_ID"] = int(chat_id_raw) if chat_id_raw else None

    g["ANKI_CONNECT_URL"] = os.getenv("ANKI_CONNECT_URL", "http://127.0.0.1:8765").strip()
    g["ANKI_EXECUTABLE_PATH"] = os.getenv(
        "ANKI_EXECUTABLE_PATH", r"F:\Productivity\Anki Cards\Anki\anki.exe"
    ).strip()

    g["DEFAULT_DECK"] = os.getenv("DEFAULT_DECK", "Default").strip()
    g["DEFAULT_NOTE_TYPE"] = os.getenv("DEFAULT_NOTE_TYPE", "Basic").strip()

    g["AUTO_MODE"] = os.getenv("AUTO_MODE", "false").strip().lower() in ("1", "true", "yes")
    g["FIRST_RUN_DONE"] = os.getenv("FIRST_RUN_DONE", "false").strip().lower() in ("1", "true", "yes")

    g["ANKI_STARTUP_TIMEOUT_SEC"] = int(os.getenv("ANKI_STARTUP_TIMEOUT_SEC", "40"))
    g["TELEGRAM_REQUEST_TIMEOUT_SEC"] = int(os.getenv("TELEGRAM_REQUEST_TIMEOUT_SEC", "15"))
    g["STARTUP_DELAY_SEC"] = int(os.getenv("STARTUP_DELAY_SEC", "15"))


def save_setting(key: str, value) -> None:
    """بيكتب قيمة جوا .env (من غير ما يلمس باقي السطور)، وبيعيد تحميل كل الإعدادات."""
    if isinstance(value, bool):
        value = "true" if value else "false"
    set_key(str(ENV_FILE), key, str(value))
    _load()


_load()
