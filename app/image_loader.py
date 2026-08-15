from __future__ import annotations

from typing import Callable

from PySide6.QtCore import QObject, QUrl, Qt
from PySide6.QtGui import QPixmap, QPainter, QPainterPath
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply


def circular_pixmap(source: QPixmap, size: int) -> QPixmap:
    scaled = source.scaled(size, size, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
    result = QPixmap(size, size)
    result.fill(Qt.transparent)
    painter = QPainter(result)
    painter.setRenderHint(QPainter.Antialiasing)
    path = QPainterPath()
    path.addEllipse(0, 0, size, size)
    painter.setClipPath(path)
    x = (scaled.width() - size) // 2
    y = (scaled.height() - size) // 2
    painter.drawPixmap(-x, -y, scaled)
    painter.end()
    return result


def rounded_pixmap(source: QPixmap, max_width: int, max_height: int, radius: int = 6) -> QPixmap:
    scaled = source.scaled(max_width, max_height, Qt.KeepAspectRatio, Qt.SmoothTransformation)
    result = QPixmap(scaled.size())
    result.fill(Qt.transparent)
    painter = QPainter(result)
    painter.setRenderHint(QPainter.Antialiasing)
    path = QPainterPath()
    path.addRoundedRect(0, 0, scaled.width(), scaled.height(), radius, radius)
    painter.setClipPath(path)
    painter.drawPixmap(0, 0, scaled)
    painter.end()
    return result


class ImageLoader(QObject):
    _instance: "ImageLoader | None" = None

    def __init__(self):
        super().__init__()
        self._manager = QNetworkAccessManager(self)
        self._cache: dict[str, QPixmap] = {}
        self._pending: dict[str, list[Callable[[QPixmap], None]]] = {}

    @classmethod
    def instance(cls) -> "ImageLoader":
        if cls._instance is None:
            cls._instance = ImageLoader()
        return cls._instance

    def fetch(self, url: str, callback: Callable[[QPixmap], None]) -> None:
        url = (url or "").strip()
        if not url or not url.startswith(("http://", "https://")):
            return
        if url in self._cache:
            callback(self._cache[url])
            return
        if url in self._pending:
            self._pending[url].append(callback)
            return
        self._pending[url] = [callback]
        request = QNetworkRequest(QUrl(url))
        request.setTransferTimeout(15000)
        reply = self._manager.get(request)
        reply.finished.connect(lambda: self._on_finished(url, reply))

    def _on_finished(self, url: str, reply: QNetworkReply) -> None:
        callbacks = self._pending.pop(url, [])
        if reply.error() == QNetworkReply.NoError:
            data = reply.readAll()
            pixmap = QPixmap()
            if pixmap.loadFromData(data):
                self._cache[url] = pixmap
                for cb in callbacks:
                    cb(pixmap)
        reply.deleteLater()
