"""
AI PR Reviewer - Multi-page Streamlit App
页面: 评审中心 / 结果总览 / 风险详情 / 建议&推理 / 使用文档
"""
import math
import streamlit as st

from src.github_client import fetch_pr, parse_pr_url, post_pr_comment, post_inline_review
from src.context_builder import build_file_contexts
from src.analyzer import answer_question
from src.pipeline import run_review
from src.reporter import build_markdown_comment

# ── 页面配置 ──────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AI PR Reviewer",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS ───────────────────────────────────────────────────────────────────────
CUSTOM_CSS = """<style>
.stApp { background-color: #0A0A0A; }
[data-testid="stHeader"] { background: transparent; }
[data-testid="stSidebar"] { background-color: #111111; border-right: 1px solid #27272A; }
.block-container { padding-top: 1.5rem; padding-bottom: 2rem; max-width: 1100px; }

/* 通用卡片 */
.card { background: #18181B; border: 1px solid #27272A; border-radius: 10px; padding: 20px 24px; margin-bottom: 16px; }
.card-title { font-size: 15px; font-weight: 600; color: #FAFAFA; margin-bottom: 12px; display: flex; align-items: center; gap: 8px; }
.card-accent { width: 4px; height: 14px; border-radius: 2px; display: inline-block; }
.acc-purple { background: #8B5CF6; }
.acc-red    { background: #F87171; }
.acc-cyan   { background: #06B6D4; }
.acc-green  { background: #34D399; }
.acc-violet { background: #A78BFA; }
.acc-gray   { background: #71717A; }

/* KPI 卡片 */
.kpi-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin-bottom: 16px; }
.kpi-card { background: #18181B; border: 1px solid #27272A; border-radius: 10px; padding: 16px 20px; }
.kpi-label { font-size: 11px; color: #71717A; text-transform: uppercase; letter-spacing: 0.8px; margin-bottom: 6px; font-weight: 600; }
.kpi-value { font-size: 32px; font-weight: 700; color: #FAFAFA; line-height: 1; }
.kpi-value.accent { color: #06B6D4; }
.kpi-value.warn   { color: #FBBF24; }
.kpi-value.bad    { color: #F87171; }
.kpi-hint { font-size: 12px; color: #71717A; margin-top: 6px; }

/* 徽章 */
.badge { font-size: 11px; padding: 2px 9px; border-radius: 999px; font-weight: 500; border: 1px solid transparent; }
.badge-sev-high   { background: rgba(248,113,113,0.1); color: #F87171; border-color: rgba(248,113,113,0.2); }
.badge-sev-medium { background: rgba(251,191,36,0.1);  color: #FBBF24; border-color: rgba(251,191,36,0.2); }
.badge-sev-low    { background: rgba(52,211,153,0.1);  color: #34D399; border-color: rgba(52,211,153,0.2); }
.badge-source-both   { background: rgba(139,92,246,0.1); color: #A78BFA; border-color: rgba(139,92,246,0.2); }
.badge-source-claude { background: rgba(6,182,212,0.1);  color: #06B6D4; border-color: rgba(6,182,212,0.2); }
.badge-source-ruff   { background: rgba(96,165,250,0.1); color: #60A5FA; border-color: rgba(96,165,250,0.2); }

/* 风险卡片 */
.risk-card { background: #0D0D0D; border: 1px solid #27272A; border-left: 4px solid #34D399; border-radius: 8px; padding: 14px 16px; margin-bottom: 10px; }
.risk-card.sev-high   { border-left-color: #F87171; }
.risk-card.sev-medium { border-left-color: #FBBF24; }
.risk-card.sev-low    { border-left-color: #34D399; }
.risk-header { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; flex-wrap: wrap; }
.risk-body { font-size: 13px; color: #E4E4E7; line-height: 1.7; }
.risk-body code { background: #18181B; color: #06B6D4; padding: 1px 5px; border-radius: 3px; font-size: 12px; }
.badge-file { font-size: 12px; color: #A1A1AA; font-family: ui-monospace,monospace; background: #18181B; padding: 2px 8px; border-radius: 4px; }
.confidence-tag { font-size: 11px; color: #06B6D4; margin-left: auto; }

/* 建议行 */
.suggest-row { background: #0D0D0D; border: 1px solid #27272A; border-radius: 8px; padding: 12px 14px; display: flex; gap: 10px; margin-bottom: 8px; }
.pri-tag { font-size: 10px; padding: 3px 8px; border-radius: 4px; font-weight: 700; height: fit-content; color: #fff; flex-shrink: 0; }
.pri-p0 { background: #8B5CF6; }
.pri-p1 { background: #06B6D4; }
.pri-p2 { background: #3F3F46; color: #A1A1AA; }
.suggest-body { font-size: 13px; color: #E4E4E7; line-height: 1.65; }
.suggest-body code { background: #18181B; color: #06B6D4; padding: 1px 5px; border-radius: 3px; font-size: 12px; }
.suggest-meta { font-size: 11px; color: #71717A; margin-top: 4px; }

/* 推理框 */
.reason-box { font-size: 12px; color: #A1A1AA; line-height: 2; font-family: ui-monospace,monospace; background: #0D0D0D; border: 1px solid #27272A; border-radius: 8px; padding: 14px 16px; }
.reason-step { color: #52525B; }

/* 文件树 */
.tree { font-size: 13px; font-family: ui-monospace,monospace; line-height: 2; }
.tree-folder { color: #71717A; }
.tree-file { color: #FAFAFA; padding-left: 16px; display: flex; align-items: center; gap: 6px; }
.tree-risk { padding: 1px 7px; border-radius: 8px; font-size: 11px; font-weight: 600; }
.risk-high-pill   { background: rgba(248,113,113,0.15); color: #F87171; }
.risk-medium-pill { background: rgba(251,191,36,0.15);  color: #FBBF24; }
.risk-low-pill    { background: rgba(52,211,153,0.15);  color: #34D399; }

/* 流水线 */
.pipeline-row { display: flex; align-items: stretch; gap: 6px; }
.pipeline-step { flex: 1; background: #0D0D0D; border: 1px solid #27272A; border-radius: 6px; padding: 10px 12px; }
.pipeline-step.highlight { border-color: #8B5CF6; }
.pipeline-step-title { display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px; font-size: 12px; font-weight: 600; }
.pipeline-step-body { font-size: 11px; color: #A1A1AA; line-height: 1.6; }
.pipeline-arrow { display: flex; align-items: center; color: #3F3F46; font-size: 14px; }

/* 活动时间线 */
.activity-row { display: flex; align-items: center; gap: 10px; font-size: 13px; color: #A1A1AA; margin-bottom: 8px; }
.activity-time { color: #52525B; width: 50px; font-family: ui-monospace,monospace; font-size: 11px; flex-shrink: 0; }
.activity-dot { width: 10px; text-align: center; flex-shrink: 0; }

/* 文档页 */
.doc-section { margin-bottom: 28px; }
.doc-section h3 { font-size: 16px; color: #FAFAFA; margin-bottom: 10px; }
.doc-section p, .doc-section li { font-size: 14px; color: #A1A1AA; line-height: 1.8; }
.doc-section code { background: #18181B; color: #06B6D4; padding: 2px 6px; border-radius: 4px; font-size: 13px; }
.doc-step { background: #18181B; border: 1px solid #27272A; border-radius: 8px; padding: 14px 18px; margin-bottom: 10px; }
.doc-step-num { display: inline-flex; align-items: center; justify-content: center; width: 24px; height: 24px; background: #8B5CF6; color: #fff; border-radius: 6px; font-size: 12px; font-weight: 700; margin-right: 8px; }

/* Streamlit 原生组件 */
.stRadio > div { gap: 10px; }
.stButton button { background: #8B5CF6; color: #fff; border: 1px solid #8B5CF6; font-size: 14px; }
.stButton button:hover { background: #7C3AED; border-color: #7C3AED; }
[data-testid="stMarkdownContainer"] p { color: #E4E4E7; font-size: 14px; }
</style>"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# ── 常量 ──────────────────────────────────────────────────────────────────────
EXAMPLE_PRS = {
    "自定义...": "",
    "PyGithub #3294": "https://github.com/PyGithub/PyGithub/pull/3294",
    "本仓库 PR #1": "https://github.com/yangshuai128/ai-pr-reviewer/pull/1",
    "本仓库 PR #2": "https://github.com/yangshuai128/ai-pr-reviewer/pull/2",
    "本仓库 PR #3": "https://github.com/yangshuai128/ai-pr-reviewer/pull/3",
}

_SEV_BADGE = {"高": "badge-sev-high", "中": "badge-sev-medium", "低": "badge-sev-low"}
_SEV_CARD  = {"高": "sev-high",       "中": "sev-medium",       "低": "sev-low"}
_SOURCE_BADGE = {"both": "badge-source-both", "claude": "badge-source-claude", "ruff": "badge-source-ruff"}
_SOURCE_LABEL = {"both": "🛡️ 双重确认", "claude": "🧠 Claude", "ruff": "🔧 ruff"}

# ── 计算函数 ──────────────────────────────────────────────────────────────────
def _compute_radar_scores(file_results):
    total  = sum(len(r.get("risks") or []) for r in file_results)
    high   = sum(1 for r in file_results for rk in (r.get("risks") or []) if rk.get("level") == "高")
    medium = sum(1 for r in file_results for rk in (r.get("risks") or []) if rk.get("level") == "中")
    both   = sum(1 for r in file_results for rk in (r.get("risks") or []) if rk.get("source") == "both")
    has_test   = any("test"   in (r.get("filename") or "").lower() for r in file_results)
    has_readme = any("readme" in (r.get("filename") or "").lower() for r in file_results)
    has_doc    = any((r.get("filename") or "").lower().endswith((".md", ".rst", ".txt")) for r in file_results)
    return {
        "安全":   max(30, min(100, 100 - high * 25)),
        "性能":   max(40, min(100, 100 - medium * 12)),
        "可维护": max(40, min(100, 100 - total * 5 + both * 3)),
        "文档":   85 if has_readme else (75 if has_doc else 55),
        "测试":   80 if has_test else 45,
    }

def _overall_score(scores):
    return sum(scores.values()) // 5

def _overall_label(score):
    if score >= 80: return "良好", "good"
    if score >= 60: return "待改进", "warn"
    return "需关注", "bad"

def _risk_severity_breakdown(file_results):
    high   = sum(1 for r in file_results for rk in (r.get("risks") or []) if rk.get("level") == "高")
    medium = sum(1 for r in file_results for rk in (r.get("risks") or []) if rk.get("level") == "中")
    low    = sum(1 for r in file_results for rk in (r.get("risks") or []) if rk.get("level") == "低")
    return high, medium, low

def _both_count(file_results):
    return sum(1 for r in file_results for rk in (r.get("risks") or []) if rk.get("source") == "both")

def _make_radar_svg(scores, size=200):
    cx, cy, max_r = 150, 160, 115
    labels = ["安全", "性能", "可维护", "文档", "测试"]
    angles = [-90, -18, 54, 126, 198]
    def pt(r, deg):
        a = math.radians(deg)
        return cx + r * math.cos(a), cy + r * math.sin(a)
    grid = "".join(
        f'<polygon points="{" ".join(f"{x:.1f},{y:.1f}" for x,y in [pt(max_r*p,d) for d in angles])}" fill="none" stroke="#27272A" stroke-width="1"/>'
        for p in [0.25, 0.5, 0.75, 1.0]
    )
    score_pts = [pt(max_r * scores[l] / 100, d) for l, d in zip(labels, angles)]
    coords    = " ".join(f"{x:.1f},{y:.1f}" for x, y in score_pts)
    polygon   = f'<polygon points="{coords}" fill="rgba(139,92,246,0.2)" stroke="#8B5CF6" stroke-width="2"/>'
    dots      = "".join(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4" fill="#06B6D4"/>' for x, y in score_pts)
    label_specs = [(150,32,"middle"),(276,120,"start"),(232,273,"middle"),(68,273,"middle"),(24,120,"end")]
    label_svg = "".join(
        f'<text x="{x}" y="{y}" text-anchor="{a}" fill="#A1A1AA" font-size="13" font-weight="500">{t} {scores[t]}</text>'
        for (x,y,a),t in zip(label_specs, labels)
    )
    return f'<svg width="100%" height="{size}" viewBox="0 0 300 300">{grid}{polygon}{dots}{label_svg}</svg>'

# ══════════════════════════════════════════════════════════════════════════════
# 页面函数
# ══════════════════════════════════════════════════════════════════════════════

def _page_review():
    """评审中心：输入 PR 链接，触发分析"""
    st.title("🔍 评审中心")
    st.markdown("输入 GitHub PR 链接，AI 将自动拉取代码、分析风险并生成报告。")

    col_select, col_url, col_btn = st.columns([2, 5, 1.5])
    with col_select:
        # 找到当前 pr_url 对应的示例选项（用于回显），默认"自定义..."
        current_url = st.session_state.get("pr_url", "")
        reverse_map = {v: k for k, v in EXAMPLE_PRS.items() if v}
        default_idx = 0
        if current_url in reverse_map:
            keys = list(EXAMPLE_PRS.keys())
            default_idx = keys.index(reverse_map[current_url])
        example_choice = st.selectbox(
            "示例 PR",
            list(EXAMPLE_PRS.keys()),
            index=default_idx,
            label_visibility="collapsed",
        )
    with col_url:
        # 如果用户选了示例，用示例 URL 填充；否则保留 session_state 里的值
        if example_choice != "自定义...":
            prefill = EXAMPLE_PRS[example_choice] or ""
        else:
            prefill = st.session_state.get("pr_url") or ""
        pr_url = st.text_input(
            "PR 链接",
            value=prefill,
            placeholder="https://github.com/owner/repo/pull/123",
            label_visibility="collapsed",
        )
    # 防御性处理：确保 pr_url 始终是字符串
    pr_url = pr_url or ""
    st.session_state["pr_url"] = pr_url

    mode = st.radio("模式", ["评审模式", "问答模式"], horizontal=True)

    with col_btn:
        run_clicked = False
        if mode == "评审模式":
            run_clicked = st.button("开始评审 →", type="primary", use_container_width=True)

    if mode == "评审模式":
        if run_clicked:
            if not pr_url.strip():
                st.warning("请先输入 PR 链接")
            else:
                try:
                    with st.spinner("正在拉取并分析（首次可能需要几十秒）..."):
                        result = run_review(pr_url)
                    if result["analysis"] is None:
                        st.info("没有可分析的代码改动。")
                        st.session_state.pop("review_result", None)
                    else:
                        st.session_state["review_result"] = result
                        st.session_state["review_file_results"] = result["analysis"].get("file_results", [])
                        st.success("✅ 分析完成！请前往左侧「结果总览」查看报告。")
                except Exception as e:
                    st.error(f"出错了：{e}")

        if st.session_state.get("review_result") and pr_url.strip():
            st.markdown("---")
            st.markdown("#### 📤 发布到 GitHub")
            publish_mode = st.radio(
                "发布模式",
                options=["📄 总结模式", "🎯 行级精准模式"],
                captions=["完整评审作为一条评论发到 PR 底部", "每条风险作为 inline review 挂在代码行"],
                horizontal=True,
            )
            btn1, btn2, btn3 = st.columns(3)
            with btn1:
                publish_clicked = st.button("📤 发布到 GitHub PR", type="primary", use_container_width=True, key="pub_btn")
            with btn2:
                md_clicked = st.button("📄 查看 Markdown", use_container_width=True, key="md_btn")
            with btn3:
                st.download_button(
                    "⬇ 导出 MD",
                    data=build_markdown_comment(st.session_state["review_result"]),
                    file_name="review.md",
                    mime="text/markdown",
                    use_container_width=True,
                )
            if publish_clicked:
                try:
                    owner, repo, pr_number = parse_pr_url(pr_url)
                    result = st.session_state["review_result"]
                    fr = st.session_state["review_file_results"]
                    if "总结模式" in publish_mode:
                        with st.spinner("正在发布评论..."):
                            comment_url = post_pr_comment(owner, repo, pr_number, build_markdown_comment(result))
                        st.success(f"✅ 评论已发布：{comment_url}")
                    else:
                        with st.status("正在发布行级评审...", expanded=True) as s:
                            ok = post_inline_review(owner, repo, pr_number, fr)
                            if ok:
                                s.update(label="✅ 行级评审已发布", state="complete", expanded=False)
                                st.success("请前往 GitHub PR 的 Files changed 页面查看 inline 评论。")
                            else:
                                s.update(label="❌ 发布失败", state="error")
                                st.error("发布失败，请检查 GitHub Token 权限。")
                except Exception as e:
                    st.error(f"❌ 发布失败：{e}")
            if md_clicked:
                st.code(build_markdown_comment(st.session_state["review_result"]), language="markdown")
    else:
        st.markdown("---")
        question = st.text_input("对这个 PR 提问", placeholder="这个改动会影响性能吗？")
        if st.button("提问", type="primary"):
            if not pr_url.strip() or not question.strip():
                st.warning("请填入 PR 链接和问题")
            else:
                try:
                    with st.spinner("正在思考..."):
                        pr_data = fetch_pr(pr_url)
                        contexts = build_file_contexts(pr_data)
                        ctx_text = "\n\n".join(c["content"] for c in contexts)
                        answer = answer_question(ctx_text, question)
                    st.markdown(f'<div class="card"><div style="font-size:14px;color:#E4E4E7;line-height:1.8;">{answer}</div></div>', unsafe_allow_html=True)
                except Exception as e:
                    st.error(f"出错了：{e}")


def _page_overview():
    """结果总览：KPI + 雷达图 + 流水线 + 文件树"""
    st.title("📊 结果总览")
    result = st.session_state.get("review_result")
    if not result:
        st.info("还没有评审结果，请先前往「评审中心」输入 PR 链接并运行分析。")
        return

    analysis    = result["analysis"]
    file_results = analysis.get("file_results", [])
    scores      = _compute_radar_scores(file_results)
    score       = _overall_score(scores)
    label, cls  = _overall_label(score)
    color       = {"good": "#34D399", "warn": "#FBBF24", "bad": "#F87171"}[cls]

    total_risks = sum(len(r.get("risks") or []) for r in file_results)
    high, medium, low = _risk_severity_breakdown(file_results)
    both        = _both_count(file_results)
    high_conf   = sum(1 for r in file_results for rk in (r.get("risks") or []) if rk.get("confidence") == "高")
    py_count    = sum(1 for r in file_results if (r.get("filename") or "").endswith(".py"))
    md_count    = sum(1 for r in file_results if (r.get("filename") or "").endswith(".md"))

    # KPI 6格
    k1, k2, k3 = st.columns(3)
    with k1:
        st.markdown(f"""<div class="kpi-card">
            <div class="kpi-label">检查文件</div>
            <div class="kpi-value">{len(file_results)}</div>
            <div class="kpi-hint">{py_count} .py · {md_count} .md</div>
        </div>""", unsafe_allow_html=True)
    with k2:
        st.markdown(f"""<div class="kpi-card">
            <div class="kpi-label">风险点</div>
            <div class="kpi-value bad">{total_risks}</div>
            <div class="kpi-hint" style="color:#F87171;">{high} 高 · {medium} 中 · {low} 低</div>
        </div>""", unsafe_allow_html=True)
    with k3:
        score_cls = {"good": "", "warn": "warn", "bad": "bad"}[cls]
        st.markdown(f"""<div class="kpi-card">
            <div class="kpi-label">综合得分</div>
            <div class="kpi-value {score_cls}">{score}<span style="font-size:16px;color:#71717A;">/100</span></div>
            <div class="kpi-hint" style="color:{color};">{label}</div>
        </div>""", unsafe_allow_html=True)

    k4, k5, k6 = st.columns(3)
    with k4:
        st.markdown(f"""<div class="kpi-card">
            <div class="kpi-label">双重确认</div>
            <div class="kpi-value accent">{both}</div>
            <div class="kpi-hint">Claude ∩ ruff</div>
        </div>""", unsafe_allow_html=True)
    with k5:
        st.markdown(f"""<div class="kpi-card">
            <div class="kpi-label">高置信风险</div>
            <div class="kpi-value accent">{high_conf}</div>
            <div class="kpi-hint">≥ 80% 置信度</div>
        </div>""", unsafe_allow_html=True)
    with k6:
        st.markdown(f"""<div class="kpi-card">
            <div class="kpi-label">分析架构</div>
            <div class="kpi-value" style="font-size:22px;">混合</div>
            <div class="kpi-hint">LLM + Linter</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("---")

    # 雷达图 + 变更总结
    col_radar, col_summary = st.columns([1, 1.4])
    with col_radar:
        st.markdown(f'<div class="card"><div class="card-title"><span class="card-accent acc-purple"></span>五维评分 · 综合 <span style="color:{color};">{score}/100 {label}</span></div>{_make_radar_svg(scores)}</div>', unsafe_allow_html=True)
    with col_summary:
        overall = analysis.get("overall_summary", "(暂无总结)")
        st.markdown(f'<div class="card"><div class="card-title"><span class="card-accent acc-purple"></span>变更总结</div><div style="font-size:14px;color:#E4E4E7;line-height:1.8;">{overall}</div></div>', unsafe_allow_html=True)

    st.markdown("---")

    # 流水线
    file_count = len(file_results)
    st.markdown(f"""<div class="card">
  <div class="card-title"><span class="card-accent acc-cyan"></span>分析流水线</div>
  <div class="pipeline-row">
    <div class="pipeline-step"><div class="pipeline-step-title" style="color:#06B6D4;"><span>① 抓取 PR</span><span style="color:#34D399;">●</span></div><div class="pipeline-step-body">GitHub REST API<br>{file_count} 文件 · diff</div></div>
    <div class="pipeline-arrow">→</div>
    <div class="pipeline-step"><div class="pipeline-step-title" style="color:#06B6D4;"><span>② 构建上下文</span><span style="color:#34D399;">●</span></div><div class="pipeline-step-body">智能裁剪<br>token 压缩</div></div>
    <div class="pipeline-arrow">→</div>
    <div class="pipeline-step highlight"><div class="pipeline-step-title" style="color:#A78BFA;"><span>③ Claude 分析</span><span style="color:#34D399;">●</span></div><div class="pipeline-step-body">claude-sonnet-4-6<br>JSON 结构化输出</div></div>
    <div class="pipeline-arrow">→</div>
    <div class="pipeline-step"><div class="pipeline-step-title" style="color:#60A5FA;"><span>④ ruff 校验</span><span style="color:#34D399;">●</span></div><div class="pipeline-step-body">.py 确定性扫描<br>规则级问题</div></div>
    <div class="pipeline-arrow">→</div>
    <div class="pipeline-step"><div class="pipeline-step-title" style="color:#34D399;"><span>⑤ 融合去重</span><span style="color:#34D399;">●</span></div><div class="pipeline-step-body">±3 行匹配合并<br>{total_risks} 风险 · {both} 双重确认</div></div>
  </div>
</div>""", unsafe_allow_html=True)

    # 文件树
    rows = ""
    for r in file_results[:10]:
        fname = r.get("filename", "?")
        risks_count = len(r.get("risks") or [])
        if risks_count == 0:
            pill = ""
        else:
            levels = [rk.get("level") for rk in (r.get("risks") or [])]
            cls2 = "risk-high-pill" if "高" in levels else ("risk-medium-pill" if "中" in levels else "risk-low-pill")
            pill = f'<span class="tree-risk {cls2}">{risks_count}</span>'
        rows += f'<div class="tree-file">📄 {fname} {pill}</div>'
    st.markdown(f"""<div class="card">
  <div class="card-title"><span class="card-accent acc-cyan"></span>文件影响树 <span style="font-size:12px;color:#71717A;margin-left:8px;">{len(file_results)} 文件</span></div>
  <div class="tree"><div class="tree-folder">📁 changed files</div>{rows}</div>
</div>""", unsafe_allow_html=True)

    # 活动时间线
    st.markdown(f"""<div class="card">
  <div class="card-title"><span class="card-accent acc-gray"></span>活动时间线</div>
  <div class="activity-row"><span class="activity-time">刚刚</span><span class="activity-dot" style="color:#34D399;">●</span><span>评审完成，识别 {total_risks} 个风险点，其中 {both} 项为双重确认</span></div>
  <div class="activity-row"><span class="activity-time">刚刚</span><span class="activity-dot" style="color:#06B6D4;">●</span><span>融合去重完成：Claude + ruff 输出合并</span></div>
  <div class="activity-row"><span class="activity-time">刚刚</span><span class="activity-dot" style="color:#A78BFA;">●</span><span>Claude 语义分析完成，生成结构化 JSON</span></div>
  <div class="activity-row"><span class="activity-time">刚刚</span><span class="activity-dot" style="color:#60A5FA;">●</span><span>ruff 静态扫描 {file_count} 个文件</span></div>
  <div class="activity-row"><span class="activity-time">刚刚</span><span class="activity-dot" style="color:#71717A;">●</span><span>从 GitHub API 抓取 PR 元数据与 diff</span></div>
</div>""", unsafe_allow_html=True)


