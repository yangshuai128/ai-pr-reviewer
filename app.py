"""
Streamlit 网页界面。运行：streamlit run app.py
两种模式：评审模式（总结+风险+建议+静态检查）/ 问答模式（对 PR 自由提问）。
"""
import streamlit as st

from src.github_client import fetch_pr, parse_pr_url, post_pr_comment
from src.context_builder import build_file_contexts
from src.analyzer import answer_question
from src.pipeline import run_review
from src.reporter import build_markdown_comment

# ── 自定义 CSS ────────────────────────────────────────────────────────────────
CUSTOM_CSS = """
<style>
/* 全局字体与排版优化 */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');
html, body, [class*="css"] { font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif; }

/* Hero 区：增加微发光效果 */
.hero-card { background: #fff; border-radius: 12px; border: 1px solid #E1E4E8; padding: 1.5rem; display: flex; align-items: center; gap: 16px; margin-bottom: 1.5rem; box-shadow: 0 2px 8px rgba(27, 31, 36, 0.04); }
.hero-logo { width: 48px; height: 48px; border-radius: 10px; background: linear-gradient(135deg, #EEEDFE 0%, #E0DEFD 100%); display: flex; align-items: center; justify-content: center; font-size: 24px; box-shadow: inset 0 0 0 1px rgba(83, 74, 183, 0.1); }
.hero-title { font-size: 20px; font-weight: 600; color: #24292F; letter-spacing: -0.5px; }
.hero-tagline { font-size: 14px; color: #57606A; margin-top: 4px; }

/* KPI 卡片：增加悬浮反馈感 */
.kpi-card { background: #fff; border-radius: 10px; padding: 1.25rem; border: 1px solid #E1E4E8; box-shadow: 0 1px 3px rgba(27, 31, 36, 0.04); transition: transform 0.2s ease, box-shadow 0.2s ease; }
.kpi-card:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(27, 31, 36, 0.08); }
.kpi-card.risk-high { background: #FEF0F0; border-color: #FBC4C4; }
.kpi-card.risk-medium { background: #FDF6EC; border-color: #F5DAB1; }
.kpi-card.risk-low { background: #F0F9EB; border-color: #C2E7B0; }
.kpi-label { font-size: 13px; color: #57606A; margin-bottom: 8px; font-weight: 500; text-transform: uppercase; letter-spacing: 0.5px; }
.kpi-value { font-size: 28px; font-weight: 600; color: #24292F; line-height: 1; }

/* 风险详情卡片：增加左侧严重度色带识别 (Stripe/GitHub 风格) */
.section-card { background: #fff; border-radius: 12px; border: 1px solid #E1E4E8; padding: 1.5rem; margin-bottom: 1.5rem; box-shadow: 0 1px 3px rgba(27, 31, 36, 0.02); }
.section-title { font-size: 18px; font-weight: 600; color: #24292F; margin-bottom: 1.25rem; letter-spacing: -0.3px; }

.risk-card { background: #fff; border: 1px solid #E1E4E8; border-radius: 8px; padding: 14px 16px; margin-bottom: 12px; border-left: 4px solid #D0D7DE; transition: box-shadow 0.2s ease; }
.risk-card:hover { box-shadow: 0 3px 8px rgba(27, 31, 36, 0.06); }
.risk-card.sev-high { border-left-color: #CF222E; }
.risk-card.sev-medium { border-left-color: #9A6700; }
.risk-card.sev-low { border-left-color: #1A7F37; }

/* 徽章设计优化：更圆润、更现代 */
.risk-header { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; margin-bottom: 8px; }
.badge { font-size: 12px; padding: 2px 10px; border-radius: 12px; display: inline-block; font-weight: 500; }
.badge-file { font-size: 13px; color: #57606A; font-family: ui-monospace, SFMono-Regular, "SF Mono", Menlo, monospace; background: #F6F8FA; padding: 2px 8px; border-radius: 6px; }
.badge-sev-high { background: #FFEBE9; color: #CF222E; border: 1px solid rgba(207, 34, 46, 0.15); }
.badge-sev-medium { background: #FFF8C5; color: #9A6700; border: 1px solid rgba(154, 103, 0, 0.15); }
.badge-sev-low { background: #DAFBE1; color: #1A7F37; border: 1px solid rgba(26, 127, 55, 0.15); }
.badge-source-both { background: #F4F1FF; color: #534AB7; border: 1px solid rgba(83, 74, 183, 0.15); }
.badge-source-claude { background: #E6FFFA; color: #04724D; border: 1px solid rgba(4, 114, 77, 0.15); }
.badge-source-ruff { background: #E1F0FF; color: #0969DA; border: 1px solid rgba(9, 105, 218, 0.15); }

.risk-body { font-size: 14px; color: #24292F; line-height: 1.6; }
.app-footer { text-align: center; margin-top: 3rem; color: #8C959F; font-size: 12px; padding-top: 1rem; border-top: 1px solid #E1E4E8; }
</style>
"""

