"""
telegram_to_anki.py
--------------------
بيدور على آخر رسايل بعتها لبوت تيليجرام بتاعك (نص أو ملف CSV/TSV مرفق)،
ويحولها لكروت Anki تلقائي عن طريق AnkiConnect.

المتطلبات قبل التشغيل:
  1) Anki + add-on "AnkiConnect" (كود 2055492159)
  2) بوت تيليجرام (اتعمل عن طريق @BotFather) ومعاك التوكن بتاعه
  3) pip install -r requirements.txt

الإعدادات كلها في ملف .env المجاور (شوف .env.example). أول مرة تشغّل السكريبت
وYOUR_CHAT_ID لسه فاضي، هيطبعلك الـ Chat ID بتاعك في اللوج - انسخه لـ .env.
"""

import csv
import logging
import subprocess
import sys
import time
from logging.handlers import RotatingFileHandler

import requests

import config

log = logging.getLogger("telegram_to_anki")


def setup_logging() -> None:
    log.setLevel(logging.INFO)
    fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", "%Y-%m-%d %H:%M:%S")

    file_handler = RotatingFileHandler(config.LOG_FILE, maxBytes=1_000_000, backupCount=3, encoding="utf-8")
    file_handler.setFormatter(fmt)
    log.addHandler(file_handler)

    # نسخة الـ exe المبنية بـ --windowed مفيهاش console حقيقي، وsys.stdout بيبقى إما None أو
    # stream بترميز مش utf-8 بيعمل كراش على النصوص العربية/الإيموجي - عشان كده منضيفهوش غير في وضع التطوير.
    if not getattr(sys, "frozen", False) and sys.stdout is not None:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(fmt)
        log.addHandler(console_handler)


def get_last_offset() -> int:
    if config.STATE_FILE.exists():
        try:
            return int(config.STATE_FILE.read_text().strip() or 0)
        except ValueError:
            return 0
    return 0


def save_offset(offset: int) -> None:
    config.STATE_FILE.write_text(str(offset))


def anki_connect_reachable() -> bool:
    try:
        resp = requests.post(config.ANKI_CONNECT_URL, json={"action": "version", "version": 6}, timeout=3)
        return resp.ok and resp.json().get("error") is None
    except requests.RequestException:
        return False


def ensure_anki_running() -> bool:
    """يتأكد إن Anki شغال ومتاح عن طريق AnkiConnect، ولو لأ يحاول يشغّله."""
    if anki_connect_reachable():
        log.info("Anki شغال بالفعل ومتصل بـ AnkiConnect.")
        return True

    log.warning("Anki مش شغال أو AnkiConnect مش متاح - بحاول أشغّل Anki...")
    try:
        subprocess.Popen([config.ANKI_EXECUTABLE_PATH], close_fds=True)
    except OSError as e:
        log.error(f"❌ فشل تشغيل Anki من المسار: {config.ANKI_EXECUTABLE_PATH} ({e})")
        return False

    deadline = time.monotonic() + config.ANKI_STARTUP_TIMEOUT_SEC
    while time.monotonic() < deadline:
        if anki_connect_reachable():
            log.info("✅ Anki اشتغل وبقى متاح عن طريق AnkiConnect.")
            return True
        time.sleep(2)

    log.error("❌ Anki اتشغّل بس AnkiConnect لسه مش راضي يرد بعد المهلة.")
    return False


def anki_request(action: str, **params):
    payload = {"action": action, "version": 6, "params": params}
    resp = requests.post(config.ANKI_CONNECT_URL, json=payload, timeout=10)
    resp.raise_for_status()
    result = resp.json()
    if result.get("error"):
        raise RuntimeError(f"AnkiConnect error [{action}]: {result['error']}")
    return result["result"]


def resolve_deck_name(deck: str) -> str:
    """مطابقة case-insensitive مع الديكات الموجودة (لو الاسم جديد كليًا هيتعمل بنفس الحروف اللي كتبتها)."""
    existing_decks = anki_request("deckNames")
    for existing in existing_decks:
        if existing.lower() == deck.lower():
            return existing
    return deck


def ensure_deck_exists(deck: str) -> None:
    anki_request("createDeck", deck=deck)  # آمن لو الديك موجود بالفعل


def resolve_notetype_name(notetype: str) -> str:
    """مطابقة case-insensitive مع أنواع النوت الموجودة - عشان الكتابة من الموبايل بتلخبط الحروف الكبيرة/الصغيرة."""
    existing_models = anki_request("modelNames")
    for existing in existing_models:
        if existing.lower() == notetype.lower():
            return existing
    raise RuntimeError(
        f"نوع النوت '{notetype}' مش موجود في Anki. المتاح: {', '.join(existing_models)}"
    )


