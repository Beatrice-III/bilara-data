"""Simple file-backed cache for translations."""
from __future__ import annotations

import json
import threading
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from typing import Dict, Optional, Tuple


@dataclass
class CacheKey:
    segment_id: str
    context_hash: str

    def to_tuple(self) -> Tuple[str, str]:
        return (self.segment_id, self.context_hash)


class TranslationCache:
    """File-backed cache mapping segment/context to translated text."""

    def __init__(self, path: Path) -> None:
        self.path = Path(path)
        self._lock = threading.Lock()
        self._data: Dict[str, Dict[str, str]] = {}
        self._load()

    def _load(self) -> None:
        if self.path.exists():
            with self.path.open("r", encoding="utf-8") as handle:
                payload = json.load(handle)
            if isinstance(payload, dict):
                self._data = {
                    segment_id: dict(values)
                    for segment_id, values in payload.items()
                    if isinstance(values, dict)
                }

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("w", encoding="utf-8") as handle:
            json.dump(self._data, handle, ensure_ascii=False, indent=2)

    @staticmethod
    def compute_context_hash(context: str) -> str:
        digest = sha256(context.encode("utf-8")).hexdigest()
        return digest

    def get(self, segment_id: str, context: str) -> Optional[str]:
        context_hash = self.compute_context_hash(context)
        with self._lock:
            return self._data.get(segment_id, {}).get(context_hash)

    def set(self, segment_id: str, context: str, translation: str) -> None:
        context_hash = self.compute_context_hash(context)
        with self._lock:
            segment_cache = self._data.setdefault(segment_id, {})
            segment_cache[context_hash] = translation
            self._save()