# ── 示例 PR 映射 ──────────────────────────────────────────────────────────────
EXAMPLE_PRS = {
    "自定义...": "",
    "PyGithub #3294": "https://github.com/PyGithub/PyGithub/pull/3294",
    "本仓库 PR #1": "https://github.com/yangshuai128/ai-pr-reviewer/pull/1",
    "本仓库 PR #2": "https://github.com/yangshuai128/ai-pr-reviewer/pull/2",
    "本仓库 PR #3": "https://github.com/yangshuai128/ai-pr-reviewer/pull/3",
}

# ── 辅助：把风险等级汉字映射到 CSS 类 ─────────────────────────────────────────
_SEV_CLASS = {"高": "badge-sev-high", "中": "badge-sev-medium", "低": "badge-sev-low"}
_SEV_DEFAULT = "badge-sev-low"

_SOURCE_CLASS = {"both": "badge-source-both", "claude": "badge-source-claude", "ruff": "badge-source-ruff"}
_SOURCE_LABEL = {
    "both":   "🛡️ 双重确认 · Claude + ruff",
    "claude": "🧠 来源 · Claude",
    "ruff":   "🔧 来源 · ruff",
}


# 风险等级汉字 → 左侧色带 CSS 类
_SEV_CARD_CLASS = {"高": "sev-high", "中": "sev-medium", "低": "sev-low"}


def _risk_card_html(rk: dict, filename: str) -> str:
    level = rk.get("level", "低")
    badge_cls = _SEV_CLASS.get(level, _SEV_DEFAULT)
    card_sev_cls = _SEV_CARD_CLASS.get(level, "sev-low")
    line = rk.get("line", "")
    file_label = f"{filename}:{line}" if line else filename
    source = rk.get("source", "claude")
    src_cls = _SOURCE_CLASS.get(source, "badge-source-claude")
    src_label = _SOURCE_LABEL.get(source, source)
    desc = rk.get("description", "")
    return (
        f'<div class="risk-card {card_sev_cls}">'
        f'<div class="risk-header">'
        f'<span class="badge {badge_cls}">{level}</span>'
        f'<span class="badge-file">{file_label}</span>'
        f'<span class="badge {src_cls}">{src_label}</span>'
        f'</div>'
        f'<div class="risk-body">{desc}</div>'
        f'</div>'
    )


def _overall_risk_class(file_results: list) -> str:
    """综合风险等级：有高→red，有中→yellow，否则→green。"""
    levels = [rk.get("level", "") for r in file_results for rk in r.get("risks", [])]
    if "高" in levels:
        return "risk-high", "高"
    if "中" in levels:
        return "risk-medium", "中"
    return "risk-low", "低"


# ── 页面配置 ──────────────────────────────────────────────────────────────────
st.set_page_config(page_title="AI PR Reviewer", page_icon="🤖", layout="wide")
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# ── Hero ──────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero-card">
  <div class="hero-logo">🤖</div>
  <div>
    <div class="hero-title">AI PR Reviewer</div>
    <div class="hero-tagline">智能 Pull Request 评审 · Claude + ruff 混合架构</div>
  </div>
