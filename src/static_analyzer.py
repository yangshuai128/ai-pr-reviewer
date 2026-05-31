"""
模块5：静态分析（混合架构加分项，思路参考 CodeRabbit / Kodus）
职责：用 ruff 对 Python 代码做确定性检查（语法、未用变量等），零误报。
设计：与 LLM 的语义分析职责分离——确定性问题给工具，主观问题给 LLM。
容错：任何异常都返回 []，绝不影响主流程（fail-soft）。
"""
import subprocess
import json
import tempfile
import os


def analyze_python_snippet(filename: str, code: str):
    """对一段 Python 代码跑 ruff，返回 [{line, code, message}]。
    非 Python 文件或空内容返回 []。
    """
    if not filename.endswith(".py") or not code.strip():
        return []
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False, encoding="utf-8") as tf:
        tf.write(code)
        tmp = tf.name
    try:
        proc = subprocess.run(
            ["ruff", "check", "--output-format=json", tmp],
            capture_output=True,
            text=True,
            encoding="utf-8",   # 明确指定 UTF-8，避免 Windows GBK 解码失败
            errors="replace",   # 无法解码的字节用 ? 替换，不崩溃
            timeout=30,
        )
        out = (proc.stdout or "").strip()
        if not out:
            return []
        return [{
            "line": d.get("location", {}).get("row"),
            "code": d.get("code"),
            "message": d.get("message"),
            "source": "ruff",
        } for d in json.loads(out)]
    except (subprocess.TimeoutExpired, json.JSONDecodeError, FileNotFoundError,
            AttributeError, OSError):
        return []  # ruff 未安装或出错时静默降级
    finally:
        os.unlink(tmp)


def added_code_from_patch(patch: str) -> str:
    """从 diff 中抽取新增的代码行（去掉 + 前缀），用于喂给 ruff。"""
    lines = []
    for ln in patch.splitlines():
        if ln.startswith("+") and not ln.startswith("+++"):
            lines.append(ln[1:])
    return "\n".join(lines)
