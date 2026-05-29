# 🤖 AI PR Review 助手

> 七牛云 × XEngineer 暑期实训营 · 题目三作品
> 输入一个 GitHub PR 链接，AI 自动分析代码变更，输出**变更总结 / 风险识别 / Review 建议**。

> 📌 **提交前请先阅读 [`提交指南.md`](提交指南.md)** —— 里面说明了还需补充什么、以及如何提交到 GitHub。

---

## 📸 运行效果

> ⚠️ 待补充：在此处放 2–3 张实际运行截图（网页评审结果、命令行报告）。
> 截图后用 `![评审结果](docs/screenshot1.png)` 这样的语法插入。演示视频链接也放这里。

---

## ✨ 功能

- **自动取数**：给一个 GitHub PR 链接，自动拉取代码改动（diff）。
- **三类输出**：变更总结、风险代码识别（含等级与置信度）、Review 建议。
- **混合分析架构**：LLM（语义问题）+ ruff 静态检查（确定性问题），降低误报。
- **简化版 PR 压缩**：按文件信息价值排序、预算内分配，大 PR 也能有效分析。
- **两种交互**：命令行 + Streamlit 网页；网页含评审模式与问答模式。
- **小型评估脚本**：用已知问题量化召回率，体现 precision/recall 思维。
- **可配置关注点**：通过 `review_config.yaml` 注入团队自定义规则。

---

## 🚀 快速开始

### 1. 安装依赖
```bash
python -m venv venv
# Windows: venv\Scripts\activate
# Mac/Linux: source venv/bin/activate
pip install -r requirements.txt
```

### 2. 配置密钥
复制 `.env.example` 为 `.env`，填入两把钥匙：
```
GITHUB_TOKEN=你的github_token        # github.com Settings → Developer settings 生成
ANTHROPIC_API_KEY=你的anthropic_key  # console.anthropic.com 生成（需有额度）
```

### 3. 运行
```bash
# 命令行
python main.py

# 网页（推荐路演用）
streamlit run app.py

# 单独验证取数模块
python src/github_client.py

# 运行评估（需先在 eval/cases.json 填入真实 PR 与已知问题）
python eval/run_eval.py
```

---

## 📂 项目结构

```
ai-pr-reviewer/
├── main.py                 # 命令行入口
├── app.py                  # Streamlit 网页入口
├── review_config.yaml      # 可选：自定义评审关注点
├── src/
│   ├── github_client.py    # 取数：PR链接 → diff
│   ├── context_builder.py  # 上下文组织（简化版 PR 压缩）
│   ├── prompts.py          # 提示词模板（JSON 化）
│   ├── analyzer.py         # 调用 Claude + 健壮 JSON 解析
│   ├── static_analyzer.py  # ruff 静态检查（混合架构）
│   ├── pipeline.py         # 流程编排（合并 LLM + 静态分析）
│   └── reporter.py         # 命令行报告格式化
├── eval/
│   ├── cases.json          # 评估用例
│   └── run_eval.py         # 评估脚本（召回率）
└── docs/
    └── architecture.md     # 架构与设计决策说明
```

---

## 🧠 设计说明

详见 [`docs/architecture.md`](docs/architecture.md)，回答了题目要求的三点：模型选择、上下文获取方式、未来扩展方向。

---

## ⚙️ 技术栈

Python · Anthropic Claude API (`claude-sonnet-4-6`) · requests · Streamlit · ruff
