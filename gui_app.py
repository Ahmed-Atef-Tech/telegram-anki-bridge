"""
gui_app.py
----------
واجهة Fluent (Windows 11 style) لبرنامج Telegram → Anki Bridge.

- شاشة "المراجعة": بتظهر لو فيه كروت جديدة جاهزة، وتسيبك توافق أو ترفض قبل الحفظ.
- شاشة "الإعدادات": تعديل الديك الافتراضي، النوت تايب، بيانات البوت، ووضع Auto Mode.

الواجهة إنجليزي دايمًا (qfluentwidgets مبيدعمش RTL كويس للواجهة نفسها).
محتوى الكروت (سؤال/جواب) بيتحدد اتجاهه (RTL/LTR) تلقائي حسب اللغة الفعلية للنص.

طرق التشغيل:
  python gui_app.py            → المسار العادي (fetch + review لو AUTO_MODE مطفي)
  python gui_app.py --startup  → نفس الحاجة بس بتستنى STARTUP_DELAY_SEC الأول (لصنداي تسجيل الدخول)
  python gui_app.py --settings → يفتح شاشة الإعدادات على طول من غير ما يدور على رسايل
"""

import sys

from PyQt6.QtCore import Qt, QThread, QTimer, QUrl, pyqtSignal
from PyQt6.QtGui import QDesktopServices, QIcon
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QHBoxLayout,
    QMenu,
    QSystemTrayIcon,
    QVBoxLayout,
    QWidget,
)
from qfluentwidgets import (
    BodyLabel,
    CardWidget,
    CaptionLabel,
    EditableComboBox,
    FluentIcon,
    FluentWindow,
    HyperlinkButton,
    InfoBar,
    InfoBarPosition,
    LineEdit,
    MessageBox,
    MessageBoxBase,
    NavigationItemPosition,
    PrimaryPushButton,
    PushButton,
    ScrollArea,
    StrongBodyLabel,
    SubtitleLabel,
    SwitchButton,
    TextEdit,
    TitleLabel,
    setTheme,
    Theme,
)

import config
import telegram_to_anki as bridge
import updater
from guide_content import GUIDE_SECTIONS, PROMPTS, WELCOME_TEXT
from i18n import is_rtl_text, t


class UpdateCheckWorker(QThread):
    """بيدور على تحديثات في GitHub Releases في thread منفصل عشان متبطأش الواجهة."""

    result_ready = pyqtSignal(object)

    def run(self):
        try:
            result = updater.check_for_update()
        except Exception as e:
            bridge.log.warning(f"⚠️  فشل التأكد من وجود تحديث: {e}")
            result = None
        self.result_ready.emit(result)


def _content_label(text: str) -> BodyLabel:
    """QLabel بيتحدد اتجاهه ومحاذاته حسب اللغة الفعلية للنص (عربي أو إنجليزي)."""
    lbl = BodyLabel(text)
    lbl.setWordWrap(True)
    if is_rtl_text(text):
        lbl.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
    else:
        lbl.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        lbl.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
    return lbl