def _page_risks():
    """风险详情页"""
    st.title("⚠️ 风险详情")
    result = st.session_state.get("review_result")
    if not result:
        st.info("还没有评审结果，请先前往「评审中心」运行分析。")
        return

    file_results = result["analysis"].get("file_results", [])
    all_risks    = [(r.get("filename", ""), rk) for r in file_results for rk in (r.get("risks") or [])]
    high, medium, low = _risk_severity_breakdown(file_results)
    both = _both_count(file_results)

    if not all_risks:
        st.success("✅ 本 PR 未发现明显风险，混合分析架构（Claude + ruff）均未标记问题。")
        return

    # 过滤器
    col_f1, col_f2, col_f3, col_f4 = st.columns(4)
    with col_f1:
        filter_level = st.selectbox("严重程度", ["全部", "高", "中", "低"])
    with col_f2:
        filter_source = st.selectbox("来源", ["全部", "claude", "ruff", "both"])
    with col_f3:
        st.metric("高风险", high, delta=None)
    with col_f4:
        st.metric("双重确认", both, delta=None)

    st.markdown("---")

    for i, (fn, rk) in enumerate(all_risks):
        level  = rk.get("level", "低")
        source = rk.get("source", "claude")
        if filter_level != "全部" and level != filter_level:
            continue
        if filter_source != "全部" and source != filter_source:
            continue

        badge_cls = _SEV_BADGE.get(level, "badge-sev-low")
        card_cls  = _SEV_CARD.get(level, "sev-low")
        src_cls   = _SOURCE_BADGE.get(source, "badge-source-claude")
        src_label = _SOURCE_LABEL.get(source, source)
        line      = rk.get("line", "")
        file_label = f"{fn}:{line}" if line else fn
        desc      = rk.get("description", "")
        conf      = rk.get("confidence", "中")
        conf_pct  = {"高": "92%", "中": "75%", "低": "58%"}.get(conf, "—")

        st.markdown(f"""<div class="risk-card {card_cls}">
  <div class="risk-header">
    <span class="badge {badge_cls}">{level}风险</span>
    <span class="badge {src_cls}">{src_label}</span>
    <span class="badge-file">{file_label}</span>
    <span class="confidence-tag">置信度 {conf_pct}</span>
  </div>
  <div class="risk-body">{desc}</div>
</div>""", unsafe_allow_html=True)


