"""
模块4：调用 Claude 分析
职责：把上下文发给 Claude，逐文件分析，再生成整体总结；另提供问答能力。
要点：
  - 模型用当前推荐的 claude-sonnet-4-6（不要用已弃用的 ...-20250514）。
  - _safe_parse_json 用 re.findall 找出所有 {...} 候选，从最长的开始尝试解析，
    避免贪婪匹配在嵌套 JSON 上失效后把原始文本塞进 suggestions 的 bug。
    （此改动来自用本工具自评审 PR #1 时发现的真实问题）
"""
import os
import re
import json
from anthropic import Anthropic
from dotenv import load_dotenv

from src.prompts import (SYSTEM_PROMPT, FILE_REVIEW_PROMPT,
                         OVERALL_SUMMARY_PROMPT, QA_PROMPT)

load_dotenv()
client = Anthropic(
    api_key=os.getenv("ANTHROPIC_API_KEY"),
    base_url=os.getenv("ANTHROPIC_BASE_URL"),
)

MODEL = "claude-sonnet-4-6"          # 当前推荐：准确性/成本平衡
# 想更便宜更快可改为下面这行：
# MODEL = "claude-haiku-4-5-20251001"


def _call(prompt: str, max_tokens: int = 1500) -> str:
    resp = client.messages.create(
        model=MODEL,
        max_tokens=max_tokens,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    )
    return "".join(b.text for b in resp.content if b.type == "text")


def _safe_parse_json(text: str) -> dict:
    """健壮解析：找出所有 {...} 候选，从最长的开始尝试 json.loads，失败再兜底。

    改进原因（来自用本工具自评审 PR #1 时发现的真实 bug）：
    原实现用 re.search(r"\{.*\}", ..., re.DOTALL) 贪婪匹配，当模型返回的 JSON
    外层有嵌套花括号时，匹配范围可能超出合法 JSON 边界，导致 json.loads 失败，
    进而把整段原始文本（最多 500 字符）塞进 suggestions 字段显示给用户。

    新实现：用 re.findall 收集所有 {...} 候选，按长度从大到小依次尝试解析，
    命中即返回；全部失败时兜底返回友好提示而非原始 JSON 乱码。
    """
    text = text.strip()
    # 收集所有 {...} 候选（贪婪），按长度降序，优先尝试最完整的结构
    candidates = re.findall(r"\{.*?\}", text, re.DOTALL)
    # 也加入整段贪婪匹配结果，确保覆盖最外层嵌套
    greedy = re.search(r"\{.*\}", text, re.DOTALL)
    if greedy:
        candidates.insert(0, greedy.group(0))
    # 去重并按长度降序
    seen, ordered = set(), []
    for c in candidates:
        if c not in seen:
            seen.add(c)
            ordered.append(c)
    ordered.sort(key=len, reverse=True)

    for candidate in ordered:
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            continue

    # 全部失败：返回友好提示，不把原始 JSON 乱码暴露给用户
    return {
        "summary": "（解析失败，模型返回了非标准格式）",
        "risks": [],
        "suggestions": ["（AI 返回内容无法解析为 JSON，请检查提示词或重试）"],
    }


def analyze_file(file_context: str, extra_focus: str = "") -> dict:
    """分析单个文件。extra_focus 为用户自定义关注点（来自配置文件，可选）。"""
    focus = f"特别关注：{extra_focus}\n" if extra_focus else ""
    raw = _call(FILE_REVIEW_PROMPT.format(extra_focus=focus, file_context=file_context))
    return _safe_parse_json(raw)


def analyze_pr(file_contexts: list, pr_header: str, extra_focus: str = "") -> dict:
    """逐文件分析（默认模式，对大 PR 友好），再生成整体总结。"""
    file_results = []
    for ctx in file_contexts:
        r = analyze_file(ctx["content"], extra_focus)
        r["filename"] = ctx["filename"]
        file_results.append(r)

    summaries = "\n".join(
        f"- {r['filename']}: {r.get('summary', '')}" for r in file_results
    )
    overall = _call(
        OVERALL_SUMMARY_PROMPT.format(pr_header=pr_header, file_summaries=summaries),
        max_tokens=500,
    )
    return {"overall_summary": overall.strip(), "file_results": file_results}


def answer_question(pr_context: str, question: str) -> str:
    """问答模式（参考 PR-Agent 的 /ask）。"""
    return _call(QA_PROMPT.format(pr_context=pr_context[:12000], question=question)).strip()
