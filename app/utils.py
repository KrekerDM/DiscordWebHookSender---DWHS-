from __future__ import annotations

import re
import time
from html import escape as _escape

_CODE_BLOCK_RE = re.compile(r"```(?:\w*\n)?(.*?)```", re.DOTALL)
_INLINE_CODE_RE = re.compile(r"`([^`\n]+?)`")
_BOLD_ITALIC_RE = re.compile(r"\*\*\*(.+?)\*\*\*", re.DOTALL)
_BOLD_RE = re.compile(r"\*\*(.+?)\*\*", re.DOTALL)
_UNDERLINE_RE = re.compile(r"__(.+?)__", re.DOTALL)
_ITALIC_STAR_RE = re.compile(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)", re.DOTALL)
_ITALIC_US_RE = re.compile(r"(?<!_)_(?!_)(.+?)(?<!_)_(?!_)", re.DOTALL)
_STRIKE_RE = re.compile(r"~~(.+?)~~", re.DOTALL)
_SPOILER_RE = re.compile(r"\|\|(.+?)\|\|", re.DOTALL)
_QUOTE_RE = re.compile(r"^&gt;\s?(.*)$", re.MULTILINE)
_LINK_RE = re.compile(r"\[([^\]]+)\]\((https?://[^\s)]+)\)")
_BARE_URL_RE = re.compile(r"(https?://[^\s<]+)")
_MENTION_USER_RE = re.compile(r"&lt;@!?(\d+)&gt;")
_MENTION_ROLE_RE = re.compile(r"&lt;@&amp;(\d+)&gt;")
_MENTION_CHANNEL_RE = re.compile(r"&lt;#(\d+)&gt;")
_CUSTOM_EMOJI_RE = re.compile(r"&lt;a?:(\w+):(\d+)&gt;")

_PLACEHOLDER = "\x00{}\x00"


def _stash(store: list, html: str) -> str:
    store.append(html)
    return _PLACEHOLDER.format(len(store) - 1)


def _unstash(text: str, store: list) -> str:
    for i, html in enumerate(store):
        text = text.replace(_PLACEHOLDER.format(i), html)
    return text


def markdown_to_html(text: str, allow_links: bool = False) -> str:
    if not text:
        return ""
    store: list[str] = []
    escaped = _escape(text)

    def _code_block(m: re.Match) -> str:
        content = _escape(m.group(1).strip("\n"))
        return _stash(store, f'<span style="font-family:Consolas,monospace;background-color:#2b2d31;">&nbsp;{content}&nbsp;</span>')

    escaped = _CODE_BLOCK_RE.sub(_code_block, escaped)

    def _inline_code(m: re.Match) -> str:
        return _stash(store, f'<span style="font-family:Consolas,monospace;background-color:#2b2d31;">&nbsp;{m.group(1)}&nbsp;</span>')

    escaped = _INLINE_CODE_RE.sub(_inline_code, escaped)

    escaped = _MENTION_USER_RE.sub(lambda m: _stash(store, '<span style="background-color:rgba(88,101,242,0.3);color:#c9cdfb;border-radius:3px;padding:0 2px;">@user</span>'), escaped)
    escaped = _MENTION_ROLE_RE.sub(lambda m: _stash(store, '<span style="background-color:rgba(88,101,242,0.3);color:#c9cdfb;border-radius:3px;padding:0 2px;">@role</span>'), escaped)
    escaped = _MENTION_CHANNEL_RE.sub(lambda m: _stash(store, '<span style="background-color:rgba(88,101,242,0.3);color:#c9cdfb;border-radius:3px;padding:0 2px;">#channel</span>'), escaped)
    escaped = _CUSTOM_EMOJI_RE.sub(lambda m: _stash(store, f':{m.group(1)}:'), escaped)

    escaped = _BOLD_ITALIC_RE.sub(r"<b><i>\1</i></b>", escaped)
    escaped = _BOLD_RE.sub(r"<b>\1</b>", escaped)
    escaped = _UNDERLINE_RE.sub(r"<u>\1</u>", escaped)
    escaped = _STRIKE_RE.sub(r"<s>\1</s>", escaped)
    escaped = _ITALIC_STAR_RE.sub(r"<i>\1</i>", escaped)
    escaped = _ITALIC_US_RE.sub(r"<i>\1</i>", escaped)

    def _spoiler(m: re.Match) -> str:
        return _stash(store, f'<span style="background-color:#1a1b1e;color:#1a1b1e;border-radius:3px;">{m.group(1)}</span>')

    escaped = _SPOILER_RE.sub(_spoiler, escaped)
    escaped = _QUOTE_RE.sub(r'<span style="color:#949ba4;">&#9474;</span> \1', escaped)

    if allow_links:
        escaped = _LINK_RE.sub(lambda m: _stash(store, f'<a href="{m.group(2)}" style="color:#00a8fc;text-decoration:none;">{m.group(1)}</a>'), escaped)

    escaped = _BARE_URL_RE.sub(lambda m: _stash(store, f'<a href="{m.group(1)}" style="color:#00a8fc;text-decoration:none;">{m.group(1)}</a>'), escaped)

    escaped = escaped.replace("\n", "<br>")
    escaped = _unstash(escaped, store)
    return escaped


def hex_to_int(hex_str: str) -> int | None:
    hex_str = hex_str.strip().lstrip("#")
    if not re.fullmatch(r"[0-9a-fA-F]{6}", hex_str):
        return None
    return int(hex_str, 16)


def int_to_hex(value: int) -> str:
    return f"#{value:06X}"


def now_clock_time() -> str:
    return time.strftime("%H:%M", time.localtime())


def truncate(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "…"


def is_valid_url(url: str) -> bool:
    if not url:
        return True
    return bool(re.match(r"^https?://\S+\.\S+", url.strip()))


def bytes_human(n: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024:
            return f"{n:.0f}{unit}" if unit == "B" else f"{n:.1f}{unit}"
        n /= 1024
    return f"{n:.1f}TB"
