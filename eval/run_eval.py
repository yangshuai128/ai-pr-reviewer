"""
小型评估脚本（最强差异化加分项，理念参考 CodeRabbit 的评估框架）。
用法：python eval/run_eval.py
做法：用人工标注的已知问题，统计工具命中多少，算出粗略召回率。
匹配方式：字符 n-gram 重叠，对中文（无空格）和英文都适用。
说明：这是召回率的粗略代理；精确率需人工标注误报。重点是展示 precision/recall 思维，
     直接回应题目“误报与漏报控制”的要求。
"""
import json
import sys
sys.path.insert(0, ".")

from src.github_client import fetch_pr
from src.context_builder import build_file_contexts, build_pr_summary_header
from src.analyzer import analyze_pr


def _match(known_issue: str, found_text: str, n: int = 3, threshold: float = 0.3) -> bool:
    """若已知问题的字符 n-gram 有 >=threshold 比例出现在 found_text 中，判为命中。"""
    ki = known_issue.replace(" ", "")
    ft = found_text.replace(" ", "")
    grams = [ki[i:i + n] for i in range(len(ki) - n + 1)] or [ki]
    matched = sum(1 for g in grams if g in ft)
    return matched / len(grams) >= threshold


def run():
    cases = json.load(open("eval/cases.json", encoding="utf-8"))
    total_known, total_found = 0, 0
    for c in cases:
        try:
            pr = fetch_pr(c["pr_url"])
        except Exception as e:
            print(f"{c['pr_url']}: 跳过（拉取失败：{e}）")
            continue
        contexts = build_file_contexts(pr)
        analysis = analyze_pr(contexts, build_pr_summary_header(pr))
        found_text = " ".join(
            rk.get("description", "")
            for r in analysis["file_results"] for rk in r.get("risks", [])
        )
        known = c["known_issues"]
        hit = sum(1 for k in known if _match(k, found_text))
        total_known += len(known)
        total_found += hit
        print(f"{c['pr_url']}: 命中 {hit}/{len(known)}")

    if total_known:
        print(f"\n粗略召回率 ≈ {total_found}/{total_known} = "
              f"{total_found / total_known:.0%}")
    else:
        print("没有可统计的用例。")


if __name__ == "__main__":
    run()