class ReviewInterface(QWidget):
    """شاشة مراجعة الكروت الجديدة قبل ما تتحفظ في Anki."""

    def __init__(self, items, new_offset, parent=None):
        super().__init__(parent)
        self.setObjectName("ReviewInterface")
        self.items = items
        self.new_offset = new_offset
        self.checkboxes = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 20, 30, 20)
        layout.setSpacing(12)

        layout.addWidget(TitleLabel(t("review_title", n=len(items))))
        layout.addWidget(CaptionLabel(t("review_subtitle")))

        scroll = ScrollArea()
        scroll.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setSpacing(10)

        for item in items:
            card = self._build_item_card(item)
            scroll_layout.addWidget(card)
        scroll_layout.addStretch(1)
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll, 1)

        btn_row = QHBoxLayout()
        self.save_btn = PrimaryPushButton(FluentIcon.SAVE, t("btn_save"))
        self.discard_btn = PushButton(FluentIcon.DELETE, t("btn_discard"))
        self.save_btn.setAutoDefault(False)
        self.save_btn.setDefault(False)
        self.discard_btn.setAutoDefault(False)
        self.discard_btn.setDefault(False)
        self.save_btn.clicked.connect(self.on_save)
        self.discard_btn.clicked.connect(self.on_discard)
        btn_row.addStretch(1)
        btn_row.addWidget(self.discard_btn)
        btn_row.addWidget(self.save_btn)
        layout.addLayout(btn_row)

    def _build_item_card(self, item) -> CardWidget:
        card = CardWidget()
        v = QVBoxLayout(card)
        v.setContentsMargins(16, 12, 16, 12)
        v.setSpacing(6)

        header = QHBoxLayout()
        checkbox = QCheckBox()
        checkbox.setChecked(True)
        self.checkboxes.append((checkbox, item))
        header.addWidget(checkbox)
        header.addWidget(StrongBodyLabel(t("deck_count", deck=item["deck"], n=len(item["notes"]))))
        header.addStretch(1)
        v.addLayout(header)

        for note in item["notes"][:5]:
            v.addWidget(self._build_note_row(note))

        if len(item["notes"]) > 5:
            v.addWidget(CaptionLabel(t("more_cards", n=len(item["notes"]) - 5)))

        return card

    def _build_note_row(self, note) -> QWidget:
        values = list(note["fields"].values())
        front = values[0] if len(values) > 0 else ""
        back = values[1] if len(values) > 1 else ""

        row = QWidget()
        h = QHBoxLayout(row)
        h.setContentsMargins(20, 0, 0, 0)
        h.setSpacing(8)
        h.addWidget(CaptionLabel("•"))
        h.addWidget(_content_label(front), 1)
        h.addWidget(BodyLabel("→"))
        h.addWidget(_content_label(back), 1)
        return row

    def on_discard(self):
        box = MessageBox(t("discard_confirm_title"), t("discard_confirm_body"), self.window())
        if box.exec():
            bridge.save_offset(self.new_offset)
            InfoBar.success(t("discard_done_title"), t("discard_done_body"), position=InfoBarPosition.TOP, parent=self.window())
            self.window().close()

    def on_save(self):
        approved = [item for checkbox, item in self.checkboxes if checkbox.isChecked()]
        if not approved:
            InfoBar.warning(t("no_selection_title"), t("no_selection_body"), position=InfoBarPosition.TOP, parent=self.window())
            return

        try:
            success, total = bridge.commit_items(approved)
        except Exception as e:
            InfoBar.error(t("save_error_title"), t("save_error_body", error=e), position=InfoBarPosition.TOP, parent=self.window())
            return

        bridge.save_offset(self.new_offset)
        InfoBar.success(
            t("save_success_title"),
            t("save_success_body", success=success, total=total),
            position=InfoBarPosition.TOP,
            parent=self.window(),
        )
        self.save_btn.setEnabled(False)
        self.discard_btn.setEnabled(False)