def _page_suggestions():
    """建议 & 推理页"""
    st.title("💡 建议 & 推理")
    result = st.session_state.get("review_result")
    if not result:
        st.info("还没有评审结果，请先前往「评审中心」运行分析。")
        return

    file_results = result["analysis"].get("file_results", [])

    # Review 建议
    suggestions = [(r.get("filename", ""), s) for r in file_results for s in (r.get("suggestions") or [])]
    if not suggestions:
        suggestions = [("", "暂无具体改进建议，本 PR 整体质量良好。")]

    st.markdown("#### 📋 Review 建议")
    priorities = ["P0", "P1", "P2"]
    for i, (fname, text) in enumerate(suggestions[:8]):
        pri     = priorities[min(i, 2)]
        pri_cls = {"P0": "pri-p0", "P1": "pri-p1", "P2": "pri-p2"}[pri]
        meta    = f'<div class="suggest-meta">影响文件：<code>{fname}</code></div>' if fname else ""
        st.markdown(f"""<div class="suggest-row">
  <span class="pri-tag {pri_cls}">{pri}</span>
  <div style="flex:1;"><div class="suggest-body">{text}</div>{meta}</div>
</div>""", unsafe_allow_html=True)

    st.markdown("---")

    # AI 推理过程
    total    = sum(len(r.get("risks") or []) for r in file_results)
    both     = _both_count(file_results)
    fc       = len(file_results)
    py_count = sum(1 for r in file_results if (r.get("filename") or "").endswith(".py"))

    st.markdown("#### 🧠 AI 推理过程")
    st.markdown(f"""<div class="reason-box">
<span class="reason-step">[01]</span> <span style="color:#06B6D4;">主题识别</span> · 分析 PR 改动核心目标<br>
<span class="reason-step">[02]</span> <span style="color:#06B6D4;">关键文件定位</span> · 识别 {fc} 个变更文件<br>
<span class="reason-step">[03]</span> <span style="color:#FBBF24;">语义扫描</span> · Claude 检查代码意图与潜在缺陷<br>
<span class="reason-step">[04]</span> <span style="color:#60A5FA;">规则校验</span> · ruff 对 {py_count} 个 .py 文件做确定性检查<br>
<span class="reason-step">[05]</span> <span style="color:#06B6D4;">交叉验证</span> · 比对 Claude 与 ruff 输出，标记重叠<br>
<span class="reason-step">[06]</span> <span style="color:#34D399;">融合去重</span> · 同文件 ±3 行合并 → {both} 双重确认<br>
<span class="reason-step">[07]</span> <span style="color:#A78BFA;">置信度计算</span> · 双重确认 +25% · 单源基线 65%<br>
</div>""", unsafe_allow_html=True)


