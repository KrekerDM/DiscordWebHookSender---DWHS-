import random

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QGridLayout, QLineEdit, QPushButton, QColorDialog, QToolButton
)

from app.config import DEFAULT_EMBED_COLOR
from app.i18n import tr
from app.utils import hex_to_int, int_to_hex

PRESETS = [
    0x5865F2, 0x23A55A, 0xF23F42, 0xF0B232, 0xEB459E,
    0xF26522, 0x1ABC9C, 0x3498DB, 0x9B59B6, 0x2C2F33,
    0xFFFFFF, 0x99AAB5,
]


class ColorSwatch(QToolButton):
    def __init__(self, color: int, parent=None):
        super().__init__(parent)
        self.color = color
        self.setFixedSize(20, 20)
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet(
            f"QToolButton {{ background-color: {int_to_hex(color)}; border-radius: 10px; border: 2px solid transparent; }}"
            f"QToolButton:hover {{ border: 2px solid white; }}"
        )


class ColorPicker(QWidget):
    colorChanged = Signal(int)

    def __init__(self, initial: int = DEFAULT_EMBED_COLOR, parent=None):
        super().__init__(parent)
        self._color = initial

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(8)

        top_row = QHBoxLayout()
        top_row.setSpacing(8)

        self._swatch = QPushButton()
        self._swatch.setFixedSize(34, 34)
        self._swatch.setCursor(Qt.PointingHandCursor)
        self._swatch.clicked.connect(self._open_dialog)
        top_row.addWidget(self._swatch)

        self._hex_edit = QLineEdit()
        self._hex_edit.setPlaceholderText("#5865F2")
        self._hex_edit.setMaximumWidth(100)
        self._hex_edit.textEdited.connect(self._on_hex_edited)
        top_row.addWidget(self._hex_edit)

        self._random_btn = QPushButton("🎲")
        self._random_btn.setProperty("class", "icon")
        self._random_btn.setFixedSize(30, 30)
        self._random_btn.setCursor(Qt.PointingHandCursor)
        self._random_btn.setToolTip(tr("color.random_tooltip"))
        self._random_btn.clicked.connect(self._random_color)
        top_row.addWidget(self._random_btn)
        top_row.addStretch(1)
        outer.addLayout(top_row)

        presets_grid = QGridLayout()
        presets_grid.setSpacing(6)
        columns = 8
        for i, preset in enumerate(PRESETS):
            sw = ColorSwatch(preset)
            sw.clicked.connect(lambda checked=False, c=preset: self.set_color(c))
            presets_grid.addWidget(sw, i // columns, i % columns)
        presets_wrap = QHBoxLayout()
        presets_wrap.addLayout(presets_grid)
        presets_wrap.addStretch(1)
        outer.addLayout(presets_wrap)

        self._refresh()

    def _refresh(self) -> None:
        hex_str = int_to_hex(self._color)
        self._swatch.setStyleSheet(
            f"background-color: {hex_str}; border-radius: 8px; border: 1px solid rgba(255,255,255,0.15);"
        )
        self._hex_edit.setText(hex_str)

    def _open_dialog(self) -> None:
        initial = QColor(int_to_hex(self._color))
        color = QColorDialog.getColor(initial, self, tr("color.dialog_title"))
        if color.isValid():
            self.set_color(int(color.red() << 16 | color.green() << 8 | color.blue()))

    def _on_hex_edited(self, text: str) -> None:
        value = hex_to_int(text)
        if value is not None:
            self._color = value
            self._swatch.setStyleSheet(
                f"background-color: {int_to_hex(value)}; border-radius: 8px; border: 1px solid rgba(255,255,255,0.15);"
            )
            self.colorChanged.emit(value)

    def _random_color(self) -> None:
        self.set_color(random.randint(0, 0xFFFFFF))

    def set_color(self, value: int) -> None:
        self._color = value
        self._refresh()
        self.colorChanged.emit(value)

    def color(self) -> int:
        return self._color
