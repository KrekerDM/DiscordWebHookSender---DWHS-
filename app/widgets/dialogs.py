import time

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QListWidget, QListWidgetItem, QWidget, QMessageBox
)

from app import storage
from app.discord_api import parse_webhook_url, DiscordAPIError
from app.i18n import tr
from app.models import WebhookProfile, HistoryEntry


class WebhookDialog(QDialog):
    def __init__(self, profile: WebhookProfile | None = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr("dlg.webhook.title_edit") if profile else tr("dlg.webhook.title_new"))
        self.setMinimumWidth(420)
        self._editing = profile is not None
        self.profile = profile or WebhookProfile()

        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        layout.addWidget(self._label(tr("dlg.webhook.name_label")))
        self.name_edit = QLineEdit(self.profile.name)
        self.name_edit.setPlaceholderText(tr("dlg.webhook.name_placeholder"))
        layout.addWidget(self.name_edit)

        layout.addWidget(self._label(tr("dlg.webhook.url_label")))
        self.url_edit = QLineEdit(self.profile.url)
        self.url_edit.setPlaceholderText("https://discord.com/api/webhooks/…/…")
        layout.addWidget(self.url_edit)

        self.error_label = QLabel("")
        self.error_label.setStyleSheet("color: #f23f43; font-size: 12px;")
        self.error_label.setWordWrap(True)
        self.error_label.setVisible(False)
        layout.addWidget(self.error_label)

        layout.addWidget(self._label(tr("dlg.webhook.default_username_label")))
        self.default_username = QLineEdit(self.profile.default_username)
        layout.addWidget(self.default_username)

        layout.addWidget(self._label(tr("dlg.webhook.default_avatar_label")))
        self.default_avatar = QLineEdit(self.profile.default_avatar)
        layout.addWidget(self.default_avatar)

        btn_row = QHBoxLayout()
        btn_row.addStretch(1)
        cancel_btn = QPushButton(tr("dlg.cancel"))
        cancel_btn.setProperty("class", "ghost")
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(cancel_btn)
        save_btn = QPushButton(tr("dlg.save"))
        save_btn.setProperty("class", "primary")
        save_btn.clicked.connect(self._on_save)
        btn_row.addWidget(save_btn)
        layout.addLayout(btn_row)

    @staticmethod
    def _label(text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setProperty("class", "field-label")
        return lbl

    def _on_save(self) -> None:
        url = self.url_edit.text().strip()
        try:
            parse_webhook_url(url)
        except DiscordAPIError as e:
            self.error_label.setText(e.message)
            self.error_label.setVisible(True)
            return
        self.profile.name = self.name_edit.text().strip() or tr("dlg.webhook.default_name")
        self.profile.url = url
        self.profile.default_username = self.default_username.text().strip()
        self.profile.default_avatar = self.default_avatar.text().strip()
        self.accept()


class TemplatesDialog(QDialog):
    def __init__(self, current_state_provider, on_load, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr("dlg.templates.title"))
        self.setMinimumSize(420, 420)
        self._current_state_provider = current_state_provider
        self._on_load = on_load

        layout = QVBoxLayout(self)

        save_row = QHBoxLayout()
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText(tr("dlg.templates.name_placeholder"))
        save_row.addWidget(self.name_input, 1)
        save_btn = QPushButton(tr("dlg.templates.save_current"))
        save_btn.setProperty("class", "primary")
        save_btn.clicked.connect(self._save_current)
        save_row.addWidget(save_btn)
        layout.addLayout(save_row)

        self.list_widget = QListWidget()
        layout.addWidget(self.list_widget, 1)

        close_row = QHBoxLayout()
        close_row.addStretch(1)
        close_btn = QPushButton(tr("dlg.close"))
        close_btn.setProperty("class", "ghost")
        close_btn.clicked.connect(self.accept)
        close_row.addWidget(close_btn)
        layout.addLayout(close_row)

        self._reload()

    def _reload(self) -> None:
        self.list_widget.clear()
        names = storage.list_templates()
        if not names:
            item = QListWidgetItem(tr("dlg.templates.empty"))
            item.setFlags(Qt.NoItemFlags)
            self.list_widget.addItem(item)
            return
        for name in names:
            item = QListWidgetItem()
            self.list_widget.addItem(item)
            row = self._build_row(name)
            item.setSizeHint(row.sizeHint())
            self.list_widget.setItemWidget(item, row)

    def _build_row(self, name: str) -> QWidget:
        row = QWidget()
        h = QHBoxLayout(row)
        h.setContentsMargins(8, 6, 8, 6)
        label = QLabel(name)
        label.setTextFormat(Qt.PlainText)
        label.setStyleSheet("font-weight: 600;")
        h.addWidget(label, 1)
        load_btn = QPushButton(tr("dlg.templates.load"))
        load_btn.setProperty("class", "ghost")
        load_btn.clicked.connect(lambda: self._load(name))
        h.addWidget(load_btn)
        del_btn = QPushButton("✕")
        del_btn.setProperty("class", "icon")
        del_btn.setFixedSize(28, 28)
        del_btn.clicked.connect(lambda: self._delete(name))
        h.addWidget(del_btn)
        return row

    def _save_current(self) -> None:
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, tr("dlg.templates.name_required.title"), tr("dlg.templates.name_required.text"))
            return
        storage.save_template(name, self._current_state_provider())
        self.name_input.clear()
        self._reload()

    def _load(self, name: str) -> None:
        state = storage.load_template(name)
        if state:
            self._on_load(state)
            self.accept()

    def _delete(self, name: str) -> None:
        if QMessageBox.question(
            self, tr("dlg.templates.confirm_delete.title"), tr("dlg.templates.confirm_delete.text", name=name)
        ) == QMessageBox.Yes:
            storage.delete_template(name)
            self._reload()


