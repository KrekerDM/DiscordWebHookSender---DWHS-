class Colors:
    BG_PRIMARY = "#141218"
    SURFACE = "#141218"
    SURFACE_DIM = "#0F0D13"
    SURFACE_CONTAINER_LOWEST = "#0F0D13"
    SURFACE_CONTAINER_LOW = "#1D1B20"
    SURFACE_CONTAINER = "#211F26"
    SURFACE_CONTAINER_HIGH = "#2B2930"
    SURFACE_CONTAINER_HIGHEST = "#36333B"
    SURFACE_BRIGHT = "#3B383F"

    BG_SECONDARY = SURFACE_CONTAINER_LOW
    BG_TERTIARY = SURFACE_CONTAINER_LOWEST
    BG_FLOATING = SURFACE_CONTAINER_HIGH
    BG_MODIFIER_HOVER = "rgba(230,224,233,0.08)"
    BG_MODIFIER_SELECTED = "rgba(230,224,233,0.12)"
    BG_ACCENT = SURFACE_CONTAINER_HIGH
    BG_INPUT = SURFACE_CONTAINER_HIGHEST
    BG_CARD = SURFACE_CONTAINER

    TEXT_NORMAL = "#E6E0E9"
    ON_SURFACE = "#E6E0E9"
    TEXT_MUTED = "#ADA9B4"
    ON_SURFACE_VARIANT = "#CAC4D0"
    TEXT_FAINT = "#8A8593"
    TEXT_LINK = "#B9C3FF"
    TEXT_POSITIVE = "#8FDA9C"
    TEXT_DANGER = "#FFB4AB"
    TEXT_WARNING = "#F6C161"
    HEADER_SECONDARY = "#CAC4D0"

    PRIMARY = "#B9C3FF"
    PRIMARY_CONTAINER = "#3D4BC7"
    ON_PRIMARY_CONTAINER = "#FFFFFF"
    PRIMARY_HOVER = "#525FDA"
    PRIMARY_ACTIVE = "#2E3AA8"
    SECONDARY_CONTAINER = "#3F4251"

    BLURPLE = PRIMARY_CONTAINER
    BLURPLE_HOVER = PRIMARY_HOVER
    BLURPLE_ACTIVE = PRIMARY_ACTIVE

    GREEN = "#2E6E3B"
    GREEN_HOVER = "#255A30"
    RED = "#8C1D1B"
    RED_HOVER = "#93000A"
    GREY_BTN = SURFACE_CONTAINER_HIGH
    GREY_BTN_HOVER = SURFACE_BRIGHT

    OUTLINE = "#948F99"
    OUTLINE_VARIANT = "#49454E"
    DIVIDER = OUTLINE_VARIANT
    DIVIDER_SOFT = "#322F37"
    SCROLLBAR_THUMB = "#49454E"
    SCROLLBAR_THUMB_HOVER = "#5C5862"
    SCROLLBAR_TRACK = "transparent"

    BADGE_BOT_BG = "#5865f2"

    FONT_FAMILY = '"Inter", "Segoe UI", "Helvetica Neue", Arial, sans-serif'
    FONT_FAMILY_MONO = 'Consolas, "Courier New", monospace'