class SettingsInterface(QWidget):
    """شاشة إعدادات البرنامج - بتتكتب على طول في .env."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("SettingsInterface")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 20, 30, 20)
        layout.setSpacing(14)

        layout.addWidget(TitleLabel(t("settings_title")))

        # التوكن وChat ID دايمًا LTR - مش نص لغة، أكواد/أرقام.
        self.token_edit = LineEdit()
        self.token_edit.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        self.token_edit.setText(config.TELEGRAM_BOT_TOKEN)
        self.token_edit.setPlaceholderText(t("placeholder_token"))

        self.chat_id_edit = LineEdit()
        self.chat_id_edit.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        self.chat_id_edit.setText(str(config.YOUR_CHAT_ID) if config.YOUR_CHAT_ID else "")
        self.chat_id_edit.setPlaceholderText(t("placeholder_chat_id"))
        detect_btn = PushButton("Detect from last message")
        detect_btn.setAutoDefault(False)
        detect_btn.setDefault(False)
        detect_btn.clicked.connect(self.on_detect_chat_id)
        chat_id_row = QHBoxLayout()
        chat_id_row.addWidget(self.chat_id_edit, 1)
        chat_id_row.addWidget(detect_btn)
        chat_id_row_widget = QWidget()
        chat_id_row_widget.setLayout(chat_id_row)

        self.deck_combo = EditableComboBox()
        self.notetype_combo = EditableComboBox()
        self._populate_anki_lists()

        self.auto_mode_switch = SwitchButton()
        self.auto_mode_switch.setChecked(config.AUTO_MODE)

        layout.addWidget(self._labeled_row(t("label_token"), self.token_edit))
        layout.addWidget(self._labeled_row(t("label_chat_id"), chat_id_row_widget))
        layout.addWidget(self._labeled_row(t("label_deck"), self.deck_combo))
        layout.addWidget(self._labeled_row(t("label_notetype"), self.notetype_combo))

        guide_row = CardWidget()
        guide_layout = QHBoxLayout(guide_row)
        guide_layout.setContentsMargins(16, 12, 16, 12)
        guide_layout.addWidget(BodyLabel("New here? The Guide tab explains how this all works."))
        guide_layout.addStretch(1)
        open_guide_btn = PushButton(FluentIcon.HELP, "Open Guide")
        open_guide_btn.setAutoDefault(False)
        open_guide_btn.setDefault(False)
        open_guide_btn.clicked.connect(self.on_open_guide)
        guide_layout.addWidget(open_guide_btn)
        layout.addWidget(guide_row)

        auto_row = CardWidget()
        auto_layout = QHBoxLayout(auto_row)
        auto_layout.setContentsMargins(16, 12, 16, 12)
        auto_text = QVBoxLayout()
        auto_text.addWidget(StrongBodyLabel(t("auto_mode_title")))
        auto_text.addWidget(CaptionLabel(t("auto_mode_desc")))
        auto_layout.addLayout(auto_text)
        auto_layout.addStretch(1)
        auto_layout.addWidget(self.auto_mode_switch)
        layout.addWidget(auto_row)

        layout.addStretch(1)

        save_btn = PrimaryPushButton(FluentIcon.SAVE, t("btn_save_settings"))
        save_btn.setAutoDefault(False)
        save_btn.setDefault(False)
        save_btn.clicked.connect(self.on_save)
        layout.addWidget(save_btn, 0, Qt.AlignmentFlag.AlignLeft)

    def _labeled_row(self, label: str, widget) -> CardWidget:
        card = CardWidget()
        h = QHBoxLayout(card)
        h.setContentsMargins(16, 10, 16, 10)
        lbl = BodyLabel(label)
        lbl.setFixedWidth(160)
        h.addWidget(lbl)
        h.addWidget(widget, 1)
        return card

    def _populate_anki_lists(self):
        try:
            decks = bridge.anki_request("deckNames")
            models = bridge.anki_request("modelNames")
        except Exception:
            decks, models = [], []

        if config.DEFAULT_DECK not in decks:
            decks = [config.DEFAULT_DECK] + decks
        if config.DEFAULT_NOTE_TYPE not in models:
            models = [config.DEFAULT_NOTE_TYPE] + models

        self.deck_combo.addItems(decks)
        self.deck_combo.setCurrentText(config.DEFAULT_DECK)
        self.notetype_combo.addItems(models)
        self.notetype_combo.setCurrentText(config.DEFAULT_NOTE_TYPE)

    def on_detect_chat_id(self):
        token = self.token_edit.text().strip() or config.TELEGRAM_BOT_TOKEN
        if not token:
            InfoBar.warning("Missing token", "Enter and save a bot token first.", position=InfoBarPosition.TOP, parent=self.window())
            return

        original_token = config.TELEGRAM_BOT_TOKEN
        config.TELEGRAM_BOT_TOKEN = token
        try:
            chat_id = bridge.get_latest_chat_id()
        except Exception as e:
            InfoBar.error("Error", f"Couldn't fetch messages: {e}", position=InfoBarPosition.TOP, parent=self.window())
            return
        finally:
            config.TELEGRAM_BOT_TOKEN = original_token

        if chat_id is None:
            InfoBar.warning("No messages yet", "Send any message to your bot on Telegram first, then try again.", position=InfoBarPosition.TOP, parent=self.window())
            return

        self.chat_id_edit.setText(str(chat_id))
        InfoBar.success("Detected", f"Chat ID {chat_id} filled in - click Save Settings to keep it.", position=InfoBarPosition.TOP, parent=self.window())

    def on_open_guide(self):
        self.window().switchTo(self.window().guide_interface)

    def on_save(self):
        config.save_setting("TELEGRAM_BOT_TOKEN", self.token_edit.text().strip())

        chat_id_text = self.chat_id_edit.text().strip()
        config.save_setting("YOUR_CHAT_ID", chat_id_text)

        config.save_setting("DEFAULT_DECK", self.deck_combo.currentText().strip() or "Default")
        config.save_setting("DEFAULT_NOTE_TYPE", self.notetype_combo.currentText().strip() or "Basic")
        config.save_setting("AUTO_MODE", self.auto_mode_switch.isChecked())

        InfoBar.success(t("settings_saved_title"), t("settings_saved_body"), position=InfoBarPosition.TOP, parent=self.window())


CONTACT_LINKS = [
    (FluentIcon.GLOBE, "Portfolio", "ahmed-atef-tech.github.io", "https://ahmed-atef-tech.github.io"),
    (FluentIcon.MAIL, "Email", "ahmed.atef.tech@gmail.com", "mailto:ahmed.atef.tech@gmail.com"),
    (FluentIcon.GITHUB, "GitHub", "Ahmed-Atef-Tech", "https://github.com/Ahmed-Atef-Tech"),
    (FluentIcon.PEOPLE, "LinkedIn", "Ahmed Atef", "https://www.linkedin.com/in/ahmed-atef-8a73a8263/"),
    (FluentIcon.SEND, "WhatsApp", "+20 101 987 6314", "https://wa.me/201019876314"),
    (FluentIcon.CHAT, "YouTube", "AhmedAtef-Tech", "https://www.youtube.com/@AhmedAtef-Tech/videos"),
]


class AboutInterface(QWidget):
    """شاشة عن البرنامج - معلومات المطور وطرق التواصل."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("AboutInterface")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 20, 30, 20)
        layout.setSpacing(6)

        layout.addWidget(TitleLabel("About"))
        layout.addWidget(CaptionLabel(f"Telegram → Anki Bridge v{updater.APP_VERSION} - built by Ahmed Atef"))
        layout.addSpacing(6)

        self.update_row = CardWidget()
        self.update_row.hide()
        update_layout = QHBoxLayout(self.update_row)
        update_layout.setContentsMargins(16, 10, 16, 10)
        self.update_label = StrongBodyLabel("")
        update_layout.addWidget(self.update_label)
        update_layout.addStretch(1)
        self.update_btn = HyperlinkButton("", "Download", icon=FluentIcon.DOWNLOAD)
        update_layout.addWidget(self.update_btn)
        layout.addWidget(self.update_row)
        layout.addSpacing(8)

        for icon, label, value, url in CONTACT_LINKS:
            layout.addWidget(self._contact_row(icon, label, value, url))

        layout.addStretch(1)

    def show_update_link(self, version: str, url: str) -> None:
        self.update_label.setText(f"Version {version} is available")
        self.update_btn.setUrl(url)
        self.update_row.show()

    def _contact_row(self, icon, label: str, value: str, url: str) -> CardWidget:
        card = CardWidget()
        h = QHBoxLayout(card)
        h.setContentsMargins(16, 10, 16, 10)

        text_col = QVBoxLayout()
        text_col.addWidget(StrongBodyLabel(label))
        text_col.addWidget(CaptionLabel(value))
        h.addLayout(text_col)
        h.addStretch(1)
        h.addWidget(HyperlinkButton(url, "Open", icon=icon))
        return card


