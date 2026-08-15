from __future__ import annotations

import os

from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QGuiApplication, QIcon, QPixmap, QPainter, QColor, QFont
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QFrame, QLabel, QLineEdit,
    QPlainTextEdit, QPushButton, QCheckBox, QSplitter, QStackedWidget, QScrollArea,
    QFileDialog, QMessageBox, QMenu
)

from app import storage
from app.config import (
    APP_NAME, MAX_CONTENT_LEN, MAX_USERNAME_LEN, MAX_EMBEDS, MAX_FILES, MAX_FILE_SIZE,
)
from app.discord_api import ApiWorker, send_message, edit_message, delete_message, get_webhook_info
from app import i18n
from app.i18n import tr
from app.models import MessageState, WebhookProfile, Embed, HistoryEntry
from app.theme import Colors
from app.utils import truncate, bytes_human, is_valid_url
from app.widgets.sidebar import Sidebar
from app.widgets.preview import PreviewPanel
from app.widgets.embed_editor import EmbedEditor
from app.widgets.toast import Toast
from app.widgets.dialogs import WebhookDialog, TemplatesDialog, HistoryDialog


def _section_label(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setProperty("class", "field-label")
    lbl.setWordWrap(True)
    return lbl


def _hint(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setProperty("class", "hint")
    lbl.setWordWrap(True)
    return lbl


def step_icon(number: int, active: bool, size: int = 28) -> QIcon:
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setPen(Qt.NoPen)
    painter.setBrush(QColor(Colors.PRIMARY_CONTAINER if active else Colors.SURFACE_CONTAINER_HIGHEST))
    painter.drawEllipse(0, 0, size, size)
    painter.setPen(QColor("white" if active else Colors.ON_SURFACE_VARIANT))
    font = QFont("Inter", int(size * 0.42), QFont.Bold)
    painter.setFont(font)
    painter.drawText(pixmap.rect(), Qt.AlignCenter, str(number))
    painter.end()
    return QIcon(pixmap)


def kebab_icon(size: int = 20, color: str = Colors.ON_SURFACE_VARIANT) -> QIcon:
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setPen(Qt.NoPen)
    painter.setBrush(QColor(color))
    dot = max(2, round(size * 0.14))
    cx = size / 2
    for cy in (size * 0.22, size * 0.5, size * 0.78):
        painter.drawEllipse(int(cx - dot / 2), int(cy - dot / 2), dot, dot)
    painter.end()
    return QIcon(pixmap)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_NAME)
        self.resize(1440, 900)
        self.setMinimumSize(1100, 680)

        self.profiles: list[WebhookProfile] = storage.load_profiles()
        self.history: list[HistoryEntry] = storage.load_history()
        self.settings: dict = storage.load_settings()
        self.active_profile_id: str | None = self.settings.get("active_profile_id")
        if self.active_profile_id not in {p.id for p in self.profiles}:
            self.active_profile_id = self.profiles[0].id if self.profiles else None

        self.state = MessageState()
        self.editing_message_id: str | None = None
        self._workers: list = []

        self._build_ui()
        self._refresh_sidebar()
        self._refresh_topbar()
        self._sync_preview()

    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self.sidebar = Sidebar()
        self.sidebar.addRequested.connect(self._on_add_profile)
        self.sidebar.profileSelected.connect(self._on_select_profile)
        self.sidebar.renameRequested.connect(self._on_edit_profile)
        self.sidebar.duplicateRequested.connect(self._on_duplicate_profile)
        self.sidebar.deleteRequested.connect(self._on_delete_profile)
        self.sidebar.languageSelected.connect(self._on_language_selected)
        root.addWidget(self.sidebar)

        main_col = QWidget()
        main_layout = QVBoxLayout(main_col)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        root.addWidget(main_col, 1)

        main_layout.addWidget(self._build_topbar())
        self.toast = Toast(main_col)
        main_layout.addWidget(self.toast)

        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(1)
        splitter.setChildrenCollapsible(False)

        splitter.addWidget(self._build_nav_panel())
        splitter.addWidget(self._build_editor_stack())
        self.preview_panel = PreviewPanel()
        self.preview_panel.setMinimumWidth(360)
        splitter.addWidget(self.preview_panel)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setStretchFactor(2, 0)
        splitter.setSizes([168, 640, 480])
        main_layout.addWidget(splitter, 1)

        main_layout.addWidget(self._build_statusbar())

    def _build_topbar(self) -> QFrame:
        bar = QFrame()
        bar.setProperty("class", "topbar")
        bar.setFixedHeight(64)
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(20, 8, 16, 8)
        layout.setSpacing(14)

        info_col = QVBoxLayout()
        info_col.setSpacing(2)
        self.profile_name_lbl = QLabel(tr("topbar.no_webhook"))
        self.profile_name_lbl.setTextFormat(Qt.PlainText)
        self.profile_name_lbl.setStyleSheet("font-size: 15px; font-weight: 700;")
        info_col.addWidget(self.profile_name_lbl)

        url_row = QHBoxLayout()
        url_row.setSpacing(6)
        self.profile_url_lbl = QLabel(tr("topbar.add_webhook_hint"))
        self.profile_url_lbl.setProperty("class", "hint")
        url_row.addWidget(self.profile_url_lbl)
        self._url_revealed = False
        self.reveal_btn = QPushButton("👁")
        self.reveal_btn.setProperty("class", "icon")
        self.reveal_btn.setFixedSize(22, 22)
        self.reveal_btn.setToolTip(tr("topbar.reveal_tooltip"))
        self.reveal_btn.clicked.connect(self._toggle_url_reveal)
        url_row.addWidget(self.reveal_btn)
        self.copy_url_btn = QPushButton(tr("topbar.copy"))
        self.copy_url_btn.setProperty("class", "ghost")
        self.copy_url_btn.clicked.connect(self._copy_url)
        url_row.addWidget(self.copy_url_btn)
        url_row.addStretch(1)
        info_col.addLayout(url_row)
        layout.addLayout(info_col, 1)

        self.editing_banner = QLabel("")
        self.editing_banner.setStyleSheet("color: #f0b232; font-weight: 600; font-size: 12px;")
        self.editing_banner.setVisible(False)
        layout.addWidget(self.editing_banner)

        more_btn = QPushButton()
        more_btn.setIcon(kebab_icon())
        more_btn.setIconSize(QSize(20, 20))
        more_btn.setFixedSize(36, 36)
        more_btn.setCursor(Qt.PointingHandCursor)
        more_btn.setToolTip(tr("topbar.more_tooltip"))
        more_btn.setStyleSheet(
            f"QPushButton {{ background-color: {Colors.SURFACE_CONTAINER_HIGH}; border-radius: 18px; }}"
            f"QPushButton:hover {{ background-color: {Colors.SURFACE_BRIGHT}; }}"
        )
        more_btn.clicked.connect(self._open_more_menu)
        layout.addWidget(more_btn)

        self.send_btn = QPushButton(tr("topbar.send"))
        self.send_btn.setProperty("class", "primary")
        self.send_btn.setCursor(Qt.PointingHandCursor)
        self.send_btn.setMinimumWidth(130)
        self.send_btn.clicked.connect(self._on_send)
        layout.addWidget(self.send_btn)

        return bar

    def _open_more_menu(self) -> None:
        menu = QMenu(self)
        test_action = menu.addAction(tr("menu.test_connection"))
        history_action = menu.addAction(tr("menu.history"))
        templates_action = menu.addAction(tr("menu.templates"))
        menu.addSeparator()
        clear_action = menu.addAction(tr("menu.clear"))
        chosen = menu.exec(self.sender().mapToGlobal(self.sender().rect().bottomRight()))
        if chosen == test_action:
            self._on_test_connection()
        elif chosen == history_action:
            self._open_history()
        elif chosen == templates_action:
            self._open_templates()
        elif chosen == clear_action:
            self._on_clear()

    def _build_nav_panel(self) -> QFrame:
        panel = QFrame()
        panel.setProperty("class", "navpanel")
        panel.setFixedWidth(216)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(12, 20, 12, 12)
        layout.setSpacing(6)

        self.nav_buttons: dict[int, QPushButton] = {}
        self.nav_labels = [tr("nav.message"), tr("nav.embeds"), tr("nav.files"), tr("nav.json")]
        for i, label in enumerate(self.nav_labels):
            btn = QPushButton(f"  {label}")
            btn.setProperty("class", "navitem")
            btn.setCursor(Qt.PointingHandCursor)
            btn.setFixedHeight(48)
            btn.setIconSize(QSize(28, 28))
            btn.setIcon(step_icon(i + 1, active=(i == 0)))
            btn.clicked.connect(lambda checked=False, idx=i: self._switch_page(idx))
            layout.addWidget(btn)
            self.nav_buttons[i] = btn
        layout.addStretch(1)
        return panel

    def _build_editor_stack(self) -> QStackedWidget:
        self.stack = QStackedWidget()
        self.stack.addWidget(self._build_message_page())
        self.stack.addWidget(self._build_embeds_page())
        self.stack.addWidget(self._build_files_page())
        self.stack.addWidget(self._build_json_page())
        self._switch_page(0)
        return self.stack

    def _wrap_scroll(self, inner: QWidget) -> QScrollArea:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setWidget(inner)
        return scroll

    def _build_message_page(self) -> QScrollArea:
        page = QWidget()
        v = QVBoxLayout(page)
        v.setContentsMargins(24, 20, 24, 24)
        v.setSpacing(16)

        head = QHBoxLayout()
        head.addWidget(_section_label(tr("msg.content_title")))
        head.addStretch(1)
        self.content_counter = _hint(f"0/{MAX_CONTENT_LEN}")
        head.addWidget(self.content_counter)
        v.addLayout(head)

        self.content_edit = QPlainTextEdit(self.state.content)
        self.content_edit.setPlaceholderText(tr("msg.content_placeholder"))
        self.content_edit.setFixedHeight(140)
        self.content_edit.textChanged.connect(self._on_content_changed)
        v.addWidget(self.content_edit)

        grid_row = QHBoxLayout()
        grid_row.setSpacing(16)

        col1 = QVBoxLayout()
        col1.addWidget(_section_label(tr("msg.username_label")))
        self.username_edit = QLineEdit(self.state.username)
        self.username_edit.setMaxLength(MAX_USERNAME_LEN)
        self.username_edit.setPlaceholderText(tr("msg.username_placeholder"))
        self.username_edit.textChanged.connect(self._on_field_changed)
        col1.addWidget(self.username_edit)
        grid_row.addLayout(col1, 1)

        col2 = QVBoxLayout()
        col2.addWidget(_section_label(tr("msg.avatar_label")))
        self.avatar_edit = QLineEdit(self.state.avatar_url)
        self.avatar_edit.setPlaceholderText(tr("msg.avatar_placeholder"))
        self.avatar_edit.textChanged.connect(self._on_field_changed)
        col2.addWidget(self.avatar_edit)
        grid_row.addLayout(col2, 1)
        v.addLayout(grid_row)

        v.addWidget(_section_label(tr("msg.thread_label")))
        self.thread_name_edit = QLineEdit(self.state.thread_name)
        self.thread_name_edit.setPlaceholderText(tr("msg.thread_placeholder"))
        self.thread_name_edit.textChanged.connect(self._on_field_changed)
        v.addWidget(self.thread_name_edit)

        self.tts_check = QCheckBox(tr("msg.tts"))
        self.tts_check.toggled.connect(self._on_field_changed)
        v.addWidget(self.tts_check)

        v.addStretch(1)
        return self._wrap_scroll(page)

    def _build_embeds_page(self) -> QScrollArea:
        page = QWidget()
        self.embeds_page_layout = QVBoxLayout(page)
        self.embeds_page_layout.setContentsMargins(24, 20, 24, 24)
        self.embeds_page_layout.setSpacing(12)

        head = QHBoxLayout()
        self.embeds_head_label = QLabel(tr("embeds.header", n=0, max=MAX_EMBEDS))
        self.embeds_head_label.setProperty("class", "section-title")
        head.addWidget(self.embeds_head_label)
        head.addStretch(1)
        add_embed_btn = QPushButton(tr("embeds.add"))
        add_embed_btn.setProperty("class", "primary")
        add_embed_btn.setCursor(Qt.PointingHandCursor)
        add_embed_btn.clicked.connect(self._add_embed)
        self.add_embed_btn = add_embed_btn
        head.addWidget(add_embed_btn)
        self.embeds_page_layout.addLayout(head)

        self.embeds_empty_hint = _hint(tr("embeds.empty_hint"))
        self.embeds_page_layout.addWidget(self.embeds_empty_hint)

        self.embeds_container = QVBoxLayout()
        self.embeds_container.setSpacing(12)
        self.embeds_page_layout.addLayout(self.embeds_container)
        self.embeds_page_layout.addStretch(1)

        self.embed_editors: list[EmbedEditor] = []
        return self._wrap_scroll(page)

    def _build_files_page(self) -> QScrollArea:
        page = QWidget()
        v = QVBoxLayout(page)
        v.setContentsMargins(24, 20, 24, 24)
        v.setSpacing(12)

        head = QHBoxLayout()
        head.addWidget(_section_label(tr("files.title")))
        head.addStretch(1)
        browse_btn = QPushButton(tr("files.browse"))
        browse_btn.setProperty("class", "primary")
        browse_btn.setCursor(Qt.PointingHandCursor)
        browse_btn.clicked.connect(self._on_attach_files)
        head.addWidget(browse_btn)
        v.addLayout(head)

        v.addWidget(_hint(tr("files.limit_hint", max_files=MAX_FILES, max_size=bytes_human(MAX_FILE_SIZE))))

        self.files_container = QVBoxLayout()
        self.files_container.setSpacing(6)
        v.addLayout(self.files_container)
        self.files_empty_hint = _hint(tr("files.empty"))
        v.addWidget(self.files_empty_hint)
        v.addStretch(1)
        return self._wrap_scroll(page)

    def _build_json_page(self) -> QScrollArea:
        page = QWidget()
        v = QVBoxLayout(page)
        v.setContentsMargins(24, 20, 24, 24)
        v.setSpacing(10)

        v.addWidget(_section_label(tr("json.import_title")))
        v.addWidget(_hint(tr("json.import_hint")))
        self.json_import_edit = QPlainTextEdit()
        self.json_import_edit.setPlaceholderText(tr("json.import_placeholder"))
        self.json_import_edit.setFixedHeight(160)
        v.addWidget(self.json_import_edit)

        apply_row = QHBoxLayout()
        apply_row.addStretch(1)
        apply_btn = QPushButton(tr("json.apply"))
        apply_btn.setProperty("class", "primary")
        apply_btn.clicked.connect(self._apply_json_import)
        apply_row.addWidget(apply_btn)
        v.addLayout(apply_row)

        sep = QFrame()
        sep.setProperty("class", "divider")
        v.addWidget(sep)

        export_head = QHBoxLayout()
        export_head.addWidget(_section_label(tr("json.export_title")))
        export_head.addStretch(1)
        copy_btn = QPushButton(tr("json.copy"))
        copy_btn.setProperty("class", "ghost")
        copy_btn.clicked.connect(self._copy_json)
        export_head.addWidget(copy_btn)
        v.addLayout(export_head)

        self.json_export_edit = QPlainTextEdit()
        self.json_export_edit.setReadOnly(True)
        self.json_export_edit.setMinimumHeight(220)
        v.addWidget(self.json_export_edit, 1)

        return self._wrap_scroll(page)

    def _build_statusbar(self) -> QFrame:
        bar = QFrame()
        bar.setProperty("class", "statusbar")
        bar.setFixedHeight(32)
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(20, 0, 20, 0)
        self.status_label = QLabel(tr("status.ready"))
        self.status_label.setProperty("class", "hint")
        layout.addWidget(self.status_label)
        layout.addStretch(1)
        return bar

    def _switch_page(self, index: int) -> None:
        self.stack.setCurrentIndex(index)
        for i, btn in self.nav_buttons.items():
            active = i == index
            btn.setProperty("class", "navitem-active" if active else "navitem")
            btn.setIcon(step_icon(i + 1, active=active))
            btn.style().unpolish(btn)
            btn.style().polish(btn)

    def _active_profile(self) -> WebhookProfile | None:
        for p in self.profiles:
            if p.id == self.active_profile_id:
                return p
        return None

    def _refresh_sidebar(self) -> None:
        self.sidebar.set_profiles(self.profiles, self.active_profile_id)

    def _refresh_topbar(self) -> None:
        profile = self._active_profile()
        if not profile:
            self.profile_name_lbl.setText(tr("topbar.no_webhook"))
            self.profile_url_lbl.setText(tr("topbar.add_webhook_hint"))
            self.send_btn.setEnabled(False)
            return
        self.send_btn.setEnabled(True)
        self.profile_name_lbl.setText(profile.name)
        self.profile_url_lbl.setText(self._masked_or_full(profile.url))

    def _masked_or_full(self, url: str) -> str:
        if self._url_revealed:
            return url
        tail = url.rstrip("/").split("/")[-1]
        if len(tail) > 8:
            tail = tail[:4] + "…" + tail[-3:]
        return f"…/webhooks/…/{tail}"

    def _toggle_url_reveal(self) -> None:
        self._url_revealed = not self._url_revealed
        self._refresh_topbar()

    def _copy_url(self) -> None:
        profile = self._active_profile()
        if not profile:
            return
        QGuiApplication.clipboard().setText(profile.url)
        self.toast.show_message(tr("toast.url_copied"), "success", 2000)

    def _on_add_profile(self) -> None:
        dialog = WebhookDialog(parent=self)
        if dialog.exec():
            self.profiles.append(dialog.profile)
            self.active_profile_id = dialog.profile.id
            storage.save_profiles(self.profiles)
            storage.save_settings({**self.settings, "active_profile_id": self.active_profile_id})
            self._refresh_sidebar()
            self._refresh_topbar()
            self.toast.show_message(tr("toast.webhook_added", name=dialog.profile.name), "success")

    def _on_select_profile(self, profile_id: str) -> None:
        self.active_profile_id = profile_id
        self.settings["active_profile_id"] = profile_id
        storage.save_settings(self.settings)
        profile = self._active_profile()
        if profile and not self.username_edit.text().strip() and profile.default_username:
            self.username_edit.setText(profile.default_username)
        if profile and not self.avatar_edit.text().strip() and profile.default_avatar:
            self.avatar_edit.setText(profile.default_avatar)
        self._url_revealed = False
        self._refresh_sidebar()
        self._refresh_topbar()
        self._sync_preview()

    def _on_edit_profile(self, profile_id: str) -> None:
        profile = next((p for p in self.profiles if p.id == profile_id), None)
        if not profile:
            return
        dialog = WebhookDialog(profile, parent=self)
        if dialog.exec():
            storage.save_profiles(self.profiles)
            self._refresh_sidebar()
            self._refresh_topbar()
            self.toast.show_message(tr("toast.webhook_updated"), "success", 2000)

    def _on_duplicate_profile(self, profile_id: str) -> None:
        profile = next((p for p in self.profiles if p.id == profile_id), None)
        if not profile:
            return
        clone = WebhookProfile(
            name=tr("profile.copy_suffix", name=profile.name), url=profile.url,
            default_username=profile.default_username, default_avatar=profile.default_avatar,
        )
        self.profiles.append(clone)
        storage.save_profiles(self.profiles)
        self._refresh_sidebar()
        self.toast.show_message(tr("toast.webhook_duplicated"), "success", 2000)

    def _on_delete_profile(self, profile_id: str) -> None:
        profile = next((p for p in self.profiles if p.id == profile_id), None)
        if not profile:
            return
        if QMessageBox.question(
            self, tr("confirm.delete_webhook.title"), tr("confirm.delete_webhook.text", name=profile.name)
        ) != QMessageBox.Yes:
            return
        self.profiles = [p for p in self.profiles if p.id != profile_id]
        self.history = [h for h in self.history if h.profile_id != profile_id]
        storage.save_profiles(self.profiles)
        storage.save_history(self.history)
        if self.active_profile_id == profile_id:
            self.active_profile_id = self.profiles[0].id if self.profiles else None
            self.settings["active_profile_id"] = self.active_profile_id
            storage.save_settings(self.settings)
        self._refresh_sidebar()
        self._refresh_topbar()
        self.toast.show_message(tr("toast.webhook_deleted"), "info", 2000)

    def _on_content_changed(self) -> None:
        text = self.content_edit.toPlainText()
        if len(text) > MAX_CONTENT_LEN:
            cursor = self.content_edit.textCursor()
            pos = cursor.position()
            self.content_edit.blockSignals(True)
            self.content_edit.setPlainText(text[:MAX_CONTENT_LEN])
            cursor.setPosition(min(pos, MAX_CONTENT_LEN))
            self.content_edit.setTextCursor(cursor)
            self.content_edit.blockSignals(False)
            text = self.content_edit.toPlainText()
        self.state.content = text
        n = len(text)
        self.content_counter.setText(f"{n}/{MAX_CONTENT_LEN}")
        self.content_counter.setProperty("class", "counter-danger" if n >= MAX_CONTENT_LEN else "counter")
        self.content_counter.style().unpolish(self.content_counter)
        self.content_counter.style().polish(self.content_counter)
        self._sync_preview()

    def _on_field_changed(self) -> None:
        self.state.username = self.username_edit.text()
        self.state.avatar_url = self.avatar_edit.text()
        self.state.thread_name = self.thread_name_edit.text()
        self.state.tts = self.tts_check.isChecked()
        self.avatar_edit.setProperty("error", not is_valid_url(self.avatar_edit.text()))
        self.avatar_edit.style().unpolish(self.avatar_edit)
        self.avatar_edit.style().polish(self.avatar_edit)
        self._sync_preview()

    def _add_embed(self) -> None:
        if len(self.state.embeds) >= MAX_EMBEDS:
            self.toast.show_message(tr("embeds.max_reached", max=MAX_EMBEDS), "warning")
            return
        embed = Embed()
        self.state.embeds.append(embed)
        self._add_embed_editor(embed)
        self._refresh_embeds_header()
        self._sync_preview()

    def _add_embed_editor(self, embed: Embed) -> None:
        editor = EmbedEditor(embed, len(self.embed_editors))
        editor.changed.connect(self._sync_preview)
        editor.removeRequested.connect(self._remove_embed)
        editor.duplicateRequested.connect(self._duplicate_embed)
        editor.moveUpRequested.connect(lambda e: self._move_embed(e, -1))
        editor.moveDownRequested.connect(lambda e: self._move_embed(e, 1))
        self.embed_editors.append(editor)
        self.embeds_container.addWidget(editor)

    def _remove_embed(self, editor: EmbedEditor) -> None:
        idx = self.embed_editors.index(editor)
        self.embed_editors.pop(idx)
        self.state.embeds.pop(idx)
        self.embeds_container.removeWidget(editor)
        editor.deleteLater()
        self._reindex_embeds()
        self._refresh_embeds_header()
        self._sync_preview()

    def _duplicate_embed(self, editor: EmbedEditor) -> None:
        if len(self.state.embeds) >= MAX_EMBEDS:
            self.toast.show_message(tr("embeds.max_reached", max=MAX_EMBEDS), "warning")
            return
        idx = self.embed_editors.index(editor)
        clone = Embed.from_dict(editor.embed.to_dict())
        self.state.embeds.insert(idx + 1, clone)
        new_editor = EmbedEditor(clone, idx + 1)
        new_editor.changed.connect(self._sync_preview)
        new_editor.removeRequested.connect(self._remove_embed)
        new_editor.duplicateRequested.connect(self._duplicate_embed)
        new_editor.moveUpRequested.connect(lambda e: self._move_embed(e, -1))
        new_editor.moveDownRequested.connect(lambda e: self._move_embed(e, 1))
        self.embed_editors.insert(idx + 1, new_editor)
        self.embeds_container.insertWidget(idx + 1, new_editor)
        self._reindex_embeds()
        self._refresh_embeds_header()
        self._sync_preview()

    def _move_embed(self, editor: EmbedEditor, delta: int) -> None:
        idx = self.embed_editors.index(editor)
        new_idx = idx + delta
        if new_idx < 0 or new_idx >= len(self.embed_editors):
            return
        self.embed_editors[idx], self.embed_editors[new_idx] = self.embed_editors[new_idx], self.embed_editors[idx]
        self.state.embeds[idx], self.state.embeds[new_idx] = self.state.embeds[new_idx], self.state.embeds[idx]
        for i in reversed(range(self.embeds_container.count())):
            self.embeds_container.takeAt(i)
        for e in self.embed_editors:
            self.embeds_container.addWidget(e)
        self._reindex_embeds()
        self._sync_preview()

    def _reindex_embeds(self) -> None:
        for i, e in enumerate(self.embed_editors):
            e.set_index(i)

    def _refresh_embeds_header(self) -> None:
        n = len(self.state.embeds)
        self.embeds_head_label.setText(tr("embeds.header", n=n, max=MAX_EMBEDS))
        self.embeds_empty_hint.setVisible(n == 0)
        self.add_embed_btn.setEnabled(n < MAX_EMBEDS)

    def _on_attach_files(self) -> None:
        if len(self.state.file_paths) >= MAX_FILES:
            self.toast.show_message(tr("files.max_files", max=MAX_FILES), "warning")
            return
        paths, _ = QFileDialog.getOpenFileNames(self, tr("files.dialog_title"))
        if not paths:
            return
        for path in paths:
            if len(self.state.file_paths) >= MAX_FILES:
                self.toast.show_message(tr("files.limit_reached", max=MAX_FILES), "warning")
                break
            try:
                size = os.path.getsize(path)
            except OSError:
                continue
            if size > MAX_FILE_SIZE:
                self.toast.show_message(tr("files.too_large", name=os.path.basename(path), size=bytes_human(MAX_FILE_SIZE)), "error")
                continue
            if path in self.state.file_paths:
                continue
            self.state.file_paths.append(path)
        self._refresh_files_list()
        self._sync_preview()

    def _refresh_files_list(self) -> None:
        while self.files_container.count():
            item = self.files_container.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()
        self.files_empty_hint.setVisible(len(self.state.file_paths) == 0)
        for path in list(self.state.file_paths):
            row = QWidget()
            h = QHBoxLayout(row)
            h.setContentsMargins(0, 0, 0, 0)
            try:
                size = bytes_human(os.path.getsize(path))
            except OSError:
                size = "?"
            label = QLabel(f"{os.path.basename(path)}  ·  {size}")
            label.setTextFormat(Qt.PlainText)
            h.addWidget(label, 1)
            remove_btn = QPushButton(tr("files.remove"))
            remove_btn.setProperty("class", "ghost")
            remove_btn.clicked.connect(lambda checked=False, p=path: self._remove_file(p))
            h.addWidget(remove_btn)
            self.files_container.addWidget(row)

    def _remove_file(self, path: str) -> None:
        if path in self.state.file_paths:
            self.state.file_paths.remove(path)
        self._refresh_files_list()
        self._sync_preview()

    def _apply_json_import(self) -> None:
        import json
        text = self.json_import_edit.toPlainText().strip()
        if not text:
            return
        try:
            data = json.loads(text)
        except json.JSONDecodeError as e:
            self.toast.show_message(tr("json.invalid", error=e), "error")
            return
        if not isinstance(data, dict):
            self.toast.show_message(tr("json.invalid", error=tr("json.not_object")), "error")
            return
        def _text(value) -> str:
            return value if isinstance(value, str) else ""

        new_state = MessageState(
            content=_text(data.get("content"))[:MAX_CONTENT_LEN],
            username=_text(data.get("username"))[:MAX_USERNAME_LEN],
            avatar_url=_text(data.get("avatar_url")),
            tts=bool(data.get("tts", False)),
        )
        embeds_raw = data.get("embeds")
        new_state.embeds = [
            Embed.from_discord_json(e) for e in (embeds_raw if isinstance(embeds_raw, list) else []) if isinstance(e, dict)
        ][:MAX_EMBEDS]
        new_state.file_paths = list(self.state.file_paths)
        self._load_state(new_state)
        self.toast.show_message(tr("json.applied"), "success")

    def _copy_json(self) -> None:
        QGuiApplication.clipboard().setText(self.json_export_edit.toPlainText())
        self.toast.show_message(tr("json.copied"), "success", 2000)

    def _load_state(self, state: MessageState) -> None:
        self.state = state
        self.content_edit.blockSignals(True)
        self.content_edit.setPlainText(state.content)
        self.content_edit.blockSignals(False)
        self.username_edit.blockSignals(True)
        self.username_edit.setText(state.username)
        self.username_edit.blockSignals(False)
        self.avatar_edit.blockSignals(True)
        self.avatar_edit.setText(state.avatar_url)
        self.avatar_edit.blockSignals(False)
        self.avatar_edit.setProperty("error", not is_valid_url(self.avatar_edit.text()))
        self.avatar_edit.style().unpolish(self.avatar_edit)
        self.avatar_edit.style().polish(self.avatar_edit)
        self.thread_name_edit.blockSignals(True)
        self.thread_name_edit.setText(state.thread_name)
        self.thread_name_edit.blockSignals(False)
        self.tts_check.blockSignals(True)
        self.tts_check.setChecked(state.tts)
        self.tts_check.blockSignals(False)

        while self.embeds_container.count():
            item = self.embeds_container.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()
        self.embed_editors = []
        for embed in state.embeds:
            self._add_embed_editor(embed)
        self._refresh_embeds_header()
        self._refresh_files_list()

        n = len(state.content)
        self.content_counter.setText(f"{n}/{MAX_CONTENT_LEN}")
        self.content_counter.setProperty("class", "counter-danger" if n >= MAX_CONTENT_LEN else "counter")
        self.content_counter.style().unpolish(self.content_counter)
        self.content_counter.style().polish(self.content_counter)
        self._sync_preview()

    def _on_clear(self) -> None:
        if QMessageBox.question(self, tr("confirm.clear.title"), tr("confirm.clear.text")) != QMessageBox.Yes:
            return
        self._exit_editing_mode()
        self._load_state(MessageState())
        self.toast.show_message(tr("toast.editor_cleared"), "info", 2000)

    def _sync_preview(self) -> None:
        import json
        profile = self._active_profile()
        display_name = self.state.username.strip() or (profile.default_username if profile else "") or (profile.name if profile else tr("preview.default_username"))
        display_avatar = self.state.avatar_url.strip() or (profile.default_avatar if profile else "")
        self.preview_panel.update_content(self.state, display_name, display_avatar)
        payload = self.state.to_payload()
        self.json_export_edit.setPlainText(json.dumps(payload, indent=2, ensure_ascii=False))

    def _enter_editing_mode(self, message_id: str) -> None:
        self.editing_message_id = message_id
        self.editing_banner.setText(tr("topbar.editing_banner", id=message_id) + "  ·  ")
        self.editing_banner.setVisible(True)
        self.send_btn.setText(tr("topbar.save_changes"))

    def _exit_editing_mode(self) -> None:
        self.editing_message_id = None
        self.editing_banner.setVisible(False)
        self.send_btn.setText(tr("topbar.send"))

    def _run_worker(self, func, *args, on_success=None, on_error=None) -> None:
        worker = ApiWorker(func, *args)
        if on_success:
            worker.succeeded.connect(on_success)
        if on_error:
            worker.failed.connect(on_error)
        worker.finished.connect(lambda: self._workers.remove(worker) if worker in self._workers else None)
        self._workers.append(worker)
        worker.start()

    def _on_test_connection(self) -> None:
        profile = self._active_profile()
        if not profile:
            self.toast.show_message(tr("toast.no_webhook"), "warning")
            return
        self.status_label.setText(tr("status.testing"))
        self._run_worker(
            get_webhook_info, profile.url,
            on_success=self._on_test_success, on_error=self._on_test_error,
        )

    def _on_test_success(self, data: dict) -> None:
        self.status_label.setText(tr("status.ready"))
        name = data.get("name", "?")
        channel_id = data.get("channel_id", "?")
        guild_id = data.get("guild_id", "?")
        self.toast.show_message(
            tr("toast.test_success", name=name, channel=channel_id, guild=guild_id), "success", 6000
        )

    def _on_test_error(self, message: str, detail: str) -> None:
        self.status_label.setText(tr("status.ready"))
        self._show_error(message, detail)

    def _on_send(self) -> None:
        profile = self._active_profile()
        if not profile:
            self.toast.show_message(tr("toast.no_webhook"), "warning")
            return
        if not self.state.content.strip() and not any(not e.is_empty() for e in self.state.embeds) and not self.state.file_paths:
            self.toast.show_message(tr("toast.empty_message"), "warning")
            return

        payload = self.state.to_payload()
        self.send_btn.setEnabled(False)
        self.status_label.setText(tr("status.sending"))

        if self.editing_message_id:
            self._run_worker(
                edit_message, profile.url, self.editing_message_id, payload, list(self.state.file_paths),
                on_success=self._on_edit_success, on_error=self._on_send_error,
            )
        else:
            self._run_worker(
                send_message, profile.url, payload, list(self.state.file_paths),
                on_success=self._on_send_success, on_error=self._on_send_error,
            )

    def _on_send_success(self, response: dict) -> None:
        self.send_btn.setEnabled(True)
        self.status_label.setText(tr("status.ready"))
        message_id = response.get("id", "")
        summary = truncate(self.state.content.strip() or (self.state.embeds[0].title if self.state.embeds else ""), 60)
        entry = HistoryEntry(message_id=message_id, profile_id=self.active_profile_id, summary=summary, payload=self.state.to_dict())
        self.history.append(entry)
        storage.save_history(self.history)
        self.toast.show_message(tr("toast.message_sent", id=message_id), "success")

    def _on_edit_success(self, response: dict) -> None:
        self.send_btn.setEnabled(True)
        self.status_label.setText(tr("status.ready"))
        for h in self.history:
            if h.message_id == self.editing_message_id:
                h.summary = truncate(self.state.content.strip() or (self.state.embeds[0].title if self.state.embeds else ""), 60)
                h.payload = self.state.to_dict()
        storage.save_history(self.history)
        self.toast.show_message(tr("toast.message_updated"), "success")
        self._exit_editing_mode()

    def _on_send_error(self, message: str, detail: str) -> None:
        self.send_btn.setEnabled(True)
        self.status_label.setText(tr("status.ready"))
        self._show_error(message, detail)

    def _show_error(self, message: str, detail: str = "") -> None:
        if detail:
            box = QMessageBox(QMessageBox.Critical, APP_NAME, message, parent=self)
            box.setDetailedText(detail)
            box.exec()
        else:
            self.toast.show_message(message, "error", 7000)

    def _open_history(self) -> None:
        profile = self._active_profile()
        if not profile:
            self.toast.show_message(tr("toast.no_webhook"), "warning")
            return
        entries = [h for h in self.history if h.profile_id == profile.id]
        dialog = HistoryDialog(entries, self._start_edit_from_history, self._delete_from_history, parent=self)
        dialog.exec()

    def _start_edit_from_history(self, entry: HistoryEntry) -> None:
        state = MessageState.from_dict(entry.payload)
        self._load_state(state)
        self._enter_editing_mode(entry.message_id)
        self._switch_page(0)
        self.toast.show_message(tr("toast.message_loaded_for_edit"), "info", 3000)

    def _delete_from_history(self, entry: HistoryEntry, on_done=None) -> None:
        profile = self._active_profile()
        if not profile:
            return

        def on_success(_):
            self.history = [h for h in self.history if h.message_id != entry.message_id]
            storage.save_history(self.history)
            self.toast.show_message(tr("toast.message_deleted"), "success", 3000)
            if on_done:
                on_done()

        def on_error(msg, detail):
            self._show_error(msg, detail)

        self._run_worker(delete_message, profile.url, entry.message_id, on_success=on_success, on_error=on_error)

    def _open_templates(self) -> None:
        dialog = TemplatesDialog(lambda: self.state, self._load_state, parent=self)
        dialog.exec()

    def _on_language_selected(self, code: str) -> None:
        if code == i18n.get_language():
            return
        i18n.set_language(code)
        self.settings["language"] = code
        storage.save_settings(self.settings)
        self.toast.show_message(
            tr("toast.language_changed", language=i18n.LANGUAGES.get(code, code)), "info", 6000
        )

