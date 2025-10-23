from pathlib import Path

from tools.epub_translator.cache import TranslationCache
from tools.epub_translator.client import DeepSeekClient
from tools.epub_translator.data_loader import Segment
from tools.epub_translator.translator import Translator


class StubClient(DeepSeekClient):
    def __init__(self) -> None:
        super().__init__(api_key="test", enabled=True)
        self.calls = 0

    def translate_segment(self, segment: Segment, context: str) -> str:  # type: ignore[override]
        self.calls += 1
        return f"translated:{segment.segment_id}:{context}"


def test_cache_hits_prevent_api_calls(tmp_path: Path) -> None:
    cache_file = tmp_path / "cache.json"
    cache = TranslationCache(cache_file)
    client = StubClient()
    translator = Translator(client=client, cache=cache)

    segments = [
        Segment(segment_id="s1", root="root", translation="", comment=""),
        Segment(segment_id="s1", root="root", translation="", comment=""),
    ]

    result_first = translator.translate_segments(segments)
    assert client.calls == 2

    # Second call should use cache for both segments
    client.calls = 0
    result_second = translator.translate_segments(segments)
    assert client.calls == 0
    assert [seg.translation for seg in result_second] == [seg.translation for seg in result_first]
