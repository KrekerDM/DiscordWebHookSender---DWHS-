import sys
from pathlib import Path

APP_NAME = "Discord Webhook Sender"
APP_VERSION = "1.0.0"
AUTHOR_NAME = "KrekerDM"
AUTHOR_URL = "https://github.com/KrekerDM"

_FROZEN = getattr(sys, "frozen", False)

BASE_DIR = Path(sys.executable).resolve().parent if _FROZEN else Path(__file__).resolve().parent.parent
RESOURCE_DIR = Path(getattr(sys, "_MEIPASS", BASE_DIR)) if _FROZEN else BASE_DIR
DATA_DIR = BASE_DIR / "data"
TEMPLATES_DIR = DATA_DIR / "templates"
PROFILES_FILE = DATA_DIR / "profiles.json"
HISTORY_FILE = DATA_DIR / "history.json"
SETTINGS_FILE = DATA_DIR / "settings.json"

DATA_DIR.mkdir(parents=True, exist_ok=True)
TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)

MAX_CONTENT_LEN = 2000
MAX_EMBEDS = 10
MAX_EMBED_TITLE = 256
MAX_EMBED_DESCRIPTION = 4096
MAX_EMBED_FIELDS = 25
MAX_FIELD_NAME = 256
MAX_FIELD_VALUE = 1024
MAX_FOOTER_TEXT = 2048
MAX_AUTHOR_NAME = 256
MAX_TOTAL_EMBED = 6000
MAX_USERNAME_LEN = 80
MAX_FILE_SIZE = 25 * 1024 * 1024
MAX_FILES = 10

DEFAULT_EMBED_COLOR = 0x5865F2

WEBHOOK_URL_RE = r"^https://(?:ptb\.|canary\.)?discord(?:app)?\.com/api/webhooks/(\d+)/([\w-]+)(?:/(?:slack|github))?/?$"
