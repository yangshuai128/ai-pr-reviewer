"""
模块6：报告生成（命令行版）
把分析结果格式化成人类可读的报告：整体总结 / 各文件 总结·风险·建议。
"""


def format_report(analysis: dict, pr_title: str) -> str:
    L = ["=" * 60, f"AI PR Review 报告：{pr_title}", "=" * 60,
         "\n【整体总结】", analysis["overall_summary"]]
    for r in analysis["file_results"]:
        L += ["\n" + "-" * 60, f"文件：{r['filename']}", f"总结：{r.get('summary', '')}"]
        risks = r.get("risks", [])
        if risks:
            L.append("风险点：")
            for rk in risks:
                L.append(f"  [{rk.get('level', '?')}风险/置信度{rk.get('confidence', '?')}] "
                         f"{rk.get('description', '')}")
        else:
            L.append("风险点：未发现明显风险")

        static_issues = r.get("static_issues", [])
        if static_issues:
            L.append("静态检查（ruff，确定性问题）：")
            for s in static_issues:
                L.append(f"  [{s.get('code', '?')}] 第{s.get('line', '?')}行 {s.get('message', '')}")

        sugg = r.get("suggestions", [])
        if sugg:
            L.append("改进建议：")
            L += [f"  - {s}" for s in sugg]
    L.append("\n" + "=" * 60)
    return "\n".join(L)