def stylesheet() -> str:
    c = Colors
    return f"""
    * {{
        font-family: {c.FONT_FAMILY};
        outline: none;
    }}

    QWidget {{
        color: {c.ON_SURFACE};
        selection-background-color: {c.PRIMARY_CONTAINER};
        selection-color: white;
        font-size: 14px;
    }}

    QMainWindow, QDialog {{
        background-color: {c.SURFACE};
    }}

    QToolTip {{
        background-color: {c.SURFACE_CONTAINER_HIGH};
        color: {c.ON_SURFACE};
        border: 1px solid {c.OUTLINE_VARIANT};
        padding: 6px 10px;
        border-radius: 8px;
        font-size: 12px;
    }}

    QScrollArea {{
        border: none;
        background: transparent;
    }}
    QScrollArea > QWidget > QWidget {{
        background: transparent;
    }}

    QScrollBar:vertical {{
        background: transparent;
        width: 14px;
        margin: 2px 2px 2px 0;
    }}
    QScrollBar::handle:vertical {{
        background: {c.SCROLLBAR_THUMB};
        border-radius: 6px;
        min-height: 32px;
    }}
    QScrollBar::handle:vertical:hover {{
        background: {c.SCROLLBAR_THUMB_HOVER};
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0px;
    }}
    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
        background: none;
    }}
    QScrollBar:horizontal {{
        background: transparent;
        height: 12px;
    }}
    QScrollBar::handle:horizontal {{
        background: {c.SCROLLBAR_THUMB};
        border-radius: 6px;
        min-width: 32px;
    }}
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
        width: 0px;
    }}

    QSplitter::handle {{
        background-color: {c.DIVIDER_SOFT};
        width: 1px;
    }}

    QLabel[class="section-title"] {{
        color: {c.PRIMARY};
        font-size: 12px;
        font-weight: 700;
        padding: 0;
    }}
    QLabel[class="field-label"] {{
        color: {c.ON_SURFACE_VARIANT};
        font-size: 12px;
        font-weight: 600;
    }}
    QLabel[class="hint"] {{
        color: {c.TEXT_FAINT};
        font-size: 12px;
    }}
    QLabel[class="counter"] {{
        color: {c.TEXT_FAINT};
        font-size: 12px;
    }}
    QLabel[class="counter-warn"] {{
        color: {c.TEXT_WARNING};
        font-size: 12px;
    }}
    QLabel[class="counter-danger"] {{
        color: {c.TEXT_DANGER};
        font-size: 12px;
    }}
    QLabel[class="app-title"] {{
        color: {c.ON_SURFACE};
        font-size: 16px;
        font-weight: 700;
    }}
    QLabel[class="app-sub"] {{
        color: {c.TEXT_MUTED};
        font-size: 12px;
    }}

    QFrame[class="divider"] {{
        background-color: {c.DIVIDER_SOFT};
        max-height: 1px;
        min-height: 1px;
        border: none;
    }}
    QFrame[class="card"] {{
        background-color: {c.BG_CARD};
        border-radius: 16px;
        border: 1px solid {c.DIVIDER_SOFT};
    }}
    QFrame[class="topbar"] {{
        background-color: {c.SURFACE_CONTAINER_LOW};
        border-bottom: 1px solid {c.DIVIDER_SOFT};
    }}
    QFrame[class="statusbar"] {{
        background-color: {c.SURFACE_CONTAINER_LOW};
        border-top: 1px solid {c.DIVIDER_SOFT};
    }}
    QFrame[class="navpanel"] {{
        background-color: {c.SURFACE_CONTAINER_LOW};
    }}
    QFrame[class="sidebar"] {{
        background-color: {c.SURFACE_CONTAINER_LOWEST};
    }}
    QFrame[class="preview-panel"] {{
        background-color: #1a1c22;
    }}

    QLineEdit, QPlainTextEdit, QTextEdit {{
        background-color: {c.BG_INPUT};
        color: {c.ON_SURFACE};
        border: none;
        border-bottom: 2px solid {c.OUTLINE_VARIANT};
        border-top-left-radius: 10px;
        border-top-right-radius: 10px;
        padding: 10px 12px;
        font-size: 14px;
    }}
    QLineEdit:hover, QPlainTextEdit:hover {{
        background-color: {c.SURFACE_BRIGHT};
    }}
    QLineEdit:focus, QPlainTextEdit:focus, QTextEdit:focus {{
        border-bottom: 2px solid {c.PRIMARY};
    }}
    QLineEdit:disabled, QPlainTextEdit:disabled {{
        color: {c.TEXT_FAINT};
    }}
    QLineEdit[error="true"], QPlainTextEdit[error="true"] {{
        border-bottom: 2px solid {c.TEXT_DANGER};
    }}

    QSpinBox {{
        background-color: {c.BG_INPUT};
        border: none;
        border-bottom: 2px solid {c.OUTLINE_VARIANT};
        border-top-left-radius: 10px;
        border-top-right-radius: 10px;
        padding: 6px 10px;
        color: {c.ON_SURFACE};
    }}
    QSpinBox:focus {{ border-bottom: 2px solid {c.PRIMARY}; }}

    QComboBox {{
        background-color: {c.BG_INPUT};
        border: none;
        border-bottom: 2px solid {c.OUTLINE_VARIANT};
        border-top-left-radius: 10px;
        border-top-right-radius: 10px;
        padding: 9px 12px;
        color: {c.ON_SURFACE};
        font-size: 14px;
    }}
    QComboBox:hover {{ background-color: {c.SURFACE_BRIGHT}; }}
    QComboBox::drop-down {{ border: none; width: 26px; }}
    QComboBox QAbstractItemView {{
        background-color: {c.SURFACE_CONTAINER_HIGH};
        color: {c.ON_SURFACE};
        border: 1px solid {c.OUTLINE_VARIANT};
        border-radius: 12px;
        selection-background-color: {c.PRIMARY_CONTAINER};
        padding: 6px;
        outline: none;
    }}

    QCheckBox {{
        color: {c.ON_SURFACE};
        font-size: 14px;
        spacing: 10px;
    }}
    QCheckBox::indicator {{
        width: 20px;
        height: 20px;
        border-radius: 5px;
        border: 2px solid {c.OUTLINE};
        background-color: transparent;
    }}
    QCheckBox::indicator:hover {{
        border-color: {c.PRIMARY};
    }}
    QCheckBox::indicator:checked {{
        border-color: {c.PRIMARY};
        background-color: {c.PRIMARY};
        image: none;
    }}

    QPushButton {{
        border: none;
        border-radius: 999px;
        padding: 10px 20px;
        font-size: 13px;
        font-weight: 600;
        background-color: {c.SURFACE_CONTAINER_HIGH};
        color: {c.ON_SURFACE};
    }}
    QPushButton:hover {{ background-color: {c.SURFACE_BRIGHT}; }}
    QPushButton:disabled {{ background-color: {c.SURFACE_CONTAINER}; color: {c.TEXT_FAINT}; }}

    QPushButton[class="primary"] {{
        background-color: {c.PRIMARY_CONTAINER};
        color: {c.ON_PRIMARY_CONTAINER};
        padding: 11px 24px;
    }}
    QPushButton[class="primary"]:hover {{ background-color: {c.PRIMARY_HOVER}; }}
    QPushButton[class="primary"]:pressed {{ background-color: {c.PRIMARY_ACTIVE}; }}

    QPushButton[class="danger"] {{
        background-color: transparent;
        color: {c.TEXT_DANGER};
        border: 1px solid {c.OUTLINE_VARIANT};
    }}
    QPushButton[class="danger"]:hover {{ background-color: {c.RED}; color: white; border-color: transparent; }}

    QPushButton[class="success"] {{
        background-color: {c.GREEN};
        color: white;
    }}
    QPushButton[class="success"]:hover {{ background-color: {c.GREEN_HOVER}; }}

    QPushButton[class="ghost"] {{
        background-color: transparent;
        color: {c.ON_SURFACE_VARIANT};
        padding: 8px 14px;
        font-weight: 500;
    }}
    QPushButton[class="ghost"]:hover {{
        background-color: {c.BG_MODIFIER_HOVER};
        color: {c.ON_SURFACE};
    }}

    QPushButton[class="link"] {{
        background-color: transparent;
        color: {c.TEXT_LINK};
        font-weight: 500;
        padding: 2px;
        border-radius: 4px;
    }}
    QPushButton[class="link"]:hover {{ text-decoration: underline; }}

    QPushButton[class="icon"] {{
        background-color: transparent;
        border-radius: 18px;
        padding: 4px;
        color: {c.ON_SURFACE_VARIANT};
    }}
    QPushButton[class="icon"]:hover {{
        background-color: {c.BG_MODIFIER_HOVER};
        color: {c.ON_SURFACE};
    }}

    QPushButton[class="navitem"] {{
        background-color: transparent;
        color: {c.ON_SURFACE_VARIANT};
        text-align: left;
        padding: 12px 16px;
        border-radius: 24px;
        font-weight: 600;
        font-size: 14px;
    }}
    QPushButton[class="navitem"]:hover {{
        background-color: {c.BG_MODIFIER_HOVER};
        color: {c.ON_SURFACE};
    }}
    QPushButton[class="navitem-active"] {{
        background-color: {c.SECONDARY_CONTAINER};
        color: {c.ON_SURFACE};
        text-align: left;
        padding: 12px 16px;
        border-radius: 24px;
        font-weight: 700;
        font-size: 14px;
    }}

    QPushButton[class="profile-item"] {{
        background-color: transparent;
        color: {c.ON_SURFACE};
        text-align: left;
        padding: 8px;
        border-radius: 16px;
        font-weight: 500;
    }}
    QPushButton[class="profile-item"]:hover {{
        background-color: {c.BG_MODIFIER_HOVER};
    }}
    QPushButton[class="profile-item-active"] {{
        background-color: {c.SECONDARY_CONTAINER};
        color: {c.ON_SURFACE};
        text-align: left;
        padding: 8px;
        border-radius: 16px;
        font-weight: 600;
    }}

    QListWidget {{
        background-color: {c.SURFACE_CONTAINER_HIGH};
        color: {c.ON_SURFACE};
        border: 1px solid {c.OUTLINE_VARIANT};
        border-radius: 12px;
        padding: 4px;
        outline: none;
    }}
    QListWidget::item {{
        background-color: transparent;
        border-radius: 10px;
        padding: 2px;
        margin: 2px;
    }}
    QListWidget::item:selected, QListWidget::item:hover {{
        background-color: {c.BG_MODIFIER_HOVER};
    }}

    QMenu {{
        background-color: {c.SURFACE_CONTAINER_HIGH};
        border: 1px solid {c.OUTLINE_VARIANT};
        border-radius: 12px;
        padding: 6px;
    }}
    QMenu::item {{
        padding: 9px 14px;
        border-radius: 8px;
        color: {c.ON_SURFACE};
        font-size: 13px;
    }}
    QMenu::item:selected {{
        background-color: {c.PRIMARY_CONTAINER};
        color: white;
    }}
    QMenu::separator {{
        height: 1px;
        background: {c.DIVIDER_SOFT};
        margin: 4px 8px;
    }}

    QMessageBox {{
        background-color: {c.SURFACE_CONTAINER_HIGH};
    }}

    QTabWidget::pane {{
        border: none;
    }}

    QStatusBar {{
        background-color: {c.SURFACE_CONTAINER_LOW};
        color: {c.TEXT_MUTED};
    }}
    """
