"""Simple Chinese interactive interface for configuring the EPUB translation pipeline."""
from __future__ import annotations

from pathlib import Path
from typing import Callable, Dict

Prompt = Callable[[str], str]


def _input_with_default(prompt: str, default: str, input_func: Prompt) -> str:
    message = f"{prompt}（默认：{default}）：" if default else f"{prompt}："
    response = input_func(message).strip()
    return response or default


def collect_parameters_interactively(
    *,
    default_language: str,
    default_cache_path: Path,
    input_func: Prompt = input,
) -> Dict[str, object]:
    """Return a dictionary with CLI parameters collected via Chinese prompts."""

    print("欢迎使用 Bilara EPUB 翻译工具 👋")
    print("请按提示填写信息，直接回车可使用默认值。")

    base_path = Path(
        input_func("请输入 Bilara 数据目录（含 root/ translation/ comment/）：").strip()
    )
    while not base_path.exists():
        print("⚠️ 路径不存在，请重新输入。")
        base_path = Path(
            input_func("请输入 Bilara 数据目录（含 root/ translation/ comment/）：").strip()
        )

    output_path = Path(
        input_func("请输入要生成的 EPUB 文件路径，例如 output/book.epub：").strip()
    )
    while not output_path.parent.exists():
        print("⚠️ 输出目录不存在，请重新输入。")
        output_path = Path(
            input_func("请输入要生成的 EPUB 文件路径，例如 output/book.epub：").strip()
        )

    language = _input_with_default("译文语言代码", default_language, input_func)

    cache_path_input = _input_with_default(
        "缓存文件路径", str(default_cache_path), input_func
    )
    cache_path = Path(cache_path_input)

    api_key = input_func(
        "请输入 DeepSeek API 密钥（留空则使用环境变量 DEEPSEEK_API_KEY）："
    ).strip() or None

    dry_run_answer = input_func(
        "是否跳过 API 调用仅生成结构文件？(y/N)："
    ).strip().lower()
    dry_run = dry_run_answer == "y"

    max_segments_value = input_func(
        "需要仅翻译前 N 个段落吗？直接回车表示全部："
    ).strip()
    max_segments = int(max_segments_value) if max_segments_value else None

    print("设置完成，开始执行翻译流程……")

    return {
        "base_path": base_path,
        "output": output_path,
        "language": language,
        "cache": cache_path,
        "api_key": api_key,
        "dry_run": dry_run,
        "max_segments": max_segments,
    }

