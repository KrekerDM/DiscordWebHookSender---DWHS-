from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QLineEdit,
    QPlainTextEdit, QPushButton, QCheckBox, QWidget
)

from app.config import (
    MAX_EMBED_TITLE, MAX_EMBED_DESCRIPTION, MAX_EMBED_FIELDS, MAX_AUTHOR_NAME,
    MAX_FOOTER_TEXT, MAX_TOTAL_EMBED,
)
from app.i18n import tr
from app.models import Embed, EmbedField
from app.utils import is_valid_url
from app.widgets.color_picker import ColorPicker
from app.widgets.field_editor import FieldEditor


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


class EmbedEditor(QFrame):
    changed = Signal()
    removeRequested = Signal(object)
    duplicateRequested = Signal(object)
    moveUpRequested = Signal(object)
    moveDownRequested = Signal(object)

    def __init__(self, embed: Embed, index: int, parent=None):
        super().__init__(parent)
        self.embed = embed
        self.setProperty("class", "card")
        self._collapsed = False

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        header = QWidget()
        header.setStyleSheet(f"background-color: {self._bar_color()}; border-top-left-radius: 8px; border-top-right-radius: 8px;")
        header.setFixedHeight(6)
        outer.addWidget(header)
        self._header_bar = header

        content = QVBoxLayout()
        content.setContentsMargins(14, 12, 14, 14)
        content.setSpacing(10)

        top_row = QHBoxLayout()
        self.title_label = QLabel(tr("embed.number", n=index + 1))
        self.title_label.setProperty("class", "section-title")
        top_row.addWidget(self.title_label)
        top_row.addStretch(1)

        self.collapse_btn = QPushButton("▾")
        self.collapse_btn.setProperty("class", "icon")
        self.collapse_btn.setFixedSize(26, 26)
        self.collapse_btn.setCursor(Qt.PointingHandCursor)
        self.collapse_btn.clicked.connect(self._toggle_collapse)
        top_row.addWidget(self.collapse_btn)

        for symbol, tip, handler in (
            ("↑", tr("embed.move_up"), lambda: self.moveUpRequested.emit(self)),
            ("↓", tr("embed.move_down"), lambda: self.moveDownRequested.emit(self)),
            ("⧉", tr("embed.duplicate"), lambda: self.duplicateRequested.emit(self)),
            ("✕", tr("embed.delete"), lambda: self.removeRequested.emit(self)),
        ):
            btn = QPushButton(symbol)
            btn.setProperty("class", "icon")
            btn.setFixedSize(26, 26)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setToolTip(tip)
            btn.clicked.connect(handler)
            top_row.addWidget(btn)

        content.addLayout(top_row)

        self.body = QWidget()
        body_layout = QVBoxLayout(self.body)
        body_layout.setContentsMargins(0, 4, 0, 0)
        body_layout.setSpacing(14)

        body_layout.addWidget(self._build_author_section())
        body_layout.addWidget(self._build_title_section())
        body_layout.addWidget(self._build_description_section())
        body_layout.addWidget(self._build_color_section())
        body_layout.addWidget(self._build_images_section())
        body_layout.addWidget(self._build_footer_section())
        body_layout.addWidget(self._build_fields_section())

        content.addWidget(self.body)
        outer.addLayout(content)

        self.total_counter = QLabel()
        self.total_counter.setProperty("class", "counter")
        content.addWidget(self.total_counter, alignment=Qt.AlignRight)

        self._refresh_all_counters()
        self._update_error_states()

    def _bar_color(self) -> str:
        from app.utils import int_to_hex
        return int_to_hex(self.embed.color)

    def _toggle_collapse(self) -> None:
        self._collapsed = not self._collapsed
        self.body.setVisible(not self._collapsed)
        self.collapse_btn.setText("▸" if self._collapsed else "▾")

    def set_index(self, index: int) -> None:
        self.title_label.setText(tr("embed.number", n=index + 1))

    def _build_author_section(self) -> QWidget:
        section = QWidget()
        v = QVBoxLayout(section)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(6)
        v.addWidget(_section_label(tr("embed.author_title")))

        self.author_name = QLineEdit(self.embed.author_name)
        self.author_name.setPlaceholderText(tr("embed.author_name_ph"))
        self.author_name.setMaxLength(MAX_AUTHOR_NAME)
        self.author_name.textChanged.connect(self._on_change)

        self.author_url = QLineEdit(self.embed.author_url)
        self.author_url.setPlaceholderText(tr("embed.author_url_ph"))
        self.author_url.textChanged.connect(self._on_change)

        self.author_icon = QLineEdit(self.embed.author_icon)
        self.author_icon.setPlaceholderText(tr("embed.author_icon_ph"))
        self.author_icon.textChanged.connect(self._on_change)

        grid = QGridLayout()
        grid.setSpacing(6)
        grid.addWidget(self.author_name, 0, 0)
        grid.addWidget(self.author_url, 0, 1)
        grid.addWidget(self.author_icon, 1, 0, 1, 2)
        v.addLayout(grid)
        return section

    def _build_title_section(self) -> QWidget:
        section = QWidget()
        v = QVBoxLayout(section)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(6)
        head = QHBoxLayout()
        head.addWidget(_section_label(tr("embed.title_title")))
        head.addStretch(1)
        self.title_counter = _hint("")
        head.addWidget(self.title_counter)
        v.addLayout(head)

        self.title_edit = QLineEdit(self.embed.title)
        self.title_edit.setPlaceholderText(tr("embed.title_ph"))
        self.title_edit.setMaxLength(MAX_EMBED_TITLE)
        self.title_edit.textChanged.connect(self._on_change)
        v.addWidget(self.title_edit)

        self.url_edit = QLineEdit(self.embed.url)
        self.url_edit.setPlaceholderText(tr("embed.url_ph"))
        self.url_edit.textChanged.connect(self._on_change)
        v.addWidget(self.url_edit)
        return section

    def _build_description_section(self) -> QWidget:
        section = QWidget()
        v = QVBoxLayout(section)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(6)
        head = QHBoxLayout()
        head.addWidget(_section_label(tr("embed.desc_title")))
        head.addStretch(1)
        self.desc_counter = _hint("")
        head.addWidget(self.desc_counter)
        v.addLayout(head)

        self.desc_edit = QPlainTextEdit(self.embed.description)
        self.desc_edit.setPlaceholderText(tr("embed.desc_ph"))
        self.desc_edit.setFixedHeight(90)
        self.desc_edit.textChanged.connect(self._enforce_desc_limit)
        v.addWidget(self.desc_edit)
        return section

    def _build_color_section(self) -> QWidget:
        section = QWidget()
        v = QVBoxLayout(section)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(6)
        v.addWidget(_section_label(tr("embed.color_title")))
        self.color_picker = ColorPicker(self.embed.color)
        self.color_picker.colorChanged.connect(self._on_color_change)
        v.addWidget(self.color_picker)
        return section

    def _build_images_section(self) -> QWidget:
        section = QWidget()
        grid = QGridLayout(section)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setSpacing(6)

        grid.addWidget(_section_label(tr("embed.thumb_title")), 0, 0)
        self.thumb_edit = QLineEdit(self.embed.thumbnail_url)
        self.thumb_edit.setPlaceholderText(tr("embed.thumb_ph"))
        self.thumb_edit.textChanged.connect(self._on_change)
        grid.addWidget(self.thumb_edit, 1, 0)

        grid.addWidget(_section_label(tr("embed.image_title")), 0, 1)
        self.image_edit = QLineEdit(self.embed.image_url)
        self.image_edit.setPlaceholderText(tr("embed.image_ph"))
        self.image_edit.textChanged.connect(self._on_change)
        grid.addWidget(self.image_edit, 1, 1)
        return section

    def _build_footer_section(self) -> QWidget:
        section = QWidget()
        v = QVBoxLayout(section)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(6)
        head = QHBoxLayout()
        head.addWidget(_section_label(tr("embed.footer_title")))
        head.addStretch(1)
        self.footer_counter = _hint("")
        head.addWidget(self.footer_counter)
        v.addLayout(head)

        grid = QGridLayout()
        grid.setSpacing(6)
        self.footer_text = QLineEdit(self.embed.footer_text)
        self.footer_text.setPlaceholderText(tr("embed.footer_text_ph"))
        self.footer_text.setMaxLength(MAX_FOOTER_TEXT)
        self.footer_text.textChanged.connect(self._on_change)
        grid.addWidget(self.footer_text, 0, 0)

        self.footer_icon = QLineEdit(self.embed.footer_icon)
        self.footer_icon.setPlaceholderText(tr("embed.footer_icon_ph"))
        self.footer_icon.textChanged.connect(self._on_change)
        grid.addWidget(self.footer_icon, 0, 1)
        v.addLayout(grid)

        self.timestamp_check = QCheckBox(tr("embed.timestamp_check"))
        self.timestamp_check.setChecked(self.embed.use_timestamp)
        self.timestamp_check.toggled.connect(self._on_change)
        v.addWidget(self.timestamp_check)
        return section

    def _build_fields_section(self) -> QWidget:
        section = QWidget()
        v = QVBoxLayout(section)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(8)
        head = QHBoxLayout()
        head.addWidget(_section_label(tr("embed.fields_title")))
        head.addStretch(1)
        self.fields_counter = _hint("")
        head.addWidget(self.fields_counter)
        v.addLayout(head)

        self.fields_container = QVBoxLayout()
        self.fields_container.setSpacing(8)
        v.addLayout(self.fields_container)

        self.add_field_btn = QPushButton(tr("embed.add_field"))
        self.add_field_btn.setProperty("class", "ghost")
        self.add_field_btn.setCursor(Qt.PointingHandCursor)
        self.add_field_btn.clicked.connect(self._add_field)
        v.addWidget(self.add_field_btn)

        self._field_rows: list[FieldEditor] = []
        for f in self.embed.fields:
            self._add_field_row(f)
        return section

    def _add_field(self) -> None:
        if len(self.embed.fields) >= MAX_EMBED_FIELDS:
            return
        f = EmbedField()
        self.embed.fields.append(f)
        self._add_field_row(f)
        self._on_change()

    def _add_field_row(self, f: EmbedField) -> None:
        row = FieldEditor(f, len(self._field_rows))
        row.changed.connect(self._on_change)
        row.removeRequested.connect(self._remove_field)
        row.moveUpRequested.connect(lambda r: self._move_field(r, -1))
        row.moveDownRequested.connect(lambda r: self._move_field(r, 1))
        self._field_rows.append(row)
        self.fields_container.addWidget(row)

    def _remove_field(self, row: FieldEditor) -> None:
        idx = self._field_rows.index(row)
        self._field_rows.pop(idx)
        self.embed.fields.pop(idx)
        self.fields_container.removeWidget(row)
        row.deleteLater()
        self._reindex_fields()
        self._on_change()

    def _move_field(self, row: FieldEditor, delta: int) -> None:
        idx = self._field_rows.index(row)
        new_idx = idx + delta
        if new_idx < 0 or new_idx >= len(self._field_rows):
            return
        self._field_rows[idx], self._field_rows[new_idx] = self._field_rows[new_idx], self._field_rows[idx]
        self.embed.fields[idx], self.embed.fields[new_idx] = self.embed.fields[new_idx], self.embed.fields[idx]
        for i in reversed(range(self.fields_container.count())):
            self.fields_container.takeAt(i)
        for r in self._field_rows:
            self.fields_container.addWidget(r)
        self._reindex_fields()
        self._on_change()

    def _reindex_fields(self) -> None:
        for i, r in enumerate(self._field_rows):
            r.set_index(i)

    def _enforce_desc_limit(self) -> None:
        text = self.desc_edit.toPlainText()
        if len(text) > MAX_EMBED_DESCRIPTION:
            cursor = self.desc_edit.textCursor()
            pos = cursor.position()
            self.desc_edit.blockSignals(True)
            self.desc_edit.setPlainText(text[:MAX_EMBED_DESCRIPTION])
            cursor.setPosition(min(pos, MAX_EMBED_DESCRIPTION))
            self.desc_edit.setTextCursor(cursor)
            self.desc_edit.blockSignals(False)
        self._on_change()

    def _on_color_change(self, value: int) -> None:
        self.embed.color = value
        self._header_bar.setStyleSheet(
            f"background-color: {self._bar_color()}; border-top-left-radius: 8px; border-top-right-radius: 8px;"
        )
        self.changed.emit()

    def _on_change(self) -> None:
        self.embed.title = self.title_edit.text()
        self.embed.url = self.url_edit.text()
        self.embed.description = self.desc_edit.toPlainText()
        self.embed.author_name = self.author_name.text()
        self.embed.author_url = self.author_url.text()
        self.embed.author_icon = self.author_icon.text()
        self.embed.thumbnail_url = self.thumb_edit.text()
        self.embed.image_url = self.image_edit.text()
        self.embed.footer_text = self.footer_text.text()
        self.embed.footer_icon = self.footer_icon.text()
        self.embed.use_timestamp = self.timestamp_check.isChecked()

        self._update_error_states()
        self._refresh_all_counters()
        self.changed.emit()

    def _update_error_states(self) -> None:
        for edit in (self.author_url, self.author_icon, self.thumb_edit,
                     self.image_edit, self.footer_icon, self.url_edit):
            edit.setProperty("error", not is_valid_url(edit.text()))
            edit.style().unpolish(edit)
            edit.style().polish(edit)

    def _refresh_all_counters(self) -> None:
        self.title_counter.setText(f"{len(self.title_edit.text())}/{MAX_EMBED_TITLE}")
        self.desc_counter.setText(f"{len(self.desc_edit.toPlainText())}/{MAX_EMBED_DESCRIPTION}")
        self.footer_counter.setText(f"{len(self.footer_text.text())}/{MAX_FOOTER_TEXT}")
        self.fields_counter.setText(f"{len(self.embed.fields)}/{MAX_EMBED_FIELDS}")
        self.add_field_btn.setEnabled(len(self.embed.fields) < MAX_EMBED_FIELDS)

        total = (
            len(self.title_edit.text()) + len(self.desc_edit.toPlainText()) +
            len(self.footer_text.text()) + len(self.author_name.text()) +
            sum(len(f.name) + len(f.value) for f in self.embed.fields)
        )
        self.total_counter.setText(tr("embed.total_counter", total=total, max=MAX_TOTAL_EMBED))
        warn = total > MAX_TOTAL_EMBED
        self.total_counter.setProperty("class", "counter-danger" if warn else "counter")
        self.total_counter.style().unpolish(self.total_counter)
        self.total_counter.style().polish(self.total_counter)
