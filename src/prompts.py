"""
模块3：提示词模板（JSON 化提示，思路参考 PR-Agent）
要求模型按固定 JSON 结构返回，便于解析；类别可在此集中调整。
注意：模板里的双花括号 {{ }} 是“字面花括号”，给 .format() 用的，不可改成单花括号。
"""

SYSTEM_PROMPT = "你是一位资深的代码评审专家，擅长发现代码中的 bug、安全隐患、性能问题和规范问题。"

FILE_REVIEW_PROMPT = """请评审下面这个文件的代码改动。
{extra_focus}
{file_context}

请严格按照以下 JSON 格式返回，不要输出任何额外文字、不要用 markdown 代码块包裹：
{{
  "summary": "这个文件改动的简要总结",
  "risks": [
    {{"level": "高/中/低", "description": "风险描述", "confidence": "高/中/低"}}
  ],
  "suggestions": ["具体改进建议1", "具体改进建议2"]
}}
如果没有发现风险，risks 返回空数组 []。"""

OVERALL_SUMMARY_PROMPT = """下面是一个 Pull Request 的整体信息和各文件评审结果。

{pr_header}

各文件评审摘要：
{file_summaries}

请用 2-3 句话总结这个 PR 整体做了什么、整体质量如何。只返回总结文字，不要 JSON。"""

QA_PROMPT = """下面是一个 Pull Request 的代码改动：

{pr_context}

用户的问题：{question}

请基于上述代码改动回答用户的问题，准确、简洁。"""
