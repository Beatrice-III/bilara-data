from pathlib import Path

from tools.epub_translator.ui import collect_parameters_interactively


def test_collect_parameters_interactively_uses_defaults(tmp_path):
    base_path = tmp_path / "data"
    base_path.mkdir()
    (base_path / "root").mkdir()
    (base_path / "translation").mkdir()
    (base_path / "comment").mkdir()

    output_dir = tmp_path / "out"
    output_dir.mkdir()

    inputs = iter(
        [
            str(base_path),
            str(output_dir / "book.epub"),
            "",  # use default language
            "",  # use default cache path
            "",  # use environment API key
            "n",  # dry run disabled
            "",  # translate all segments
        ]
    )

    def fake_input(prompt: str) -> str:
        return next(inputs)

    result = collect_parameters_interactively(
        default_language="zh",
        default_cache_path=Path(".deepseek_cache.json"),
        input_func=fake_input,
    )

    assert result["base_path"] == base_path
    assert result["output"] == output_dir / "book.epub"
    assert result["language"] == "zh"
    assert result["cache"] == Path(".deepseek_cache.json")
    assert result["api_key"] is None
    assert result["dry_run"] is False
    assert result["max_segments"] is None
