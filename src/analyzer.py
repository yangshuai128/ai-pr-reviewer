"""
模块4：调用 Claude 分析
职责：把上下文发给 Claude，逐文件分析，再生成整体总结；另提供问答能力。
要点：
  - 模型用当前推荐的 claude-sonnet-4-6（不要用已弃用的 ...-20250514）。
  - _safe_parse_json 用正则提取第一个 {...}，能容忍模型在 JSON 前后多写文字。
"""
import os
import re
import json
from anthropic import Anthropic
from dotenv import load_dotenv

from src.prompts import (SYSTEM_PROMPT, FILE_REVIEW_PROMPT,
                         OVERALL_SUMMARY_PROMPT, QA_PROMPT)

load_dotenv()
client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

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
    """健壮解析：正则提取第一个 {...}，容忍前后多余文字；失败兜底，保证不崩。"""
    text = text.strip()
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if m:
        text = m.group(0)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {
            "summary": "（解析失败，模型返回了非标准格式）",
            "risks": [],
            "suggestions": [text[:500]],
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
