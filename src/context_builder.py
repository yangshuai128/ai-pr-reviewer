"""
模块2：上下文组织（简化版 PR 压缩策略，思路参考 PR-Agent）
职责：把原始 diff 整理成适合喂给模型的文本块。
策略：按文件信息价值排序 -> 在总字符预算内分配 -> 超预算时只保留变化行，而非粗暴截断尾部。
"""

TOTAL_BUDGET_CHARS = 15000   # 整个 PR 的总上下文预算
PER_FILE_SOFT_CAP = 6000     # 单文件软上限


def _file_value(f: dict) -> int:
    """信息价值打分：源码 > 测试/配置；改动越多分越高。"""
    name = (f.get("filename") or "").lower()
    churn = f.get("additions", 0) + f.get("deletions", 0)
    penalty = 0
    if any(k in name for k in ["test", "lock", ".md", ".txt", "fixture", "snapshot"]):
        penalty = 1000
    return churn - penalty


def _changed_lines_only(patch: str) -> str:
    """只保留 diff 的 hunk 头(@@)和真正的 +/- 变化行，丢弃未改动的上下文行（压缩）。
    注意排除 +++/--- 文件头行，它们不是代码变化。
    """
    kept = []
    for ln in patch.splitlines():
        if ln.startswith(("+++", "---")):
            continue                      # 文件头，跳过
        if ln.startswith(("+", "-", "@@")):
            kept.append(ln)
    return "\n".join(kept)


def build_file_contexts(pr_data: dict):
    """返回 [{filename, content}]，在预算内、最有价值的文件优先。"""
    files = [f for f in pr_data["files"] if (f.get("patch") or "").strip()]
    files.sort(key=_file_value, reverse=True)

    contexts, used = [], 0
    for f in files:
        patch = f["patch"]
        if used + len(patch) > TOTAL_BUDGET_CHARS:
            patch = _changed_lines_only(patch)            # 压缩
        if len(patch) > PER_FILE_SOFT_CAP:
            patch = patch[:PER_FILE_SOFT_CAP] + "\n...(diff 过长，已截断)..."
        if used + len(patch) > TOTAL_BUDGET_CHARS:
            break                                          # 预算耗尽
        used += len(patch)

        content = (
            f"文件名：{f['filename']}\n"
            f"改动类型：{f['status']}（新增 {f['additions']} 行，删除 {f['deletions']} 行）\n"
            f"代码改动（diff）：\n{patch}"
        )
        contexts.append({"filename": f["filename"], "content": content})
    return contexts


def build_pr_summary_header(pr_data: dict):
    """生成 PR 整体描述，用于总结环节。"""
    return f"PR 标题：{pr_data['title']}\nPR 描述：{pr_data['description'][:1000]}"
