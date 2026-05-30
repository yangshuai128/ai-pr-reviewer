"""
<<<<<<< HEAD
模块6：报告生成（命令行版 + GitHub Markdown 版）
把分析结果格式化成人类可读的报告：整体总结 / 各文件 总结·风险·建议。
=======
模块6：报告生成（命令行版 + Markdown 评论版）
- format_report：命令行纯文本报告
- build_markdown_comment：GitHub PR 评论用的 Markdown，复用 analyzer 输出的字段结构
>>>>>>> main
"""


def build_markdown_comment(result: dict) -> str:
<<<<<<< HEAD
    """生成适合发布到 GitHub PR 的 Markdown 格式评审报告。
    接受 run_review() 返回的完整 result dict（含 pr_title 和 analysis）。
    """
    analysis = result.get("analysis") or {}
    pr_title = result.get("pr_title", "")
    lines = [
        f"## 🤖 AI PR Review 报告：{pr_title}",
        "",
        "### 📋 整体总结",
        analysis.get("overall_summary", ""),
        "",
    ]
    for r in analysis.get("file_results", []):
        lines.append(f"### 📄 `{r.get('filename', '')}`")
        lines.append(f"**总结**：{r.get('summary', '')}")
        lines.append("")

        risks = r.get("risks", [])
        if risks:
            lines.append("**风险点：**")
            for rk in risks:
                level = rk.get("level", "?")
                conf = rk.get("confidence", "?")
                desc = rk.get("description", "")
                source = rk.get("source", "")
                source_tag = {"claude": "🧠 Claude", "ruff": "🔧 ruff", "both": "🛡️ 双重确认"}.get(source, source)
                lines.append(f"- `{level}风险/置信度{conf}` [{source_tag}] {desc}")
        else:
            lines.append("**风险点：** 未发现明显风险")

        static_issues = r.get("static_issues", [])
        if static_issues:
            lines.append("")
            lines.append("**静态检查（ruff）：**")
            for s in static_issues:
                lines.append(f"- `{s.get('code', '?')}` 第{s.get('line', '?')}行 {s.get('message', '')}")

        sugg = r.get("suggestions", [])
        if sugg:
            lines.append("")
            lines.append("**改进建议：**")
            for s in sugg:
                lines.append(f"- {s}")
        lines.append("")

    lines.append("---")
    lines.append("*由 [AI PR Reviewer](https://github.com/yangshuai128/ai-pr-reviewer) 自动生成*")
=======
    """把 run_review 返回的 result 转成 GitHub PR 评论 Markdown。

    复用字段说明（与 analyzer.py / pipeline.py 输出结构保持一致）：
    - result["pr_title"]：PR 标题
    - result["analysis"]["overall_summary"]：整体总结
    - result["analysis"]["file_results"]：列表，每项含 filename / summary / risks / suggestions / static_issues
    - risks 每项含 level / confidence / description
    """
    analysis = result.get("analysis") or {}
    pr_title = result.get("pr_title", "")
    file_results = analysis.get("file_results", [])

    lines = [
        "## 🤖 AI PR Review 助手",
        "",
        f"**PR 标题**：{pr_title}",
        "",
        "### 📋 变更总结",
        "",
        analysis.get("overall_summary", "（无总结）"),
        "",
    ]

    # 风险点表格
    all_risks = [
        (r.get("filename", ""), rk)
        for r in file_results
        for rk in (r.get("risks") or [])
    ]
    if all_risks:
        lines += [
            "### ⚠️ 风险点",
            "",
            "| 文件 | 等级 | 置信度 | 说明 |",
            "| --- | --- | --- | --- |",
        ]
        for fname, rk in all_risks:
            lines.append(
                f"| `{fname}` "
                f"| {rk.get('level', '?')} "
                f"| {rk.get('confidence', '?')} "
                f"| {rk.get('description', '')} |"
            )
        lines.append("")
    else:
        lines += ["### ⚠️ 风险点", "", "未发现明显风险。", ""]

    # Review 建议
    all_suggestions = [
        (r.get("filename", ""), s)
        for r in file_results
        for s in (r.get("suggestions") or [])
    ]
    if all_suggestions:
        lines += ["### 💡 Review 建议", ""]
        for fname, s in all_suggestions:
            lines.append(f"- **`{fname}`**：{s}")
        lines.append("")

    # ruff 静态检查结果（如果有）
    all_static = [
        (r.get("filename", ""), s)
        for r in file_results
        for s in (r.get("static_issues") or [])
    ]
    if all_static:
        lines += ["### 🔍 静态检查（ruff）", ""]
        for fname, s in all_static:
            lines.append(
                f"- `{fname}` 第 {s.get('line', '?')} 行 "
                f"[{s.get('code', '?')}] {s.get('message', '')}"
            )
        lines.append("")

    lines.append("---")
    lines.append("*本评论由 [ai-pr-reviewer](https://github.com/yangshuai128/ai-pr-reviewer) 自动生成*")

>>>>>>> main
    return "\n".join(lines)


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