class GuideInterface(QWidget):
    """شرح المشكلة اللي البرنامج بيحلها، خطوات الاستخدام، وبرومبتات جاهزة لأي AI."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("GuideInterface")

        outer = QVBoxLayout(self)
        outer.setContentsMargins(30, 20, 30, 20)
        outer.setSpacing(12)
        outer.addWidget(TitleLabel("Guide"))

        scroll = ScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setSpacing(10)

        for heading, body in GUIDE_SECTIONS:
            layout.addWidget(self._section_card(heading, body))

        layout.addWidget(SubtitleLabel("Copy a prompt for AI card generation"))
        layout.addWidget(
            CaptionLabel(
                "Paste your study material into ChatGPT/Claude/Gemini after one of these "
                "prompts, then paste the AI's output straight into your Telegram bot."
            )
        )
        for name, desc, prompt_text in PROMPTS:
            layout.addWidget(self._prompt_card(name, desc, prompt_text))

        layout.addStretch(1)
        scroll.setWidget(content)
        outer.addWidget(scroll, 1)

    def _section_card(self, heading: str, body: str) -> CardWidget:
        card = CardWidget()
        v = QVBoxLayout(card)
        v.setContentsMargins(16, 12, 16, 12)
        v.setSpacing(4)
        v.addWidget(StrongBodyLabel(heading))
        body_label = BodyLabel(body)
        body_label.setWordWrap(True)
        v.addWidget(body_label)
        return card

    def _prompt_card(self, name: str, desc: str, prompt_text: str) -> CardWidget:
        card = CardWidget()
        h = QHBoxLayout(card)
        h.setContentsMargins(16, 10, 16, 10)

        text_col = QVBoxLayout()
        text_col.addWidget(StrongBodyLabel(name))
        caption = CaptionLabel(desc)
        caption.setWordWrap(True)
        text_col.addWidget(caption)
        h.addLayout(text_col, 1)

        copy_btn = PrimaryPushButton(FluentIcon.COPY, "Copy Prompt")
        copy_btn.clicked.connect(lambda checked=False, text=prompt_text, n=name: self._copy_prompt(text, n))
        h.addWidget(copy_btn)
        return card

    def _copy_prompt(self, prompt_text: str, name: str) -> None:
        QApplication.clipboard().setText(prompt_text)
        InfoBar.success("Copied", f"{name} prompt copied to clipboard.", position=InfoBarPosition.TOP, parent=self.window())


class WelcomeDialog(MessageBoxBase):
    """نافذة ترحيبية بتظهر أول مرة بس - بتشرح المشكلة والاستخدام."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.titleLabel = SubtitleLabel("Welcome to Telegram → Anki Bridge", self)
        self.contentEdit = TextEdit(self)
        self.contentEdit.setPlainText(WELCOME_TEXT)
        self.contentEdit.setReadOnly(True)
        self.contentEdit.setMinimumSize(560, 420)

        self.viewLayout.addWidget(self.titleLabel)
        self.viewLayout.addWidget(self.contentEdit)

        self.yesButton.setText("Got it")
        self.cancelButton.hide()
        self.widget.setMinimumWidth(600)


