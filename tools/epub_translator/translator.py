"""Translation pipeline that uses the DeepSeek client with caching."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List

from .cache import TranslationCache
from .client import DeepSeekClient
from .data_loader import Segment


@dataclass
class Translator:
    client: DeepSeekClient
    cache: TranslationCache

    def translate_segments(self, segments: Iterable[Segment]) -> List[Segment]:
        results: List[Segment] = []
        context_lines: List[str] = []
        for segment in segments:
            context = "\n".join(context_lines[-3:])
            cached = self.cache.get(segment.segment_id, context)
            if cached is not None:
                translated_text = cached
            else:
                translated_text = self.client.translate_segment(segment, context)
                self.cache.set(segment.segment_id, context, translated_text)
            results.append(
                Segment(
                    segment_id=segment.segment_id,
                    root=segment.root,
                    translation=translated_text,
                    comment=segment.comment,
                )
            )
            context_lines.append(translated_text)
        return results