class HistoryDialog(QDialog):
    def __init__(self, entries: list[HistoryEntry], on_edit, on_delete, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr("dlg.history.title"))
        self.setMinimumSize(460, 460)
        self._on_edit = on_edit
        self._on_delete = on_delete
        self.entries = entries

        layout = QVBoxLayout(self)
        self.list_widget = QListWidget()
        layout.addWidget(self.list_widget, 1)

        close_row = QHBoxLayout()
        close_row.addStretch(1)
        close_btn = QPushButton(tr("dlg.close"))
        close_btn.setProperty("class", "ghost")
        close_btn.clicked.connect(self.accept)
        close_row.addWidget(close_btn)
        layout.addLayout(close_row)

        self._reload()

    def _reload(self) -> None:
        self.list_widget.clear()
        if not self.entries:
            item = QListWidgetItem(tr("dlg.history.empty"))
            item.setFlags(Qt.NoItemFlags)
            self.list_widget.addItem(item)
            return
        for entry in reversed(self.entries):
            item = QListWidgetItem()
            self.list_widget.addItem(item)
            row = self._build_row(entry)
            item.setSizeHint(row.sizeHint())
            self.list_widget.setItemWidget(item, row)

    def _build_row(self, entry: HistoryEntry) -> QWidget:
        row = QWidget()
        v = QVBoxLayout(row)
        v.setContentsMargins(8, 6, 8, 6)
        v.setSpacing(2)

        top = QHBoxLayout()
        when = time.strftime("%d.%m.%Y %H:%M", time.localtime(entry.sent_at))
        label = QLabel(entry.summary or tr("dlg.history.no_text"))
        label.setTextFormat(Qt.PlainText)
        label.setStyleSheet("font-weight: 600;")
        top.addWidget(label, 1)
        v.addLayout(top)

        sub = QLabel(f"{when}  ·  ID {entry.message_id}")
        sub.setProperty("class", "hint")
        v.addWidget(sub)

        btn_row = QHBoxLayout()
        btn_row.addStretch(1)
        edit_btn = QPushButton(tr("dlg.history.edit"))
        edit_btn.setProperty("class", "ghost")
        edit_btn.clicked.connect(lambda: self._edit(entry))
        btn_row.addWidget(edit_btn)
        del_btn = QPushButton(tr("dlg.history.delete"))
        del_btn.setProperty("class", "danger")
        del_btn.clicked.connect(lambda: self._delete(entry))
        btn_row.addWidget(del_btn)
        v.addLayout(btn_row)
        return row

    def _edit(self, entry: HistoryEntry) -> None:
        self._on_edit(entry)
        self.accept()

    def _delete(self, entry: HistoryEntry) -> None:
        if QMessageBox.question(
            self, tr("dlg.history.confirm_delete.title"), tr("dlg.history.confirm_delete.text")
        ) == QMessageBox.Yes:
            def on_done():
                if entry in self.entries:
                    self.entries.remove(entry)
                self._reload()
            self._on_delete(entry, on_done)