def get_model_field_names(notetype: str):
    field_names = anki_request("modelFieldNames", modelName=notetype)
    if len(field_names) < 2:
        raise RuntimeError(f"نوع النوت '{notetype}' لازم يكون فيه حقلين على الأقل.")
    return field_names


def parse_csv_text_to_notes(text: str, deck: str, notetype: str):
    deck = resolve_deck_name(deck)
    notetype = resolve_notetype_name(notetype)
    field_names = get_model_field_names(notetype)

    data_lines = [line for line in text.strip().splitlines() if line.strip() and not line.strip().startswith("#")]
    if not data_lines:
        return [], deck

    delimiter = "\t" if "\t" in data_lines[0] else ","
    reader = csv.reader(data_lines, delimiter=delimiter)

    notes = []
    for row in reader:
        row = [c.strip() for c in row]
        if len(row) < 2 or not row[0] or not row[1]:
            continue

        # العقد: العمود الأول = أول حقل في النوت تايب، التاني = تاني حقل،
        # التالت (لو موجود) = tags. أي حقول زيادة في النوت تايب بتفضل فاضية.
        fields = {field_names[0]: row[0], field_names[1]: row[1]}
        tags = row[2].split() if len(row) > 2 and row[2] else []

        notes.append(
            {
                "deckName": deck,
                "modelName": notetype,
                "fields": fields,
                "tags": tags,
                "options": {"allowDuplicate": False},
            }
        )
    return notes, deck


def parse_message_to_notes(text: str):
    """بيحول نص رسالة (CSV أو TSV، مع هيدرز اختيارية #deck: / #notetype:) لقائمة نوتس لـ AnkiConnect."""
    deck = config.DEFAULT_DECK
    notetype = config.DEFAULT_NOTE_TYPE
    data_lines = []

    for raw_line in text.strip().splitlines():
        line = raw_line.strip()
        if not line:
            continue
        lower = line.lower()
        if lower.startswith("#deck:"):
            deck = line.split(":", 1)[1].strip()
        elif lower.startswith("#notetype:"):
            notetype = line.split(":", 1)[1].strip()
        elif line.startswith("#"):
            continue
        else:
            data_lines.append(raw_line)

    notes, deck = parse_csv_text_to_notes("\n".join(data_lines), deck, notetype)
    return notes, deck


def get_telegram_updates(offset: int):
    url = f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/getUpdates"
    resp = requests.get(
        url, params={"offset": offset, "timeout": 5}, timeout=config.TELEGRAM_REQUEST_TIMEOUT_SEC
    )
    resp.raise_for_status()
    data = resp.json()
    if not data.get("ok"):
        raise RuntimeError(f"Telegram API error: {data}")
    return data["result"]


def get_latest_chat_id():
    """بيدور على آخر رسالة اتبعتت للبوت (بغض النظر عن YOUR_CHAT_ID) ويرجع chat_id بتاعها، أو None لو مفيش."""
    updates = get_telegram_updates(0)
    for update in reversed(updates):
        message = update.get("message")
        if message:
            return message["chat"]["id"]
    return None


def download_telegram_file(file_id: str) -> str:
    base = f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}"
    resp = requests.get(f"{base}/getFile", params={"file_id": file_id}, timeout=config.TELEGRAM_REQUEST_TIMEOUT_SEC)
    resp.raise_for_status()
    data = resp.json()
    if not data.get("ok"):
        raise RuntimeError(f"Telegram getFile error: {data}")
    file_path = data["result"]["file_path"]

    file_resp = requests.get(
        f"https://api.telegram.org/file/bot{config.TELEGRAM_BOT_TOKEN}/{file_path}",
        timeout=config.TELEGRAM_REQUEST_TIMEOUT_SEC,
    )
    file_resp.raise_for_status()
    return file_resp.content.decode("utf-8-sig", errors="replace")


def send_telegram_message(chat_id: int, text: str) -> None:
    url = f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/sendMessage"
    try:
        requests.post(url, json={"chat_id": chat_id, "text": text}, timeout=config.TELEGRAM_REQUEST_TIMEOUT_SEC)
    except requests.RequestException as e:
        log.warning(f"⚠️  فشل إرسال رسالة تأكيد لتيليجرام: {e}")


