from __future__ import annotations

import os
import time
import uuid
from dataclasses import dataclass, field, asdict
from app.config import (
    DEFAULT_EMBED_COLOR, MAX_CONTENT_LEN, MAX_USERNAME_LEN, MAX_EMBED_TITLE,
    MAX_EMBED_DESCRIPTION, MAX_AUTHOR_NAME, MAX_FOOTER_TEXT, MAX_FIELD_NAME,
    MAX_FIELD_VALUE, MAX_EMBED_FIELDS,
)


def _text(value) -> str:
    return value if isinstance(value, str) else ""


def _clip(text, limit: int) -> str:
    return _text(text)[:limit]


def _dict(value) -> dict:
    return value if isinstance(value, dict) else {}


def _bool(d: dict, key: str, default: bool) -> bool:
    value = d.get(key)
    return default if value is None else bool(value)


def _clamp_color(value) -> int:
    try:
        value = int(value)
    except (TypeError, ValueError):
        return DEFAULT_EMBED_COLOR
    return max(0, min(0xFFFFFF, value))


@dataclass
class EmbedField:
    name: str = ""
    value: str = ""
    inline: bool = True

    def to_dict(self) -> dict:
        return {"name": self.name, "value": self.value, "inline": self.inline}

    @staticmethod
    def from_dict(d: dict) -> "EmbedField":
        return EmbedField(
            name=_clip(d.get("name"), MAX_FIELD_NAME),
            value=_clip(d.get("value"), MAX_FIELD_VALUE),
            inline=_bool(d, "inline", True),
        )


@dataclass
class Embed:
    title: str = ""
    url: str = ""
    description: str = ""
    color: int = DEFAULT_EMBED_COLOR
    use_timestamp: bool = False
    author_name: str = ""
    author_url: str = ""
    author_icon: str = ""
    thumbnail_url: str = ""
    image_url: str = ""
    footer_text: str = ""
    footer_icon: str = ""
    fields: list[EmbedField] = field(default_factory=list)

    def is_empty(self) -> bool:
        return not any([
            self.title, self.description, self.author_name, self.footer_text,
            self.image_url, self.thumbnail_url, self.fields, self.url,
        ])

    def to_payload(self) -> dict:
        d: dict = {}
        if self.title.strip():
            d["title"] = self.title.strip()
        if self.url.strip():
            d["url"] = self.url.strip()
        if self.description.strip():
            d["description"] = self.description.strip()
        if self.color is not None:
            d["color"] = self.color
        if self.use_timestamp:
            d["timestamp"] = time.strftime("%Y-%m-%dT%H:%M:%S.000Z", time.gmtime())
        if self.author_name.strip():
            author = {"name": self.author_name.strip()}
            if self.author_url.strip():
                author["url"] = self.author_url.strip()
            if self.author_icon.strip():
                author["icon_url"] = self.author_icon.strip()
            d["author"] = author
        if self.thumbnail_url.strip():
            d["thumbnail"] = {"url": self.thumbnail_url.strip()}
        if self.image_url.strip():
            d["image"] = {"url": self.image_url.strip()}
        if self.footer_text.strip():
            footer = {"text": self.footer_text.strip()}
            if self.footer_icon.strip():
                footer["icon_url"] = self.footer_icon.strip()
            d["footer"] = footer
        fields_payload = [f.to_dict() for f in self.fields if f.name.strip() or f.value.strip()]
        if fields_payload:
            d["fields"] = fields_payload
        return d

    def to_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def from_dict(d: dict) -> "Embed":
        e = Embed(
            title=_clip(d.get("title"), MAX_EMBED_TITLE),
            url=_text(d.get("url")),
            description=_clip(d.get("description"), MAX_EMBED_DESCRIPTION),
            color=_clamp_color(d.get("color", DEFAULT_EMBED_COLOR)),
            use_timestamp=_bool(d, "use_timestamp", False),
            author_name=_clip(d.get("author_name"), MAX_AUTHOR_NAME),
            author_url=_text(d.get("author_url")),
            author_icon=_text(d.get("author_icon")),
            thumbnail_url=_text(d.get("thumbnail_url")),
            image_url=_text(d.get("image_url")),
            footer_text=_clip(d.get("footer_text"), MAX_FOOTER_TEXT),
            footer_icon=_text(d.get("footer_icon")),
        )
        e.fields = [EmbedField.from_dict(f) for f in (d.get("fields") or []) if isinstance(f, dict)][:MAX_EMBED_FIELDS]
        return e

    @staticmethod
    def from_discord_json(d: dict) -> "Embed":
        e = Embed(
            title=_clip(d.get("title"), MAX_EMBED_TITLE),
            url=_text(d.get("url")),
            description=_clip(d.get("description"), MAX_EMBED_DESCRIPTION),
            color=_clamp_color(d.get("color") or DEFAULT_EMBED_COLOR),
        )
        author = _dict(d.get("author"))
        e.author_name = _clip(author.get("name"), MAX_AUTHOR_NAME)
        e.author_url = _text(author.get("url"))
        e.author_icon = _text(author.get("icon_url"))
        footer = _dict(d.get("footer"))
        e.footer_text = _clip(footer.get("text"), MAX_FOOTER_TEXT)
        e.footer_icon = _text(footer.get("icon_url"))
        thumb = _dict(d.get("thumbnail"))
        e.thumbnail_url = _text(thumb.get("url"))
        img = _dict(d.get("image"))
        e.image_url = _text(img.get("url"))
        e.use_timestamp = bool(d.get("timestamp"))
        e.fields = [EmbedField.from_dict(f) for f in (d.get("fields") or []) if isinstance(f, dict)][:MAX_EMBED_FIELDS]
        return e


