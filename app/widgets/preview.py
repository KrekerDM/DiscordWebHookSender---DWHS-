import os
from html import escape as _html_escape

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap, QPainter, QColor, QPen, QPainterPath
from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QWidget, QScrollArea
)

from app.i18n import tr
from app.image_loader import ImageLoader, circular_pixmap, rounded_pixmap
from app.models import MessageState, Embed
from app.utils import markdown_to_html, now_clock_time, int_to_hex, bytes_human
from app.theme import Colors

EMBED_MAX_WIDTH = 432
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp"}


def _default_avatar_pixmap(size: int) -> QPixmap:
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setBrush(QColor(Colors.BLURPLE))
    painter.setPen(Qt.NoPen)
    painter.drawEllipse(0, 0, size, size)
    pen = QPen(QColor("white"))
    pen.setWidthF(size * 0.09)
    pen.setCapStyle(Qt.RoundCap)
    painter.setPen(pen)
    painter.setBrush(Qt.NoBrush)
    r = size * 0.16
    painter.drawEllipse(int(size * 0.24 - r / 2), int(size * 0.5 - r / 2), int(r), int(r))
    painter.drawEllipse(int(size * 0.76 - r / 2), int(size * 0.32 - r / 2), int(r), int(r))
    painter.drawLine(int(size * 0.30), int(size * 0.55), int(size * 0.70), int(size * 0.37))
    painter.end()
    return pixmap


class RemoteAvatar(QLabel):
    def __init__(self, size: int, circular: bool = True, parent=None):
        super().__init__(parent)
        self.size = size
        self.circular = circular
        self.setFixedSize(size, size)
        self._default = _default_avatar_pixmap(size) if circular else None
        if self._default:
            self.setPixmap(self._default)

    def set_url(self, url: str) -> None:
        if not url:
            if self._default:
                self.setPixmap(self._default)
            else:
                self.clear()
                self.setVisible(False)
            return
        self.setVisible(True)
        ImageLoader.instance().fetch(url, self._on_loaded)

    def _on_loaded(self, pixmap: QPixmap) -> None:
        if self.circular:
            self.setPixmap(circular_pixmap(pixmap, self.size))
        else:
            self.setPixmap(pixmap.scaled(self.size, self.size, Qt.KeepAspectRatio, Qt.SmoothTransformation))


class RemoteImageBlock(QLabel):
    def __init__(self, max_width: int, max_height: int, radius: int = 6, parent=None):
        super().__init__(parent)
        self.max_width = max_width
        self.max_height = max_height
        self.radius = radius
        self.setVisible(False)

    def set_url(self, url: str) -> None:
        if not url:
            self.setVisible(False)
            self.clear()
            return
        ImageLoader.instance().fetch(url, self._on_loaded)

    def _on_loaded(self, pixmap: QPixmap) -> None:
        rounded = rounded_pixmap(pixmap, self.max_width, self.max_height, self.radius)
        self.setPixmap(rounded)
        self.setFixedSize(rounded.size())
        self.setVisible(True)


def _rich_label(size: int = 14, weight: int = 400, color: str = Colors.TEXT_NORMAL) -> QLabel:
    lbl = QLabel()
    lbl.setWordWrap(True)
    lbl.setTextFormat(Qt.RichText)
    lbl.setOpenExternalLinks(True)
    lbl.setTextInteractionFlags(Qt.TextBrowserInteraction)
    lbl.setStyleSheet(f"background: transparent; color: {color}; font-size: {size}px; font-weight: {weight};")
    return lbl


def _file_icon_pixmap(size: int = 36) -> QPixmap:
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    m = size * 0.12
    w = size - 2 * m
    h = size - 2 * m
    fold = w * 0.32

    body = QPainterPath()
    body.moveTo(m, m)
    body.lineTo(m + w - fold, m)
    body.lineTo(m + w, m + fold)
    body.lineTo(m + w, m + h)
    body.lineTo(m, m + h)
    body.closeSubpath()
    painter.setPen(Qt.NoPen)
    painter.setBrush(QColor(Colors.SURFACE_CONTAINER_HIGHEST))
    painter.drawPath(body)

    fold_path = QPainterPath()
    fold_path.moveTo(m + w - fold, m)
    fold_path.lineTo(m + w, m + fold)
    fold_path.lineTo(m + w - fold, m + fold)
    fold_path.closeSubpath()
    painter.setBrush(QColor(Colors.OUTLINE_VARIANT))
    painter.drawPath(fold_path)

    pen = QPen(QColor(Colors.TEXT_MUTED))
    pen.setWidthF(max(1.0, size * 0.045))
    pen.setCapStyle(Qt.RoundCap)
    painter.setPen(pen)
    for i in range(3):
        y = m + h * 0.42 + i * h * 0.16
        painter.drawLine(int(m + w * 0.16), int(y), int(m + w * 0.7), int(y))
    painter.end()
    return pixmap


