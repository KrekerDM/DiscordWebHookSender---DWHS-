from __future__ import annotations

import json
import time
from pathlib import Path

from app.config import PROFILES_FILE, HISTORY_FILE, SETTINGS_FILE, TEMPLATES_DIR
from app.models import WebhookProfile, HistoryEntry, MessageState


def _read_json(path: Path, default):
    if not path.exists():
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return default


def _write_json(path: Path, data) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    tmp.replace(path)


def load_profiles() -> list[WebhookProfile]:
    raw = _read_json(PROFILES_FILE, [])
    return [WebhookProfile.from_dict(d) for d in raw]


def save_profiles(profiles: list[WebhookProfile]) -> None:
    _write_json(PROFILES_FILE, [p.to_dict() for p in profiles])


def load_history() -> list[HistoryEntry]:
    raw = _read_json(HISTORY_FILE, [])
    return [HistoryEntry.from_dict(d) for d in raw]


def save_history(entries: list[HistoryEntry]) -> None:
    trimmed = entries[-200:]
    _write_json(HISTORY_FILE, [e.to_dict() for e in trimmed])


def load_settings() -> dict:
    return _read_json(SETTINGS_FILE, {})


def save_settings(settings: dict) -> None:
    _write_json(SETTINGS_FILE, settings)


def list_templates() -> list[str]:
    if not TEMPLATES_DIR.exists():
        return []
    return sorted(p.stem for p in TEMPLATES_DIR.glob("*.json"))


def save_template(name: str, state: MessageState) -> Path:
    safe = "".join(c for c in name if c.isalnum() or c in " _-").strip() or f"template_{int(time.time())}"
    path = TEMPLATES_DIR / f"{safe}.json"
    _write_json(path, state.to_dict())
    return path


def load_template(name: str) -> MessageState | None:
    path = TEMPLATES_DIR / f"{name}.json"
    raw = _read_json(path, None)
    if raw is None:
        return None
    return MessageState.from_dict(raw)


def delete_template(name: str) -> None:
    path = TEMPLATES_DIR / f"{name}.json"
    if path.exists():
        path.unlink()