</div>
""", unsafe_allow_html=True)

# ── 模式切换 ──────────────────────────────────────────────────────────────────
mode = st.radio("模式", ["评审模式", "问答模式"], horizontal=True)

# ── 输入区 ────────────────────────────────────────────────────────────────────
# 示例 PR 下拉框：选中后自动填入 session_state
example_choice = st.selectbox("示例 PR", list(EXAMPLE_PRS.keys()))
if example_choice != "自定义...":
    st.session_state["pr_url"] = EXAMPLE_PRS[example_choice]

pr_url = st.text_input(
    "PR 链接",
    value=st.session_state.get("pr_url", ""),
    placeholder="https://github.com/owner/repo/pull/123",
    key="pr_url_input",
)
# 同步回 session_state（用户手动输入时）
st.session_state["pr_url"] = pr_url

# ── 评审模式 ──────────────────────────────────────────────────────────────────
if mode == "评审模式":
    if st.button("开始评审", type="primary"):
        if not pr_url.strip():
            st.warning("请先输入 PR 链接")
        else:
            try:
                with st.spinner("正在拉取并分析（首次可能需要几十秒）..."):
                    result = run_review(pr_url)

                if result["analysis"] is None:
                    st.info("没有可分析的代码改动。")
                else:
                    analysis = result["analysis"]
                    file_results = analysis.get("file_results", [])

                    # ── KPI 四卡片 ────────────────────────────────────────
                    total_files = len(file_results)
                    total_risks = sum(len(r.get("risks") or []) for r in file_results)
                    high_conf = sum(
                        1 for r in file_results
                        for rk in (r.get("risks") or [])
                        if rk.get("confidence") == "高"
                    )
                    overall_cls, overall_label = _overall_risk_class(file_results)

                    c1, c2, c3, c4 = st.columns(4)
                    c1.markdown(
                        f'<div class="kpi-card"><div class="kpi-label">检查文件</div>'
                        f'<div class="kpi-value">{total_files}</div></div>',
                        unsafe_allow_html=True,
                    )
                    c2.markdown(
                        f'<div class="kpi-card"><div class="kpi-label">风险点</div>'
                        f'<div class="kpi-value">{total_risks}</div></div>',
                        unsafe_allow_html=True,
                    )
                    c3.markdown(
                        f'<div class="kpi-card"><div class="kpi-label">高置信</div>'
                        f'<div class="kpi-value">{high_conf}</div></div>',
                        unsafe_allow_html=True,
                    )
                    c4.markdown(
                        f'<div class="kpi-card {overall_cls}"><div class="kpi-label">综合风险</div>'
                        f'<div class="kpi-value">{overall_label}</div></div>',
                        unsafe_allow_html=True,
                    )

                    st.write("")  # 间距

                    # ── 整体总结 ──────────────────────────────────────────
                    st.markdown('<div class="section-card"><div class="section-title">📋 整体总结</div>', unsafe_allow_html=True)
                    st.write(analysis["overall_summary"])
                    st.markdown('</div>', unsafe_allow_html=True)

                    # ── 风险点详情 ────────────────────────────────────────
                    all_risks = [
                        (r.get("filename", ""), rk)
                        for r in file_results
                        for rk in r.get("risks", [])
                    ]
                    if all_risks:
                        st.markdown('<div class="section-card"><div class="section-title">⚠️ 风险点详情</div>', unsafe_allow_html=True)
                        for fname, rk in all_risks:
                            st.markdown(_risk_card_html(rk, fname), unsafe_allow_html=True)
                        st.markdown('</div>', unsafe_allow_html=True)
                    else:
                        st.success("本 PR 未发现明显风险")

                    # ── 柱状图 ────────────────────────────────────────────
                    import pandas as pd
                    import plotly.express as px

                    st.markdown('<div class="section-title">每个文件的风险数</div>', unsafe_allow_html=True)
                    df_bar = pd.DataFrame({
                        "文件名": [r.get("filename", "未知") for r in file_results],
                        "风险数": [len(r.get("risks") or []) for r in file_results],
                    })
                    fig_bar = px.bar(
                        df_bar, x="风险数", y="文件名", orientation="h",
                        labels={"风险数": "风险点数量", "文件名": ""},
                        color_discrete_sequence=["#7F77DD"],
                    )
                    fig_bar.update_layout(
                        yaxis={"categoryorder": "total ascending"},
                        paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor="rgba(0,0,0,0)",
                        font={"size": 13},
                        margin={"t": 10},
                    )
                    st.plotly_chart(fig_bar, use_container_width=True)

                    # ── 各文件详情（折叠） ────────────────────────────────
                    st.subheader("📁 各文件详情")
                    for r in file_results:
                        with st.expander(f"📄 {r['filename']}"):
                            st.markdown(f"**总结**：{r.get('summary', '')}")

                            risks = r.get("risks", [])
                            if risks:
                                st.markdown("**风险点：**")
                                for rk in risks:
                                    st.markdown(
                                        f"- `{rk.get('level', '?')}风险/"
                                        f"置信度{rk.get('confidence', '?')}` "
                                        f"{rk.get('description', '')}")
                            else:
                                st.markdown("**风险点：** 未发现明显风险")

                            static_issues = r.get("static_issues", [])
                            if static_issues:
                                st.markdown("**静态检查（ruff，确定性问题）：**")
                                for s in static_issues:
                                    st.markdown(
                                        f"- `{s.get('code', '?')}` 第{s.get('line', '?')}行 "
                                        f"{s.get('message', '')}")

                            sugg = r.get("suggestions", [])
                            if sugg:
                                st.markdown("**改进建议：**")
                                for s in sugg:
                                    st.markdown(f"- {s}")

<<<<<<< HEAD
                    # ── 操作按钮 ──────────────────────────────────────────
                    st.divider()
                    btn_col1, btn_col2, btn_col3 = st.columns(3)

                    with btn_col1:
                        if st.button("📤 发布到 GitHub PR", type="primary"):
                            try:
                                owner, repo, pr_number = parse_pr_url(pr_url)
                                comment_url = post_pr_comment(
                                    owner, repo, pr_number, build_markdown_comment(result)
                                )
                                st.success(f"✅ 评论已发布：{comment_url}")
                            except Exception as e:
                                st.error(f"❌ 发布失败：{e}")

                    with btn_col2:
                        if st.button("📄 复制 Markdown"):
                            md_text = build_markdown_comment(result)
                            st.code(md_text, language="markdown")

                    with btn_col3:
                        md_export = build_markdown_comment(result)
                        st.download_button(
                            "⬇ 导出报告",
                            data=md_export,
                            file_name="review.md",
                            mime="text/markdown",
                        )

=======
                    # ── 发布到 GitHub PR ──────────────────────────────────
                    st.divider()
                    if st.button("📤 发布到 GitHub PR"):
                        try:
                            owner, repo, pr_number = parse_pr_url(pr_url)
                            comment_body = build_markdown_comment(result)
                            with st.spinner("正在发布评论..."):
                                html_url = post_pr_comment(owner, repo, pr_number, comment_body)
                            st.success(f"✅ 评论已发布：{html_url}")
                        except Exception as post_err:
                            st.error(f"发布失败：{post_err}")
>>>>>>> main
            except Exception as e:
                st.error(f"出错了：{e}")

# ── 问答模式 ──────────────────────────────────────────────────────────────────
else:
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
                st.write(answer)
            except Exception as e:
                st.error(f"出错了：{e}")

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="app-footer">
  AI PR Reviewer · 七牛云 × XEngineer 实训营 ·
  <a href="https://github.com/yangshuai128/ai-pr-reviewer">GitHub</a>
</div>
""", unsafe_allow_html=True)
