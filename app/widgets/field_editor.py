from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPlainTextEdit,
    QPushButton, QCheckBox
)

from app.config import MAX_FIELD_NAME, MAX_FIELD_VALUE
from app.i18n import tr
from app.models import EmbedField


class FieldEditor(QFrame):
    changed = Signal()
    removeRequested = Signal(object)
    moveUpRequested = Signal(object)
    moveDownRequested = Signal(object)

    def __init__(self, field_data: EmbedField, index: int, parent=None):
        super().__init__(parent)
        self.field_data = field_data
        self.setProperty("class", "card")

        root = QVBoxLayout(self)
        root.setContentsMargins(12, 10, 12, 12)
        root.setSpacing(8)

        header = QHBoxLayout()
        self.title_label = QLabel(tr("field.number", n=index + 1))
        self.title_label.setProperty("class", "section-title")
        header.addWidget(self.title_label)
        header.addStretch(1)

        self.inline_check = QCheckBox(tr("field.inline"))
        self.inline_check.setChecked(field_data.inline)
        self.inline_check.toggled.connect(self._on_change)
        header.addWidget(self.inline_check)

        up_btn = QPushButton("↑")
        up_btn.setProperty("class", "icon")
        up_btn.setFixedSize(26, 26)
        up_btn.setCursor(Qt.PointingHandCursor)
        up_btn.setToolTip(tr("field.move_up"))
        up_btn.clicked.connect(lambda: self.moveUpRequested.emit(self))
        header.addWidget(up_btn)

        down_btn = QPushButton("↓")
        down_btn.setProperty("class", "icon")
        down_btn.setFixedSize(26, 26)
        down_btn.setCursor(Qt.PointingHandCursor)
        down_btn.setToolTip(tr("field.move_down"))
        down_btn.clicked.connect(lambda: self.moveDownRequested.emit(self))
        header.addWidget(down_btn)

        del_btn = QPushButton("✕")
        del_btn.setProperty("class", "icon")
        del_btn.setFixedSize(26, 26)
        del_btn.setCursor(Qt.PointingHandCursor)
        del_btn.setToolTip(tr("field.delete"))
        del_btn.clicked.connect(lambda: self.removeRequested.emit(self))
        header.addWidget(del_btn)

        root.addLayout(header)

        self.name_edit = QLineEdit(field_data.name)
        self.name_edit.setPlaceholderText(tr("field.name_ph"))
        self.name_edit.setMaxLength(MAX_FIELD_NAME)
        self.name_edit.textChanged.connect(self._on_change)
        root.addWidget(self.name_edit)

        self.value_edit = QPlainTextEdit(field_data.value)
        self.value_edit.setPlaceholderText(tr("field.value_ph"))
        self.value_edit.setFixedHeight(56)
        self.value_edit.textChanged.connect(self._enforce_value_limit)
        root.addWidget(self.value_edit)

        self.counter_label = QLabel("")
        self.counter_label.setProperty("class", "counter")
        root.addWidget(self.counter_label, alignment=Qt.AlignRight)

        self._update_counter()

    def _enforce_value_limit(self) -> None:
        text = self.value_edit.toPlainText()
        if len(text) > MAX_FIELD_VALUE:
            cursor = self.value_edit.textCursor()
            pos = cursor.position()
            self.value_edit.blockSignals(True)
            self.value_edit.setPlainText(text[:MAX_FIELD_VALUE])
            cursor.setPosition(min(pos, MAX_FIELD_VALUE))
            self.value_edit.setTextCursor(cursor)
            self.value_edit.blockSignals(False)
        self._on_change()

    def _update_counter(self) -> None:
        n_len = len(self.name_edit.text())
        v_len = len(self.value_edit.toPlainText())
        self.counter_label.setText(
            tr("field.counter", n=n_len, max_n=MAX_FIELD_NAME, v=v_len, max_v=MAX_FIELD_VALUE)
        )

    def _on_change(self) -> None:
        self.field_data.name = self.name_edit.text()
        self.field_data.value = self.value_edit.toPlainText()
        self.field_data.inline = self.inline_check.isChecked()
        self._update_counter()
        self.changed.emit()

    def set_index(self, index: int) -> None:
        self.title_label.setText(tr("field.number", n=index + 1))
