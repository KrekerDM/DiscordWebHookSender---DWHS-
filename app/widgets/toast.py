from PySide6.QtCore import QTimer, Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QGraphicsOpacityEffect
from PySide6.QtCore import QPropertyAnimation

from app.theme import Colors
from app.utils import truncate

_MAX_TOAST_LEN = 220

_KIND_STYLES = {
    "success": (Colors.GREEN, "#ffffff", "✓"),
    "error": (Colors.RED, "#ffffff", "✕"),
    "info": (Colors.BLURPLE, "#ffffff", "ℹ"),
    "warning": (Colors.TEXT_WARNING, "#1e1f22", "⚠"),
}


class Toast(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setVisible(False)
        self.setMinimumHeight(44)
        self.setStyleSheet("border-radius: 8px;")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 10, 8, 10)
        layout.setSpacing(10)

        self._icon = QLabel()
        self._icon.setFixedWidth(18)
        layout.addWidget(self._icon, 0, Qt.AlignTop)

        self._text = QLabel()
        self._text.setWordWrap(True)
        self._text.setTextFormat(Qt.PlainText)
        self._text.setStyleSheet("background: transparent; font-size: 13px; font-weight: 600;")
        layout.addWidget(self._text, 1)

        close_btn = QPushButton("✕")
        close_btn.setFixedSize(24, 24)
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.setStyleSheet("background: transparent; border: none; font-size: 11px;")
        close_btn.clicked.connect(self.hide_toast)
        layout.addWidget(close_btn, 0, Qt.AlignTop)

        self._opacity = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self._opacity)
        self._opacity.setOpacity(1.0)
        self._anim = QPropertyAnimation(self._opacity, b"opacity")
        self._anim.setDuration(300)

        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self.hide_toast)

    def show_message(self, text: str, kind: str = "info", duration_ms: int = 4500) -> None:
        bg, fg, icon = _KIND_STYLES.get(kind, _KIND_STYLES["info"])
        self.setStyleSheet(f"background-color: {bg}; border-radius: 8px;")
        self._icon.setStyleSheet(f"background: transparent; color: {fg}; font-size: 14px; font-weight: 700;")
        self._icon.setText(icon)
        self._text.setStyleSheet(f"background: transparent; color: {fg}; font-size: 13px; font-weight: 600;")
        self._text.setText(truncate(text, _MAX_TOAST_LEN))
        self._opacity.setOpacity(1.0)
        self.setVisible(True)
        self._timer.stop()
        if duration_ms > 0:
            self._timer.start(duration_ms)

    def hide_toast(self) -> None:
        self._timer.stop()
        self.setVisible(False)