class MainWindow(FluentWindow):
    def __init__(self, items=None, new_offset=0, start_on_settings=False):
        super().__init__()
        self.setWindowTitle(t("window_title"))
        self.resize(760, 580)

        icon_path = config.BASE_DIR / "icons8-anki-480.ico"
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))

        self.settings_interface = SettingsInterface(self)
        self.about_interface = AboutInterface(self)
        self.guide_interface = GuideInterface(self)

        if items:
            self.review_interface = ReviewInterface(items, new_offset, self)
            self.addSubInterface(self.review_interface, FluentIcon.SYNC, t("nav_review"))
        else:
            self.review_interface = None

        self.addSubInterface(self.guide_interface, FluentIcon.BOOK_SHELF, "Guide")
        self.addSubInterface(self.settings_interface, FluentIcon.SETTING, t("nav_settings"), NavigationItemPosition.BOTTOM)
        self.addSubInterface(self.about_interface, FluentIcon.INFO, "About", NavigationItemPosition.BOTTOM)

        if start_on_settings or not items:
            self.switchTo(self.settings_interface)

        self._setup_tray()

    def maybe_show_welcome(self) -> None:
        """لازم تتنادى بعد ما الشباك يتعرض (show())، عشان الـ overlay dialog يظهر صح فوقه."""
        if config.FIRST_RUN_DONE:
            return
        config.save_setting("FIRST_RUN_DONE", True)
        WelcomeDialog(self).exec()

    def check_for_update(self) -> None:
        self._update_worker = UpdateCheckWorker()
        self._update_worker.result_ready.connect(self._on_update_check_result)
        self._update_worker.start()

    def _on_update_check_result(self, result) -> None:
        if not result:
            return
        self._update_url = result["download_url"] or result["url"]
        version = result["version"]

        self.tray_icon.messageClicked.connect(self._open_update_url)
        self.tray_icon.showMessage(
            "Update available",
            f"Telegram → Anki Bridge {version} is available - click to download.",
            QSystemTrayIcon.MessageIcon.Information,
            8000,
        )
        InfoBar.success(
            "Update available",
            f"Version {version} is out - see the About tab to download it.",
            position=InfoBarPosition.TOP,
            duration=8000,
            parent=self,
        )
        if hasattr(self, "about_interface"):
            self.about_interface.show_update_link(version, self._update_url)

    def _open_update_url(self) -> None:
        if getattr(self, "_update_url", None):
            QDesktopServices.openUrl(QUrl(self._update_url))

    def _setup_tray(self) -> None:
        self.tray_icon = QSystemTrayIcon(self.windowIcon(), self)
        self.tray_icon.setToolTip(t("window_title"))

        menu = QMenu()
        open_action = menu.addAction("Open")
        open_action.triggered.connect(self._show_from_tray)
        exit_action = menu.addAction("Exit")
        exit_action.triggered.connect(self._quit_from_tray)
        self.tray_icon.setContextMenu(menu)

        self.tray_icon.activated.connect(self._on_tray_activated)
        self.tray_icon.show()

    def _on_tray_activated(self, reason) -> None:
        if reason in (QSystemTrayIcon.ActivationReason.Trigger, QSystemTrayIcon.ActivationReason.DoubleClick):
            self._show_from_tray()

    def _show_from_tray(self) -> None:
        self.show()
        self.setWindowState(self.windowState() & ~Qt.WindowState.WindowMinimized)
        self.raise_()
        self.activateWindow()

    def _quit_from_tray(self) -> None:
        self.tray_icon.hide()
        QApplication.instance().quit()

    def closeEvent(self, event) -> None:
        event.ignore()
        self.hide()
        self.tray_icon.showMessage(
            t("window_title"),
            "Still running in the tray. Right-click the tray icon to exit.",
            QSystemTrayIcon.MessageIcon.Information,
            3000,
        )


