import sys

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFont, QFontDatabase

from app import storage, i18n
from app.config import RESOURCE_DIR
from app.theme import stylesheet
from app.main_window import MainWindow


def _load_app_font() -> str:
    font_path = RESOURCE_DIR / "assets" / "fonts" / "Inter.ttf"
    if font_path.exists():
        font_id = QFontDatabase.addApplicationFont(str(font_path))
        families = QFontDatabase.applicationFontFamilies(font_id)
        if families:
            return families[0]
    return "Segoe UI"


def main() -> None:
    app = QApplication(sys.argv)
    app.setApplicationName("Discord Webhook Sender")
    family = _load_app_font()
    font = QFont(family, 10)
    app.setFont(font)
    app.setStyleSheet(stylesheet())

    settings = storage.load_settings()
    i18n.set_language(settings.get("language", i18n.DEFAULT_LANG))

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
