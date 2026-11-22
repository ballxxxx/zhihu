# -*- coding: utf-8 -*-
"""D7 里程碑测试:全链路(划重点→经验→抽认卡→模拟题→计划)一次跑通。"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import models
from app.services.pipeline import generate_review_package

models.init_db()


def main() -> None:
    stages = []

    def progress(stage: str, detail: str) -> None:
        stages.append(stage)
        print(f"  [{stage}] {detail}")

    print("== 全链路生成中 ==")
    result = generate_review_package(doc_id=1, course="高等数学", exam_date="2026-11-25", progress=progress)

    print("\n== 生成结果摘要 ==")
    print(f"课程: {result['course']}({result['family']})  考前 {result['days']} 天")
    print(f"重点: {len(result['points'])} 个")
    print(f"挂靠经验: {sum(len(v) for v in result['experiences'].values())} 条 + 通用 {len(result['general_experiences'])} 条")
    print(f"抽认卡: {len(result['cards'])} 张")
    print(f"模拟题: {len(result['exam'])} 题")
    print(f"复习计划: {len(result['plan']['days'])} 天")
    print(f"计划 Day1: 学 {len(result['plan']['days'][0]['learn'])} 新 / 复习 {len(result['plan']['days'][0]['review'])} 旧")

    # 完整结果落盘,供 D8 报告渲染用
    out = Path(__file__).resolve().parent.parent / "data" / "pipeline_result.json"
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n完整结果已保存: {out}")

    assert result["points"] and result["cards"] and result["exam"] and result["plan"]["days"]
    assert stages[-1] == "done"
    print("\n=== 里程碑达成:全链路 PASS ===")


if __name__ == "__main__":
    main()
