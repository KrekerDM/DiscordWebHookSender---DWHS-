from PySide6.QtCore import Qt, Signal, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QScrollArea,
    QWidget, QMenu, QComboBox
)

from app.config import AUTHOR_NAME, AUTHOR_URL, APP_NAME, APP_VERSION
from app.i18n import LANGUAGES, get_language, tr
from app.models import WebhookProfile

_AVATAR_COLORS = ["#5865f2", "#23a55a", "#f23f42", "#f0b232", "#eb459e", "#1abc9c", "#e67e22", "#9b59b6"]


def _avatar_color(seed: str) -> str:
    if not seed:
        return _AVATAR_COLORS[0]
    return _AVATAR_COLORS[sum(ord(c) for c in seed) % len(_AVATAR_COLORS)]


class ProfileItem(QPushButton):
    contextMenuRequested = Signal(object, object)

    def __init__(self, profile: WebhookProfile, parent=None):
        super().__init__(parent)
        self.profile = profile
        self.setCheckable(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setProperty("class", "profile-item")
        self.setFixedHeight(56)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(lambda pos: self.contextMenuRequested.emit(self, pos))

        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 4, 6, 4)
        layout.setSpacing(10)

        initial = (profile.name.strip()[:1] or "?").upper()
        avatar = QLabel(initial)
        avatar.setFixedSize(36, 36)
        avatar.setAlignment(Qt.AlignCenter)
        avatar.setStyleSheet(
            f"background-color: {_avatar_color(profile.id)}; color: white; border-radius: 18px; "
            f"font-weight: 700; font-size: 14px;"
        )
        layout.addWidget(avatar)

        text_col = QVBoxLayout()
        text_col.setSpacing(1)
        name_label = QLabel(profile.name)
        name_label.setTextFormat(Qt.PlainText)
        name_label.setStyleSheet("background: transparent; color: #f2f3f5; font-weight: 600; font-size: 13px;")
        text_col.addWidget(name_label)

        masked = self._mask_url(profile.url)
        url_label = QLabel(masked)
        url_label.setStyleSheet("background: transparent; color: #949ba4; font-size: 11px;")
        text_col.addWidget(url_label)

        layout.addLayout(text_col, 1)

    @staticmethod
    def _mask_url(url: str) -> str:
        if not url:
            return tr("sidebar.no_url")
        tail = url.rstrip("/").split("/")[-1]
        if len(tail) > 6:
            tail = tail[:4] + "…" + tail[-2:]
        return f"…/{tail}"

    def set_active(self, active: bool) -> None:
        self.setChecked(active)
        self.setProperty("class", "profile-item-active" if active else "profile-item")
        self.style().unpolish(self)
        self.style().polish(self)


