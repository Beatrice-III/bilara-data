"""Render translated segments to HTML and EPUB."""
from __future__ import annotations

import datetime as dt
import html
import uuid
from pathlib import Path
from typing import Iterable, List
from zipfile import ZIP_DEFLATED, ZipFile

try:  # pragma: no cover - optional dependency
    from ebooklib import epub  # type: ignore
except Exception:  # pragma: no cover - fallback path
    epub = None

from .data_loader import Segment


CSS_CONTENT = """
body { font-family: "Noto Sans", "Source Han Serif", serif; margin: 1.5em; }
h1 { text-align: center; }
.segment { margin-bottom: 1em; }
.segment-id { color: #888; font-size: 0.8em; }
.root { font-style: italic; color: #3b6ea5; }
.translation { display: block; margin-top: 0.3em; }
.comment { display: block; margin-top: 0.2em; color: #555; }
""".strip()


class EpubRenderer:
    """Render segments into an EPUB file."""

    def __init__(self, language: str = "zh") -> None:
        self.language = language

    def render(self, segments: Iterable[Segment], output_path: Path) -> Path:
        segments_list = list(segments)
        html_content = self._render_html(segments_list)
        output_path = Path(output_path)
        if epub is not None:
            return self._render_with_ebooklib(segments_list, html_content, output_path)
        return self._render_with_zip(segments_list, html_content, output_path)

    def _render_html(self, segments: List[Segment]) -> str:
        body_segments: List[str] = ["<h1>Bilara Translation</h1>"]
        for segment in segments:
            body_segments.append(
                """
                <div class="segment">
                    <div class="segment-id">{segment_id}</div>
                    <span class="root">{root}</span>
                    <span class="translation">{translation}</span>
                    <span class="comment">{comment}</span>
                </div>
                """.format(
                    segment_id=html.escape(segment.segment_id),
                    root=html.escape(segment.root),
                    translation=html.escape(segment.translation),
                    comment=html.escape(segment.comment),
                )
            )
        body = "\n".join(body_segments)
        return (
            "<!DOCTYPE html>\n"
            "<html lang=\"{lang}\">\n"
            "<head>\n"
            "  <meta charset=\"utf-8\" />\n"
            "  <title>Bilara Translation</title>\n"
            "  <style>{css}</style>\n"
            "</head>\n"
            "<body>\n"
            "{body}\n"
            "</body>\n"
            "</html>\n".format(lang=self.language, css=CSS_CONTENT, body=body)
        )

    def _render_with_ebooklib(self, segments: List[Segment], html_content: str, output_path: Path) -> Path:
        book = epub.EpubBook()  # type: ignore[attr-defined]
        book.set_identifier(str(uuid.uuid4()))
        book.set_language(self.language)
        book.set_title("Bilara Translation")
        book.add_author("Bilara Tools")

        css_item = epub.EpubItem(  # type: ignore[attr-defined]
            uid="style_nav",
            file_name="style/main.css",
            media_type="text/css",
            content=CSS_CONTENT.encode("utf-8"),
        )
        book.add_item(css_item)

        chapter = epub.EpubHtml(  # type: ignore[attr-defined]
            title="Bilara Translation",
            file_name="chapters/chapter_1.xhtml",
            lang=self.language,
        )
        chapter.content = html_content
        book.add_item(chapter)
        book.toc = (chapter,)
        book.add_item(epub.EpubNcx())  # type: ignore[attr-defined]
        book.add_item(epub.EpubNav())  # type: ignore[attr-defined]
        book.spine = ["nav", chapter]

        output_path.parent.mkdir(parents=True, exist_ok=True)
        epub.write_epub(str(output_path), book)  # type: ignore[attr-defined]
        return output_path

    def _render_with_zip(self, segments: List[Segment], html_content: str, output_path: Path) -> Path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with ZipFile(output_path, "w") as epub_zip:
            epub_zip.writestr("mimetype", "application/epub+zip", compress_type=ZIP_DEFLATED)
            epub_zip.writestr(
                "META-INF/container.xml",
                """
                <?xml version="1.0"?>
                <container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
                  <rootfiles>
                    <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml" />
                  </rootfiles>
                </container>
                """.strip(),
            )
            epub_zip.writestr("OEBPS/main.css", CSS_CONTENT)
            epub_zip.writestr("OEBPS/content.xhtml", html_content)
            manifest = """
                <?xml version="1.0" encoding="UTF-8"?>
                <package xmlns="http://www.idpf.org/2007/opf" unique-identifier="bookid" version="3.0">
                  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
                    <dc:identifier id="bookid">{identifier}</dc:identifier>
                    <dc:title>Bilara Translation</dc:title>
                    <dc:language>{lang}</dc:language>
                    <meta property="dcterms:modified">{modified}</meta>
                  </metadata>
                  <manifest>
                    <item id="content" href="content.xhtml" media-type="application/xhtml+xml" />
                    <item id="css" href="main.css" media-type="text/css" />
                  </manifest>
                  <spine>
                    <itemref idref="content" />
                  </spine>
                </package>
            """.format(
                identifier=uuid.uuid4(),
                lang=self.language,
                modified=dt.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
            )
            epub_zip.writestr("OEBPS/content.opf", manifest.strip())
        return output_path
