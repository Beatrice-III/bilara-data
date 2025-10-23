"""Command-line entry point for the EPUB translator tool."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Optional

from . import data_loader, translator
from .cache import TranslationCache
from .client import DeepSeekClient
from .renderer import EpubRenderer
from .ui import collect_parameters_interactively


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="将 Bilara 数据翻译为 EPUB 的命令行工具",
    )
    parser.add_argument(
        "base_path",
        type=Path,
        nargs="?",
        help="Bilara 数据集的根目录（包含 root/ translation/ comment/）",
    )
    parser.add_argument(
        "output",
        type=Path,
        nargs="?",
        help="生成的 EPUB 文件路径",
    )
    parser.add_argument("--language", default="zh", help="译文语言代码，默认为中文")
    parser.add_argument(
        "--cache",
        type=Path,
        default=Path(".deepseek_cache.json"),
        help="翻译缓存文件路径",
    )
    parser.add_argument(
        "--api-key",
        dest="api_key",
        help="DeepSeek API 密钥（默认读取 DEEPSEEK_API_KEY 环境变量）",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="仅加载数据并生成 EPUB，不连接翻译 API",
    )
    parser.add_argument(
        "--max-segments",
        type=int,
        default=None,
        help="仅翻译前 N 个段落，便于测试",
    )
    parser.add_argument(
        "--ui",
        action="store_true",
        help="启动中文交互界面填写参数",
    )
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.ui:
        ui_args = collect_parameters_interactively(
            default_language=args.language,
            default_cache_path=args.cache,
        )
        for field, value in ui_args.items():
            setattr(args, field, value)

    if args.base_path is None or args.output is None:
        parser.error("必须提供 base_path 和 output，或使用 --ui 交互填写参数")

    api_key = args.api_key or os.getenv("DEEPSEEK_API_KEY")
    if not api_key and not args.dry_run:
        parser.error("DeepSeek API key must be provided via --api-key or DEEPSEEK_API_KEY environment variable")

    loader = data_loader.BilaraLoader(args.base_path)
    segments = loader.load_segments(max_segments=args.max_segments)

    cache = TranslationCache(args.cache)
    client = DeepSeekClient(api_key=api_key, enabled=not args.dry_run)

    translator_service = translator.Translator(client=client, cache=cache)
    translated_segments = translator_service.translate_segments(segments)

    renderer = EpubRenderer(language=args.language)
    epub_path = renderer.render(translated_segments, output_path=args.output)

    with args.output.with_suffix(".json").open("w", encoding="utf-8") as fh:
        json.dump([segment.to_dict() for segment in translated_segments], fh, ensure_ascii=False, indent=2)

    print(f"EPUB written to {epub_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
