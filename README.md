# 🤖 AI PR Reviewer - 大厂级智能代码评审助手

> 🚀 **七牛云 × XEngineer 暑期实训营 · 参赛作品**

## 🎥 Demo 演示视频
**👉 [点击此处观看作品演示视频 (Bilibili)]
【【七牛云×XEngineer实训营】AI PR Reviewer作品演示】 https://www.bilibili.com/video/BV1SLVQ6cEw3/?share_source=copy_web&vd_source=ed1d1da6dd686d82ccbd039aa792af70
*(注：请评委老师优先观看视频，内含核心的"前后端一体化行级精准评论"功能震撼演示)*

---

## 🛠️ 第三方依赖说明 (合规声明)
本项目在开发过程中，使用了以下第三方库与框架：
1. **Streamlit**: 用于构建多页面（Multi-page）、响应式的深色系极客风前端数据看板。
2. **Anthropic (Claude)**: 接入 `claude-sonnet-4-6` 模型，用于代码的语义理解、意图分析与总结。
3. **ruff**: 采用其作为本地 Python 静态分析(Linter)引擎，进行确定性的规则扫描。
4. **PyGithub / requests**: 用于与 GitHub REST API 进行通信，拉取 PR 数据及发布评论。

## 💡 原创功能声明 (合规声明)
本项目严格遵守独立开发的原则，以下核心逻辑与架构均由本人**自主设计并手写原创实现**：
1. **多页面路由看板架构**: 原创设计并手写了基于 `st.session_state` 的多页面解耦与数据共享前端架构。
2. **混合分析与融合去重算法**: 原创实现了将大语言模型（Claude）的主观语义分析与静态代码检查（ruff）的客观结果进行 `±3行` 误差容忍的物理合并，并独创了"双重确认 (BOTH)"的高置信度徽章打标算法。
3. **行级精准发布控制台 (Inline Review)**: 原创攻克了 GitHub API 行级评论挂载的底层逻辑，实现了能够动态解析全网任意公开 PR 链接，并将风险点通过 Streamlit 状态机"像导弹一样"精准击中并挂载到 GitHub `Files changed` 具体代码行的全套前后端联动闭环。

---

## 🚀 快速启动与测试方式
1. 克隆本项目并在根目录创建 `.env` 文件，填入 `ANTHROPIC_API_KEY` 与 `GITHUB_TOKEN` (需 repo 权限)。
2. 安装依赖：`pip install -r requirements.txt`
3. 运行项目：`streamlit run app.py`
4. 在左侧边栏【评审中心】输入任意公开的 GitHub PR 链接，选择"行级精准模式 🔥"即可体验全流程。