def collect_message_notes(message: dict):
    """بيحوّل رسالة تيليجرام لـ (notes, deck, source_desc)، أو None لو مفيش حاجة تتعالج."""
    if "text" in message:
        notes, deck = parse_message_to_notes(message["text"])
        source = next((l for l in message["text"].strip().splitlines() if not l.strip().startswith("#")), message["text"])
        return notes, deck, source.strip()[:80]

    document = message.get("document")
    if document and document.get("file_name", "").lower().endswith((".csv", ".tsv", ".txt")):
        log.info(f"📎 استلمنا ملف مرفق: {document.get('file_name')}")
        text = download_telegram_file(document["file_id"])
        notes, deck = parse_message_to_notes(text)
        return notes, deck, document.get("file_name")

    return None


def fetch_pending_items(offset: int):
    """بيجيب رسايل تيليجرام الجديدة ويحوّلها لكروت (من غير ما يحفظهم في Anki). بيرجع (items, new_offset)."""
    updates = get_telegram_updates(offset)
    new_offset = offset
    items = []

    for update in updates:
        new_offset = update["update_id"] + 1
        message = update.get("message")
        if not message:
            continue
        chat_id = message["chat"]["id"]

        if config.YOUR_CHAT_ID is None:
            log.warning(f"⚠️  اكتشفنا إن الرسالة جاية من Chat ID: {chat_id}")
            log.warning("    حط الرقم ده في YOUR_CHAT_ID جوا ملف .env عشان بس رسايلك تتقبل.")
            continue

        if chat_id != config.YOUR_CHAT_ID:
            log.info(f"⏭️  رسالة من chat_id مش بتاعك ({chat_id}) - اتجاهلت.")
            continue

        try:
            result = collect_message_notes(message)
        except Exception as e:
            log.exception(f"❌ خطأ في معالجة رسالة: {e}")
            continue

        if not result:
            log.info("ℹ️  رسالة من غير نص أو ملف CSV/TSV مدعوم - اتجاهلت.")
            continue

        notes, deck, source = result
        if not notes:
            log.info("ℹ️  الرسالة دي مفيهاش كروت CSV/TSV صالحة - اتجاهلت.")
            continue

        items.append({"chat_id": chat_id, "deck": deck, "notes": notes, "source": source})

    return items, new_offset


def commit_items(items) -> tuple:
    """بيحفظ الآيتمز في Anki، وبيبعت تأكيد لكل chat_id. بيرجع (كروت اتضافت, كروت كلها)."""
    total_success = 0
    total_notes = 0
    per_chat_messages = {}

    for item in items:
        deck, notes, chat_id = item["deck"], item["notes"], item["chat_id"]

        ensure_deck_exists(deck)
        added = anki_request("addNotes", notes=notes)
        success = sum(1 for x in added if x is not None)
        total_success += success
        total_notes += len(notes)

        msg = f"✅ اتضاف {success}/{len(notes)} كارت في ديك '{deck}'"
        if success < len(notes):
            msg += f" ({len(notes) - success} اتجاهلوا، غالبًا duplicates)"
        log.info(msg)
        per_chat_messages.setdefault(chat_id, []).append(msg)

    for chat_id, msgs in per_chat_messages.items():
        send_telegram_message(chat_id, "\n".join(msgs))

    return total_success, total_notes


def main() -> None:
    setup_logging()
    log.info("=" * 50)
    log.info("🔍 بدء تشغيل Telegram → Anki Bridge")

    if "--startup" in sys.argv:
        log.info(f"⏳ استنى {config.STARTUP_DELAY_SEC} ثانية عشان النت وويندوز يستقروا بعد تسجيل الدخول...")
        time.sleep(config.STARTUP_DELAY_SEC)

    if not config.TELEGRAM_BOT_TOKEN:
        log.error("❌ TELEGRAM_BOT_TOKEN فاضي في .env - حط التوكن وشغّل تاني.")
        sys.exit(1)

    if not ensure_anki_running():
        log.error("❌ مش هينفع نكمل من غير Anki + AnkiConnect.")
        sys.exit(1)

    offset = get_last_offset()

    try:
        items, new_offset = fetch_pending_items(offset)
    except requests.RequestException as e:
        log.error(f"❌ فشل الاتصال بـ Telegram (اتأكد من النت): {e}")
        sys.exit(1)
    except RuntimeError as e:
        log.error(f"❌ {e}")
        sys.exit(1)

    if not items:
        log.info("لا يوجد رسايل جديدة فيها كروت.")
        save_offset(new_offset)
        return

    commit_items(items)
    save_offset(new_offset)
    log.info("🏁 خلصنا.")


if __name__ == "__main__":
    main()
