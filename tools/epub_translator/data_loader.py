"""Load Bilara JSON files and align segments."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class Segment:
    """Represents a single textual segment across all sources."""

    segment_id: str
    root: str
    translation: str
    comment: str

    def to_dict(self) -> Dict[str, str]:
        return {
            "segment_id": self.segment_id,
            "root": self.root,
            "translation": self.translation,
            "comment": self.comment,
        }


class BilaraLoader:
    """Loads aligned segments from Bilara JSON files."""

    def __init__(self, base_path: Path) -> None:
        self.base_path = Path(base_path)
        self.root_dir = self.base_path / "root"
        self.translation_dir = self.base_path / "translation"
        self.comment_dir = self.base_path / "comment"

    def load_segments(self, max_segments: Optional[int] = None) -> List[Segment]:
        root_map = self._load_directory(self.root_dir)
        translation_map = self._load_directory(self.translation_dir)
        comment_map = self._load_directory(self.comment_dir)

        segments: List[Segment] = []
        for idx, segment_id in enumerate(root_map.keys()):
            root_text = root_map[segment_id]
            translation_text = translation_map.get(segment_id, "")
            comment_text = comment_map.get(segment_id, "")
            segments.append(
                Segment(
                    segment_id=segment_id,
                    root=root_text,
                    translation=translation_text,
                    comment=comment_text,
                )
            )
            if max_segments is not None and idx + 1 >= max_segments:
                break
        return segments

    def _load_directory(self, directory: Path) -> Dict[str, str]:
        if not directory.exists():
            return {}
        combined: Dict[str, str] = {}
        for path in sorted(directory.rglob("*.json")):
            data = self._load_json(path)
            for key, value in data.items():
                combined[key] = value
        return combined

    @staticmethod
    def _load_json(path: Path) -> Dict[str, str]:
        with path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
        if not isinstance(payload, dict):
            raise ValueError(f"Expected dict in {path}, got {type(payload)!r}")
        ordered = dict(sorted(payload.items(), key=lambda item: item[0]))
        return ordered
