"""Client for interacting with the DeepSeek API."""
from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from typing import Callable, Dict, Optional

import urllib.error
import urllib.request

from .data_loader import Segment


DEFAULT_BASE_URL = "https://api.deepseek.com/v1/chat/completions"


class DeepSeekError(RuntimeError):
    """Raised when the DeepSeek API returns an error."""


@dataclass
class DeepSeekClient:
    api_key: Optional[str]
    base_url: str = DEFAULT_BASE_URL
    enabled: bool = True
    timeout: float = 30.0
    max_retries: int = 3
    backoff_factor: float = 2.0
    rate_limit_per_minute: int = 60
    _request_func: Callable[[urllib.request.Request], urllib.response.addinfourl] = field(
        default=urllib.request.urlopen
    )

    def __post_init__(self) -> None:
        self._last_request_timestamp: float = 0.0
        self._min_interval = 60.0 / max(self.rate_limit_per_minute, 1)

    def _rate_limit(self) -> None:
        now = time.time()
        elapsed = now - self._last_request_timestamp
        if elapsed < self._min_interval:
            time.sleep(self._min_interval - elapsed)
        self._last_request_timestamp = time.time()

    def translate_segment(self, segment: Segment, context: str) -> str:
        if not self.enabled:
            return f"[DRY-RUN] {segment.translation or segment.root}"

        payload = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": "You are a professional Buddhist text translator."},
                {
                    "role": "user",
                    "content": (
                        "Translate the following Pali segment into Chinese.\n"
                        f"Context: {context}\n"
                        f"Segment ({segment.segment_id}): {segment.root}"
                    ),
                },
            ],
        }
        return self._post(payload)

    def _post(self, payload: Dict[str, object]) -> str:
        if not self.api_key:
            raise DeepSeekError("API key is required when the client is enabled.")

        body = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            self.base_url,
            data=body,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
            method="POST",
        )

        for attempt in range(1, self.max_retries + 1):
            try:
                self._rate_limit()
                with self._request_func(request, timeout=self.timeout) as response:
                    if response.status != 200:
                        raise DeepSeekError(f"HTTP {response.status}: {response.read().decode('utf-8')}")
                    payload = json.load(response)
                    return self._extract_message(payload)
            except (urllib.error.HTTPError, urllib.error.URLError, DeepSeekError) as exc:  # pragma: no cover - network errors
                if attempt == self.max_retries:
                    raise DeepSeekError(str(exc))
                sleep_time = self.backoff_factor ** (attempt - 1)
                time.sleep(sleep_time)
        raise DeepSeekError("Failed to obtain translation after retries.")

    @staticmethod
    def _extract_message(payload: Dict[str, object]) -> str:
        choices = payload.get("choices") if isinstance(payload, dict) else None
        if not choices:
            raise DeepSeekError("Response payload missing 'choices'.")
        message = choices[0].get("message") if isinstance(choices[0], dict) else None
        if not message or not isinstance(message, dict):
            raise DeepSeekError("Response payload missing message content.")
        content = message.get("content")
        if not isinstance(content, str):
            raise DeepSeekError("Message content must be a string.")
        return content.strip()
