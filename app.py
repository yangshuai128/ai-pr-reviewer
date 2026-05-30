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

st.set_page_config(page_title="AI PR Review 助手", page_icon="🤖", layout="wide")

st.title("🤖 AI PR Review 助手")
st.caption("输入 GitHub PR 链接，AI 自动分析代码改动、识别风险、给出建议")

mode = st.radio("模式", ["评审模式", "问答模式"], horizontal=True)
pr_url = st.text_input("GitHub PR 链接",
                       placeholder="https://github.com/owner/repo/pull/123")

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
                    st.success("评审完成！")

                    import pandas as pd
                    import plotly.express as px

                    file_results = analysis.get("file_results", [])

                    # ══ 评审概览 ══════════════════════════════════════════
                    st.subheader("📊 评审概览")

                    # ── 模块A：统计卡片 ──────────────────────────────────
                    total_risks = sum(len(r.get("risks") or []) for r in file_results)
                    high_conf_risks = sum(
                        1 for r in file_results
                        for rk in (r.get("risks") or [])
                        if rk.get("confidence") == "高"
                    )
                    col1, col2, col3 = st.columns(3)
                    col1.metric("📁 文件数", len(file_results))
                    col2.metric("⚠️ 风险点总数", total_risks)
                    col3.metric("🎯 高置信度风险", high_conf_risks)

                    # ── 模块B：文件改动统计 - 水平柱状图 ─────────────────
                    df_bar = pd.DataFrame({
                        "文件名": [r.get("filename", "未知") for r in file_results],
                        "风险数": [len(r.get("risks") or []) for r in file_results],
                    })
                    fig_bar = px.bar(
                        df_bar, x="风险数", y="文件名", orientation="h",
                        title="各文件风险点数量",
                        labels={"风险数": "风险点数量", "文件名": ""},
                        color_discrete_sequence=["#1890ff"],
                    )
                    fig_bar.update_layout(yaxis={"categoryorder": "total ascending"})
                    st.plotly_chart(fig_bar, use_container_width=True)

                    # ── 模块C：风险等级分布 - 饼图 ───────────────────────
                    level_counts = {"高": 0, "中": 0, "低": 0}
                    for r in file_results:
                        for rk in (r.get("risks") or []):
                            level = rk.get("level", "")
                            if level in level_counts:
                                level_counts[level] += 1
                    if sum(level_counts.values()) == 0:
                        st.info("本 PR 未发现明显风险")
                    else:
                        df_pie = pd.DataFrame({
                            "等级": list(level_counts.keys()),
                            "数量": list(level_counts.values()),
                        })
                        fig_pie = px.pie(
                            df_pie, names="等级", values="数量",
                            title="风险等级分布",
                            color="等级",
                            color_discrete_map={"高": "#ff4d4f", "中": "#faad14", "低": "#1890ff"},
                        )
                        st.plotly_chart(fig_pie, use_container_width=True)

                    # ══ 评审详情 ══════════════════════════════════════════
                    st.subheader("📋 整体总结")
                    st.write(analysis["overall_summary"])

                    st.subheader("📁 各文件详情")
                    for r in analysis["file_results"]:
                        with st.expander(f"📄 {r['filename']}"):
                            st.markdown(f"**总结**：{r.get('summary', '')}")

                            risks = r.get("risks", [])
                            if risks:
                                st.markdown("**风险点（AI 语义分析）：**")
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
            except Exception as e:
                st.error(f"出错了：{e}")

else:  # 问答模式
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
