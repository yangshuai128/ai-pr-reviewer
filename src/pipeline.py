"""
流程编排：把取数 -> 上下文 -> LLM分析 -> 静态分析 合并成一个函数，供 CLI 和网页复用。
混合架构：LLM 出语义问题，ruff 出确定性问题，合并进同一份结果。
"""
import os
import yaml

from src.github_client import fetch_pr
from src.context_builder import build_file_contexts, build_pr_summary_header
from src.analyzer import analyze_pr
from src.static_analyzer import analyze_python_snippet, added_code_from_patch


def _load_focus():
    """从 review_config.yaml 读取用户自定义关注点（可选）。"""
    path = "review_config.yaml"
    if not os.path.exists(path):
        return ""
    try:
        with open(path, encoding="utf-8") as f:
            cfg = yaml.safe_load(f) or {}
        focus = cfg.get("focus", [])
        if isinstance(focus, list):
            return "；".join(focus)
        return str(focus)
    except Exception:
        return ""


def run_review(pr_url: str, with_static: bool = True) -> dict:
    """完整评审流程，返回 {pr_title, analysis}。"""
    pr_data = fetch_pr(pr_url)
    contexts = build_file_contexts(pr_data)
    header = build_pr_summary_header(pr_data)

    if not contexts:
        return {"pr_title": pr_data["title"], "analysis": None}

    extra_focus = _load_focus()
    analysis = analyze_pr(contexts, header, extra_focus)

    # 混合架构：给每个 Python 文件附加 ruff 的确定性检查结果
    if with_static:
        patch_by_name = {f["filename"]: f.get("patch", "") for f in pr_data["files"]}
        for r in analysis["file_results"]:
            fname = r.get("filename", "")
            if fname.endswith(".py"):
                code = added_code_from_patch(patch_by_name.get(fname, ""))
                r["static_issues"] = analyze_python_snippet(fname, code)

    return {"pr_title": pr_data["title"], "analysis": analysis}
