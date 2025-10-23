import zipfile
from pathlib import Path

from tools.epub_translator.data_loader import Segment
from tools.epub_translator.renderer import EpubRenderer


def test_epub_structure(tmp_path: Path) -> None:
    renderer = EpubRenderer(language="zh")
    segments = [
        Segment(segment_id="s1", root="root text", translation="translated text", comment="note"),
    ]
    output = tmp_path / "book.epub"
    renderer.render(segments, output)

    assert output.exists()
    with zipfile.ZipFile(output, "r") as zf:
        assert "mimetype" in zf.namelist()
        assert "META-INF/container.xml" in zf.namelist()
        assert "OEBPS/content.xhtml" in zf.namelist()
        content = zf.read("OEBPS/content.xhtml").decode("utf-8")
        assert "translated text" in content
        assert "root text" in content
