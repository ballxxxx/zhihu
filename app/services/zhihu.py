# -*- coding: utf-8 -*-
"""zhihu-cli 封装:直答 / 知乎搜索(经验检索用)"""
import subprocess

from app import config


class ZhihuCliError(RuntimeError):
    pass


def _run(args: list[str], timeout: int = 120) -> str:
    proc = subprocess.run(
        [config.ZHIHU_CLI, *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=timeout,
    )
    if proc.returncode != 0:
        detail = (proc.stderr or proc.stdout or "").strip()
        raise ZhihuCliError(f"zhihu-cli 调用失败: {' '.join(args[:2])} -> {detail[:300]}")
    return proc.stdout


def answer(query: str, model: str | None = None, timeout: int = 240) -> str:
    """知乎直答:先检索知乎内容再生成答案。返回 JSON 字符串。"""
    args = ["answer", "--query", query, "--output", "json", "--pretty", "--timeout", f"{timeout}s"]
    if model:
        args += ["--model", model]
    return _run(args, timeout=timeout + 30)


def search_zhihu(query: str, count: int = 5, timeout: int = 90) -> str:
    """知乎站内搜索。返回 JSON 字符串。"""
    return _run(
        ["search", "zhihu", "--query", query, "--count", str(count), "--timeout", f"{timeout}s"],
        timeout=timeout + 30,
    )


def search_global(query: str, count: int = 5, timeout: int = 90) -> str:
    """全网搜索:检索新闻、官网、行业媒体和公开网页(含美团/点评等公开商户页)。"""
    return _run(
        ["search", "global", "--query", query, "--count", str(count), "--timeout", f"{timeout}s"],
        timeout=timeout + 30,
    )