class Sidebar(QFrame):
    profileSelected = Signal(str)
    addRequested = Signal()
    renameRequested = Signal(str)
    duplicateRequested = Signal(str)
    deleteRequested = Signal(str)
    languageSelected = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setProperty("class", "sidebar")
        self.setFixedWidth(248)
        self._items: dict[str, ProfileItem] = {}
        self._active_id: str | None = None

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        header = QWidget()
        header.setFixedHeight(52)
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(16, 0, 12, 0)
        title = QLabel(APP_NAME.upper())
        title.setProperty("class", "app-title")
        title.setStyleSheet("font-size: 13px; font-weight: 800; letter-spacing: 0.02em;")
        h_layout.addWidget(title)
        h_layout.addStretch(1)
        root.addWidget(header)

        sep = QFrame()
        sep.setProperty("class", "divider")
        root.addWidget(sep)

        list_header = QWidget()
        lh_layout = QHBoxLayout(list_header)
        lh_layout.setContentsMargins(16, 12, 12, 6)
        label = QLabel(tr("sidebar.webhooks_title"))
        label.setProperty("class", "section-title")
        lh_layout.addWidget(label)
        lh_layout.addStretch(1)
        add_btn = QPushButton("+")
        add_btn.setProperty("class", "icon")
        add_btn.setFixedSize(24, 24)
        add_btn.setCursor(Qt.PointingHandCursor)
        add_btn.setToolTip(tr("sidebar.add_tooltip"))
        add_btn.clicked.connect(self.addRequested.emit)
        lh_layout.addWidget(add_btn)
        root.addWidget(list_header)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)
        self.list_widget = QWidget()
        self.list_layout = QVBoxLayout(self.list_widget)
        self.list_layout.setContentsMargins(8, 0, 8, 8)
        self.list_layout.setSpacing(4)
        self.list_layout.addStretch(1)
        self.scroll.setWidget(self.list_widget)
        root.addWidget(self.scroll, 1)

        self.empty_hint = QLabel(tr("sidebar.empty"))
        self.empty_hint.setProperty("class", "hint")
        self.empty_hint.setWordWrap(True)
        self.empty_hint.setAlignment(Qt.AlignCenter)
        self.empty_hint.setContentsMargins(16, 24, 16, 0)
        self.list_layout.insertWidget(0, self.empty_hint)

        footer_sep = QFrame()
        footer_sep.setProperty("class", "divider")
        root.addWidget(footer_sep)

        footer = QWidget()
        f_layout = QVBoxLayout(footer)
        f_layout.setContentsMargins(16, 8, 16, 8)
        f_layout.setSpacing(6)

        self.language_combo = QComboBox()
        self.language_combo.setToolTip(tr("sidebar.language_tooltip"))
        for code, name in LANGUAGES.items():
            self.language_combo.addItem(name, userData=code)
        current_index = self.language_combo.findData(get_language())
        if current_index >= 0:
            self.language_combo.setCurrentIndex(current_index)
        self.language_combo.currentIndexChanged.connect(
            lambda i: self.languageSelected.emit(self.language_combo.itemData(i))
        )
        f_layout.addWidget(self.language_combo)

        credit_btn = QPushButton(tr("sidebar.made_by", author=AUTHOR_NAME))
        credit_btn.setProperty("class", "link")
        credit_btn.setCursor(Qt.PointingHandCursor)
        credit_btn.setStyleSheet("text-align: left; padding: 0; font-size: 12px;")
        credit_btn.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(AUTHOR_URL)))
        f_layout.addWidget(credit_btn)
        version_label = QLabel(f"v{APP_VERSION}")
        version_label.setProperty("class", "hint")
        f_layout.addWidget(version_label)
        root.addWidget(footer)

    def set_profiles(self, profiles: list[WebhookProfile], active_id: str | None) -> None:
        for item in self._items.values():
            self.list_layout.removeWidget(item)
            item.deleteLater()
        self._items.clear()
        self._active_id = active_id

        self.empty_hint.setVisible(len(profiles) == 0)

        for profile in profiles:
            item = ProfileItem(profile)
            item.clicked.connect(lambda checked=False, pid=profile.id: self.profileSelected.emit(pid))
            item.contextMenuRequested.connect(self._show_context_menu)
            item.set_active(profile.id == active_id)
            self._items[profile.id] = item
            self.list_layout.insertWidget(self.list_layout.count() - 1, item)

    def _show_context_menu(self, item: ProfileItem, pos) -> None:
        menu = QMenu(self)
        rename_action = menu.addAction(tr("sidebar.rename"))
        duplicate_action = menu.addAction(tr("sidebar.duplicate"))
        menu.addSeparator()
        delete_action = menu.addAction(tr("sidebar.delete"))
        chosen = menu.exec(item.mapToGlobal(pos))
        if chosen == rename_action:
            self.renameRequested.emit(item.profile.id)
        elif chosen == duplicate_action:
            self.duplicateRequested.emit(item.profile.id)
        elif chosen == delete_action:
            self.deleteRequested.emit(item.profile.id)