def main() -> None:
    bridge.setup_logging()
    bridge.log.info("=" * 50)
    bridge.log.info("🖥️  بدء تشغيل Telegram → Anki Bridge (GUI)")

    is_startup_launch = "--startup" in sys.argv
    if is_startup_launch:
        bridge.log.info(f"⏳ استنى {config.STARTUP_DELAY_SEC} ثانية بعد تسجيل الدخول...")
        import time

        time.sleep(config.STARTUP_DELAY_SEC)

    force_settings = "--settings" in sys.argv

    items, new_offset = [], bridge.get_last_offset()

    if not force_settings and config.TELEGRAM_BOT_TOKEN:
        if bridge.ensure_anki_running():
            try:
                items, new_offset = bridge.fetch_pending_items(bridge.get_last_offset())
            except Exception as e:
                bridge.log.error(f"❌ فشل جلب رسايل تيليجرام: {e}")
        else:
            bridge.log.error("❌ مش هينفع نكمل من غير Anki + AnkiConnect.")

    if items and config.AUTO_MODE:
        bridge.log.info(f"🤖 Auto Mode مفعّل - بيحفظ {len(items)} رسالة من غير مراجعة.")
        bridge.commit_items(items)
        bridge.save_offset(new_offset)
        return

    if not items and not force_settings:
        bridge.save_offset(new_offset)
        if is_startup_launch:
            bridge.log.info("لا يوجد رسايل جديدة فيها كروت - مفيش داعي نفتح الواجهة.")
            return
        # تشغيل يدوي (دبل كليك أو من غير أي فلاج) - افتح شاشة الإعدادات بدل ما تقفل من غير ما تعمل حاجة.
        bridge.log.info("لا يوجد رسايل جديدة - هنفتح شاشة الإعدادات بدل ما نقفل بصمت.")
        force_settings = True

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)  # يفضل شغال في الـ tray لما تقفل الواجهة، بدل ما يخرج خالص
    setTheme(Theme.AUTO)
    window = MainWindow(items=items, new_offset=new_offset, start_on_settings=force_settings)
    window.show()
    QTimer.singleShot(0, window.maybe_show_welcome)
    QTimer.singleShot(500, window.check_for_update)
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