@dataclass
class WebhookProfile:
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    name: str = "New Webhook"
    url: str = ""
    default_username: str = ""
    default_avatar: str = ""
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def from_dict(d: dict) -> "WebhookProfile":
        return WebhookProfile(
            id=_text(d.get("id")) or uuid.uuid4().hex[:12],
            name=_text(d.get("name")) or "New Webhook",
            url=_text(d.get("url")),
            default_username=_text(d.get("default_username")),
            default_avatar=_text(d.get("default_avatar")),
            created_at=d.get("created_at") if isinstance(d.get("created_at"), (int, float)) else time.time(),
        )


@dataclass
class MessageState:
    content: str = ""
    username: str = ""
    avatar_url: str = ""
    tts: bool = False
    thread_name: str = ""
    embeds: list[Embed] = field(default_factory=list)
    file_paths: list[str] = field(default_factory=list)

    def to_payload(self) -> dict:
        payload: dict = {}
        if self.content.strip():
            payload["content"] = self.content
        if self.username.strip():
            payload["username"] = self.username.strip()
        if self.avatar_url.strip():
            payload["avatar_url"] = self.avatar_url.strip()
        if self.tts:
            payload["tts"] = True
        if self.thread_name.strip():
            payload["thread_name"] = self.thread_name.strip()
        embeds_payload = [e.to_payload() for e in self.embeds if not e.is_empty()]
        if embeds_payload:
            payload["embeds"] = embeds_payload
        payload["allowed_mentions"] = {"parse": ["users", "roles", "everyone"]}
        return payload

    def to_dict(self) -> dict:
        return {
            "content": self.content,
            "username": self.username,
            "avatar_url": self.avatar_url,
            "tts": self.tts,
            "thread_name": self.thread_name,
            "embeds": [e.to_dict() for e in self.embeds],
            "file_paths": list(self.file_paths),
        }

    @staticmethod
    def from_dict(d: dict) -> "MessageState":
        m = MessageState(
            content=_clip(d.get("content"), MAX_CONTENT_LEN),
            username=_clip(d.get("username"), MAX_USERNAME_LEN),
            avatar_url=_text(d.get("avatar_url")),
            tts=_bool(d, "tts", False),
            thread_name=_text(d.get("thread_name")),
        )
        m.embeds = [Embed.from_dict(e) for e in (d.get("embeds") or []) if isinstance(e, dict)]
        m.file_paths = [p for p in (d.get("file_paths") or []) if isinstance(p, str) and os.path.isfile(p)]
        return m


@dataclass
class HistoryEntry:
    message_id: str = ""
    profile_id: str = ""
    summary: str = ""
    sent_at: float = field(default_factory=time.time)
    payload: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def from_dict(d: dict) -> "HistoryEntry":
        return HistoryEntry(
            message_id=d.get("message_id", ""),
            profile_id=d.get("profile_id", ""),
            summary=d.get("summary", ""),
            sent_at=d.get("sent_at", time.time()),
            payload=d.get("payload", {}),
        )