class FileAttachmentPreview(QFrame):
    def __init__(self, path: str, parent=None):
        super().__init__(parent)
        self.setMaximumWidth(EMBED_MAX_WIDTH)
        name = os.path.basename(path)
        ext = os.path.splitext(name)[1].lower()

        if ext in IMAGE_EXTENSIONS and os.path.isfile(path):
            source = QPixmap(path)
        else:
            source = None

        if source is not None and not source.isNull():
            self.setStyleSheet("background: transparent;")
            layout = QVBoxLayout(self)
            layout.setContentsMargins(0, 0, 0, 0)
            img = QLabel()
            img.setPixmap(rounded_pixmap(source, 400, 300, 8))
            layout.addWidget(img)
            return

        self.setStyleSheet(f"background-color: {Colors.SURFACE_CONTAINER_HIGH}; border-radius: 8px;")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 10, 16, 10)
        layout.setSpacing(12)

        icon_lbl = QLabel()
        icon_lbl.setStyleSheet("background: transparent;")
        icon_lbl.setPixmap(_file_icon_pixmap(36))
        layout.addWidget(icon_lbl)

        text_col = QVBoxLayout()
        text_col.setSpacing(2)
        name_lbl = _rich_label(size=14, weight=600, color=Colors.TEXT_LINK)
        name_lbl.setTextFormat(Qt.PlainText)
        name_lbl.setText(name)
        text_col.addWidget(name_lbl)

        try:
            size_txt = bytes_human(os.path.getsize(path))
        except OSError:
            size_txt = ""
        size_lbl = _rich_label(size=12, weight=400, color=Colors.TEXT_MUTED)
        size_lbl.setText(size_txt)
        text_col.addWidget(size_lbl)

        layout.addLayout(text_col, 1)
        layout.addStretch(1)