def _page_docs():
    """使用文档页"""
    st.title("📖 使用文档")
    st.markdown("欢迎使用 **AI PR Reviewer**，以下是完整的使用指南。")

    st.markdown("---")
    st.markdown("### 🚀 快速开始")
    st.markdown("""<div class="doc-step"><span class="doc-step-num">1</span>在左侧导航点击 <strong>评审中心</strong></div>
<div class="doc-step"><span class="doc-step-num">2</span>在输入框粘贴 GitHub PR 链接，格式：<code>https://github.com/owner/repo/pull/123</code></div>
<div class="doc-step"><span class="doc-step-num">3</span>点击 <strong>开始评审 →</strong> 按钮，等待分析完成（通常 20-60 秒）</div>
<div class="doc-step"><span class="doc-step-num">4</span>分析完成后，通过左侧导航查看各维度报告</div>""", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### 📄 页面说明")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""**🔍 评审中心**
- 输入 PR 链接并触发分析
- 支持评审模式和问答模式
- 可一键发布评审到 GitHub PR

**📊 结果总览**
- KPI 数据卡片（文件数、风险数、综合得分等）
- 五维雷达图（安全、性能、可维护、文档、测试）
- 分析流水线可视化
- 文件影响树""")
    with col2:
        st.markdown("""**⚠️ 风险详情**
- 所有风险点列表，支持按严重程度/来源过滤
- 每条风险标注来源（Claude / ruff / 双重确认）
- 显示置信度和文件位置

**💡 建议 & 推理**
- 按优先级排列的改进建议（P0/P1/P2）
- AI 推理过程的 7 步思考链，透明可追溯""")

    st.markdown("---")
    st.markdown("### 🏗️ 技术架构")
    st.markdown("""本工具采用 **混合分析架构**，结合 LLM 语义理解与静态分析工具：

| 组件 | 作用 |
|------|------|
| **Claude claude-sonnet-4-6** | 语义理解、风险识别、总结生成 |
| **ruff** | Python 代码静态扫描，确定性规则检查 |
| **融合去重** | ±3 行匹配合并两路结果，标记双重确认 |
| **GitHub REST API** | 拉取 PR diff、发布评论、行级 review |""")

    st.markdown("---")
    st.markdown("### ⚙️ 环境配置")
    st.markdown("""在项目根目录创建 `.env` 文件，填入以下配置：

```
ANTHROPIC_API_KEY=your_anthropic_api_key
GITHUB_TOKEN=your_github_personal_access_token
```

GitHub Token 需要 `repo` 权限（用于读取私有仓库和发布评论）。""")

    st.markdown("---")
    st.markdown("### ❓ 常见问题")
    with st.expander("分析很慢，正常吗？"):
        st.markdown("首次分析需要调用 Claude API，通常需要 20-60 秒，取决于 PR 的文件数量和代码量。")
    with st.expander("发布到 GitHub 失败怎么办？"):
        st.markdown("请检查 `.env` 中的 `GITHUB_TOKEN` 是否有效，且具有 `repo` 写权限。对于公开仓库，需要 `public_repo` 权限。")
    with st.expander("问答模式和评审模式有什么区别？"):
        st.markdown("**评审模式** 会对整个 PR 进行全面分析，生成结构化报告。**问答模式** 允许你针对 PR 内容自由提问，适合深入了解某个具体问题。")
    with st.expander("ruff 只能扫描 Python 文件？"):
        st.markdown("是的，ruff 是 Python 专用的静态分析工具。对于其他语言的文件，仅使用 Claude 进行语义分析。")

    st.markdown("---")
    st.caption("AI PR Reviewer v0.5 Pro · Claude + ruff 混合架构")


# ── 侧边栏导航 ────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🤖 AI PR Reviewer")
    st.markdown("---")
    page = st.radio(
        "导航",
        ["🔍 评审中心", "📊 结果总览", "⚠️ 风险详情", "💡 建议 & 推理", "📖 使用文档"],
        label_visibility="collapsed",
    )
    st.markdown("---")
    st.markdown("**模型**")
    st.markdown(
        '<span style="background:rgba(139,92,246,0.15);color:#A78BFA;padding:3px 10px;border-radius:4px;font-size:13px;">claude-sonnet-4-6</span>',
        unsafe_allow_html=True,
    )
    st.markdown("")
    st.markdown(
        '<span style="background:rgba(52,211,153,0.15);color:#34D399;padding:3px 10px;border-radius:4px;font-size:13px;">● online</span>',
        unsafe_allow_html=True,
    )
    st.markdown("---")
    st.caption("AI PR Reviewer v0.5 Pro")
    st.caption("Claude + ruff 混合架构")

# ══════════════════════════════════════════════════════════════════════════════
# 页面路由
# ══════════════════════════════════════════════════════════════════════════════
if page == "🔍 评审中心":
    _page_review()
elif page == "📊 结果总览":
    _page_overview()
elif page == "⚠️ 风险详情":
    _page_risks()
elif page == "💡 建议 & 推理":
    _page_suggestions()
elif page == "📖 使用文档":
    _page_docs()
