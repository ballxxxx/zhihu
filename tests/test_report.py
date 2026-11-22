# -*- coding: utf-8 -*-
"""D8 测试:把管线结果渲染成 HTML 并保存。"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import config
from app.services.report import render_report


def main() -> None:
    src = config.DATA_DIR / "pipeline_result.json"
    result = json.loads(src.read_text(encoding="utf-8"))
    html = render_report(result)
    out = config.DATA_DIR / "report_sample.html"
    out.write_text(html, encoding="utf-8")
    print(f"OK: {out} ({len(html)} 字符)")
    assert "AI 划重点" in html and "抽认卡" in html and "复习计划" in html


if __name__ == "__main__":
    main()