class FieldPreview(QWidget):
    def __init__(self, name: str, value: str, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        name_lbl = _rich_label(size=13, weight=700, color=Colors.HEADER_SECONDARY)
        name_lbl.setText(markdown_to_html(name, allow_links=True) or "​")
        layout.addWidget(name_lbl)
        value_lbl = _rich_label(size=14, weight=400, color=Colors.TEXT_NORMAL)
        value_lbl.setText(markdown_to_html(value, allow_links=True) or "​")
        layout.addWidget(value_lbl)


class EmbedPreview(QFrame):
    def __init__(self, embed: Embed, parent=None):
        super().__init__(parent)
        self.setMaximumWidth(EMBED_MAX_WIDTH)
        self.setStyleSheet("background: transparent;")

        outer = QHBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        bar = QFrame()
        bar.setFixedWidth(4)
        bar.setStyleSheet(
            f"background-color: {int_to_hex(embed.color)}; border-top-left-radius: 4px; border-bottom-left-radius: 4px;"
        )
        outer.addWidget(bar)

        right_container = QVBoxLayout()
        right_container.setContentsMargins(0, 0, 0, 0)
        right_container.setSpacing(0)

        card = QFrame()
        has_image = bool(embed.image_url.strip())
        radius_css = (
            "border-top-right-radius: 4px;" if has_image else
            "border-top-right-radius: 4px; border-bottom-right-radius: 4px;"
        )
        card.setStyleSheet(f"background-color: #2b2d31; {radius_css}")
        card_layout = QHBoxLayout(card)
        card_layout.setContentsMargins(16, 14, 16, 14)
        card_layout.setSpacing(12)

        left_col = QVBoxLayout()
        left_col.setSpacing(8)

        if embed.author_name.strip():
            author_row = QHBoxLayout()
            author_row.setSpacing(8)
            if embed.author_icon.strip():
                icon = RemoteAvatar(20, circular=True)
                icon.set_url(embed.author_icon)
                author_row.addWidget(icon)
            author_lbl = _rich_label(size=14, weight=700, color=Colors.TEXT_NORMAL)
            text = _html_escape(embed.author_name.strip())
            if embed.author_url.strip():
                author_lbl.setText(f'<a href="{_html_escape(embed.author_url.strip())}" style="color:{Colors.TEXT_NORMAL};text-decoration:none;">{text}</a>')
            else:
                author_lbl.setText(text)
            author_row.addWidget(author_lbl, 1)
            left_col.addLayout(author_row)

        if embed.title.strip():
            title_lbl = _rich_label(size=15, weight=700, color=Colors.TEXT_LINK if embed.url.strip() else Colors.TEXT_NORMAL)
            title_text = _html_escape(embed.title.strip())
            if embed.url.strip():
                title_lbl.setText(f'<a href="{_html_escape(embed.url.strip())}" style="color:{Colors.TEXT_LINK};text-decoration:none;">{title_text}</a>')
            else:
                title_lbl.setText(title_text)
            left_col.addWidget(title_lbl)

        if embed.description.strip():
            desc_lbl = _rich_label(size=14, weight=400, color=Colors.TEXT_NORMAL)
            desc_lbl.setText(markdown_to_html(embed.description, allow_links=True))
            left_col.addWidget(desc_lbl)

        if embed.fields:
            fields_col = QVBoxLayout()
            fields_col.setSpacing(8)
            row: list = []

            def flush():
                if not row:
                    return
                hrow = QHBoxLayout()
                hrow.setSpacing(16)
                for f in row:
                    hrow.addWidget(FieldPreview(f.name, f.value), 1)
                fields_col.addLayout(hrow)
                row.clear()

            for f in embed.fields:
                if not (f.name.strip() or f.value.strip()):
                    continue
                if not f.inline:
                    flush()
                    hrow = QHBoxLayout()
                    hrow.addWidget(FieldPreview(f.name, f.value), 1)
                    fields_col.addLayout(hrow)
                    continue
                row.append(f)
                if len(row) == 3:
                    flush()
            flush()
            left_col.addLayout(fields_col)

        if embed.footer_text.strip():
            footer_row = QHBoxLayout()
            footer_row.setSpacing(8)
            if embed.footer_icon.strip():
                ficon = RemoteAvatar(20, circular=True)
                ficon.set_url(embed.footer_icon)
                footer_row.addWidget(ficon)
            footer_text = embed.footer_text.strip()
            if embed.use_timestamp:
                footer_text += f"  •  {tr('preview.today_at', time=now_clock_time())}"
            footer_lbl = _rich_label(size=12, weight=500, color=Colors.TEXT_MUTED)
            footer_lbl.setText(markdown_to_html(footer_text))
            footer_row.addWidget(footer_lbl, 1)
            left_col.addLayout(footer_row)

        card_layout.addLayout(left_col, 1)

        if embed.thumbnail_url.strip():
            thumb = RemoteImageBlock(80, 80, radius=6)
            thumb.set_url(embed.thumbnail_url)
            thumb.setAlignment(Qt.AlignTop)
            card_layout.addWidget(thumb, 0, Qt.AlignTop)

        right_container.addWidget(card)

        if has_image:
            image_wrap = QFrame()
            image_wrap.setStyleSheet("background-color: #2b2d31; border-bottom-right-radius: 4px;")
            image_layout = QVBoxLayout(image_wrap)
            image_layout.setContentsMargins(16, 0, 16, 14)
            image = RemoteImageBlock(400, 300, radius=6)
            image.set_url(embed.image_url)
            image_layout.addWidget(image)
            right_container.addWidget(image_wrap)

        outer.addLayout(right_container, 1)


class MessagePreview(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background: transparent;")
        self.root_layout = QHBoxLayout(self)
        self.root_layout.setContentsMargins(16, 10, 16, 10)
        self.root_layout.setSpacing(16)
        self.root_layout.setAlignment(Qt.AlignTop)

        self.avatar = RemoteAvatar(40, circular=True)
        self.root_layout.addWidget(self.avatar, 0, Qt.AlignTop)

        col = QVBoxLayout()
        col.setSpacing(2)

        header_row = QHBoxLayout()
        header_row.setSpacing(6)
        self.username_lbl = QLabel(tr("preview.default_username"))
        self.username_lbl.setTextFormat(Qt.PlainText)
        self.username_lbl.setStyleSheet("background: transparent; color: white; font-size: 15px; font-weight: 600;")
        header_row.addWidget(self.username_lbl)

        self.bot_badge = QLabel(tr("preview.bot_badge"))
        self.bot_badge.setFixedHeight(15)
        self.bot_badge.setStyleSheet(
            f"background-color: {Colors.BADGE_BOT_BG}; color: white; font-size: 10px; font-weight: 700; "
            f"border-radius: 3px; padding: 0px 4px;"
        )
        header_row.addWidget(self.bot_badge)

        self.timestamp_lbl = QLabel(tr("preview.today_at", time=now_clock_time()))
        self.timestamp_lbl.setStyleSheet(f"background: transparent; color: {Colors.TEXT_FAINT}; font-size: 12px;")
        header_row.addWidget(self.timestamp_lbl)
        header_row.addStretch(1)
        col.addLayout(header_row)

        self.content_lbl = _rich_label(size=15, weight=400)
        self.content_lbl.setVisible(False)
        col.addWidget(self.content_lbl)

        self.attachments_col = QVBoxLayout()
        self.attachments_col.setSpacing(8)
        col.addLayout(self.attachments_col)

        self.embeds_col = QVBoxLayout()
        self.embeds_col.setSpacing(8)
        col.addLayout(self.embeds_col)

        self.root_layout.addLayout(col, 1)

    def update_content(self, state: MessageState, username: str, avatar_url: str) -> None:
        self.username_lbl.setText(username or tr("preview.default_username"))
        self.avatar.set_url(avatar_url)

        if state.content.strip():
            self.content_lbl.setText(markdown_to_html(state.content, allow_links=False))
            self.content_lbl.setVisible(True)
        else:
            self.content_lbl.setVisible(False)

        while self.embeds_col.count():
            item = self.embeds_col.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()
            elif item.layout():
                _clear_layout(item.layout())

        for embed in state.embeds:
            if embed.is_empty():
                continue
            self.embeds_col.addWidget(EmbedPreview(embed))

        while self.attachments_col.count():
            item = self.attachments_col.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()
            elif item.layout():
                _clear_layout(item.layout())

        for path in state.file_paths:
            self.attachments_col.addWidget(FileAttachmentPreview(path))


def _clear_layout(layout) -> None:
    while layout.count():
        item = layout.takeAt(0)
        w = item.widget()
        if w:
            w.deleteLater()
        elif item.layout():
            _clear_layout(item.layout())


class PreviewPanel(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setProperty("class", "preview-panel")

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        header = QWidget()
        header.setFixedHeight(48)
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(16, 0, 16, 0)
        label = QLabel(tr("preview.title"))
        label.setProperty("class", "section-title")
        h_layout.addWidget(label)
        h_layout.addStretch(1)
        root.addWidget(header)

        sep = QFrame()
        sep.setProperty("class", "divider")
        root.addWidget(sep)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)

        inner = QWidget()
        inner_layout = QVBoxLayout(inner)
        inner_layout.setContentsMargins(0, 8, 0, 24)
        inner_layout.setAlignment(Qt.AlignTop)

        self.message = MessagePreview()
        inner_layout.addWidget(self.message)

        self.empty_state = QLabel(tr("preview.empty"))
        self.empty_state.setProperty("class", "hint")
        self.empty_state.setAlignment(Qt.AlignCenter)
        self.empty_state.setWordWrap(True)
        self.empty_state.setContentsMargins(16, 40, 16, 0)
        inner_layout.addWidget(self.empty_state)

        self.scroll.setWidget(inner)
        root.addWidget(self.scroll, 1)

    def update_content(self, state: MessageState, username: str, avatar_url: str) -> None:
        has_content = bool(state.content.strip()) or any(not e.is_empty() for e in state.embeds) or bool(state.file_paths)
        self.message.setVisible(has_content)
        self.empty_state.setVisible(not has_content)
        if has_content:
            self.message.update_content(state, username, avatar_url)
