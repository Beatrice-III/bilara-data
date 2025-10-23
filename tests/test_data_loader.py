from pathlib import Path

from tools.epub_translator.data_loader import BilaraLoader, Segment


def test_load_segments_preserves_order(tmp_path: Path) -> None:
    base = tmp_path
    (base / "root").mkdir()
    (base / "translation").mkdir()
    (base / "comment").mkdir()

    (base / "root" / "file.json").write_text(
        '{"s1":"root1","s2":"root2","s3":"root3"}', encoding="utf-8"
    )
    (base / "translation" / "file.json").write_text(
        '{"s1":"trans1","s2":"trans2"}', encoding="utf-8"
    )
    (base / "comment" / "file.json").write_text(
        '{"s2":"comment2","s3":"comment3"}', encoding="utf-8"
    )

    loader = BilaraLoader(base)
    segments = loader.load_segments()
    assert [segment.segment_id for segment in segments] == ["s1", "s2", "s3"]
    assert segments[1] == Segment(segment_id="s2", root="root2", translation="trans2", comment="comment2")
