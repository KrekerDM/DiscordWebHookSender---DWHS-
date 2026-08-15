from __future__ import annotations

import os
import re
import json as jsonlib
from typing import Callable, Optional

import requests
from PySide6.QtCore import QThread, Signal

from app.config import WEBHOOK_URL_RE
from app.i18n import tr

API_BASE = "https://discord.com/api/v10/webhooks"
TIMEOUT = 15


class DiscordAPIError(Exception):
    def __init__(self, message: str, status: Optional[int] = None, retry_after: Optional[float] = None,
                 detail: Optional[str] = None):
        super().__init__(message)
        self.message = message
        self.status = status
        self.retry_after = retry_after
        self.detail = detail


def parse_webhook_url(url: str) -> tuple[str, str]:
    match = re.match(WEBHOOK_URL_RE, url.strip())
    if not match:
        raise DiscordAPIError(tr("api.invalid_webhook_url"))
    return match.group(1), match.group(2)


def _endpoint(webhook_id: str, token: str, *, message_id: str | None = None,
              thread_id: str | None = None, wait: bool = False) -> str:
    url = f"{API_BASE}/{webhook_id}/{token}"
    if message_id:
        url += f"/messages/{message_id}"
    params = []
    if wait:
        params.append("wait=true")
    if thread_id:
        params.append(f"thread_id={thread_id}")
    if params:
        url += "?" + "&".join(params)
    return url


def _raise_for_response(resp: requests.Response) -> None:
    if resp.status_code == 429:
        try:
            data = resp.json()
        except ValueError:
            data = {}
        retry_after = data.get("retry_after", 1.0)
        raise DiscordAPIError(
            tr("api.rate_limited", seconds=retry_after),
            status=429, retry_after=retry_after,
        )
    if resp.status_code == 401:
        raise DiscordAPIError(tr("api.unauthorized"), status=401)
    if resp.status_code == 404:
        raise DiscordAPIError(tr("api.not_found"), status=404)
    if resp.status_code >= 400:
        try:
            data = resp.json()
            short_message = data.get("message") or tr("api.unknown_error_body")
            detail = jsonlib.dumps(data, ensure_ascii=False, indent=2)
        except ValueError:
            short_message = tr("api.unknown_error_body")
            detail = resp.text
        raise DiscordAPIError(
            tr("api.generic_error", code=resp.status_code, message=short_message),
            status=resp.status_code, detail=detail,
        )


def get_webhook_info(url: str) -> dict:
    webhook_id, token = parse_webhook_url(url)
    resp = requests.get(_endpoint(webhook_id, token), timeout=TIMEOUT)
    _raise_for_response(resp)
    return resp.json()


def _send_with_payload(method: Callable, endpoint: str, payload: dict, file_paths: list[str] | None) -> dict:
    if file_paths:
        files = {}
        opened = []
        try:
            for i, path in enumerate(file_paths):
                fh = open(path, "rb")
                opened.append(fh)
                files[f"files[{i}]"] = (os.path.basename(path), fh)
            data = {"payload_json": jsonlib.dumps(payload)}
            resp = method(endpoint, data=data, files=files, timeout=60)
        finally:
            for fh in opened:
                fh.close()
    else:
        resp = method(endpoint, json=payload, timeout=TIMEOUT)

    _raise_for_response(resp)
    if resp.text:
        return resp.json()
    return {}


def send_message(url: str, payload: dict, file_paths: list[str] | None = None,
                  thread_id: str | None = None) -> dict:
    webhook_id, token = parse_webhook_url(url)
    endpoint = _endpoint(webhook_id, token, wait=True, thread_id=thread_id)
    return _send_with_payload(requests.post, endpoint, payload, file_paths)


def edit_message(url: str, message_id: str, payload: dict, file_paths: list[str] | None = None,
                  thread_id: str | None = None) -> dict:
    webhook_id, token = parse_webhook_url(url)
    endpoint = _endpoint(webhook_id, token, message_id=message_id, thread_id=thread_id)
    return _send_with_payload(requests.patch, endpoint, payload, file_paths)


def delete_message(url: str, message_id: str, thread_id: str | None = None) -> None:
    webhook_id, token = parse_webhook_url(url)
    endpoint = _endpoint(webhook_id, token, message_id=message_id, thread_id=thread_id)
    resp = requests.delete(endpoint, timeout=TIMEOUT)
    _raise_for_response(resp)


class ApiWorker(QThread):
    succeeded = Signal(object)
    failed = Signal(str, str)

    def __init__(self, func: Callable, *args, **kwargs):
        super().__init__()
        self._func = func
        self._args = args
        self._kwargs = kwargs

    def run(self) -> None:
        try:
            result = self._func(*self._args, **self._kwargs)
            self.succeeded.emit(result)
        except DiscordAPIError as e:
            self.failed.emit(e.message, e.detail or "")
        except requests.RequestException as e:
            self.failed.emit(tr("api.network_error", error=e), "")
        except Exception as e:
            self.failed.emit(tr("api.unexpected_error", error=e), "")
