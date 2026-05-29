# 🤖 AI PR Review 助手

> 七牛云 × XEngineer 暑期实训营 · 题目三作品
> 输入一个 GitHub PR 链接，AI 自动分析代码变更，输出**变更总结 / 风险识别 / Review 建议**。

> 📌 **提交前请先阅读 [`提交指南.md`](提交指南.md)** —— 里面说明了还需补充什么、以及如何提交到 GitHub。

---

## 📖 项目背景

本项目是**七牛云 × XEngineer 暑期实训营题目三**的参赛作品。

题目要求：基于大语言模型（LLM）构建一个 AI 代码评审助手，能够自动分析 GitHub Pull Request 的代码改动，输出变更总结、风险识别和改进建议，并体现对 PR-Agent、CodeRabbit 等业界工具的理解与原创实现。

---

## 📸 运行截图

（待补充）

---

## 🎬 演示视频

（待补充）

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

## 📦 第三方依赖说明

| 包名 | 作用 |
|------|------|
| `requests` | 调用 GitHub REST API，拉取 PR 基本信息和 diff 文件列表 |
| `anthropic` | 官方 Python SDK，调用 Claude 模型进行语义分析和问答 |
| `streamlit` | 构建网页交互界面，提供评审模式和问答模式两种入口 |
| `python-dotenv` | 从 `.env` 文件加载 API 密钥等敏感配置，避免硬编码 |
| `ruff` | 高性能 Python 静态检查工具，用于混合架构中的确定性问题检测 |
| `pyyaml` | 解析 `review_config.yaml`，支持用户自定义评审关注点 |

---

## 💡 原创性声明

### 设计思路参考（仅理念，代码原创）

- **PR-Agent 的 PR 压缩策略**：启发了按文件信息价值排序、在总字符预算内分配上下文的思路（`context_builder.py`）
- **CodeRabbit / Kodus 的 LLM + 静态混合架构**：启发了将 LLM 语义分析与 ruff 确定性检查分离、合并输出的设计（`static_analyzer.py` + `pipeline.py`）

### 原创实现

- **PR 链接解析**：正则解析 GitHub PR URL，自动翻页拉取所有改动文件（`github_client.py`）
- **上下文压缩与排序**：按 churn 量和文件类型打分排序，超预算时只保留变化行而非粗暴截断（`context_builder.py`）
- **健壮 JSON 解析**：用正则提取模型返回中的第一个 `{...}`，容忍前后多余文字，失败时优雅兜底（`analyzer.py`）
- **模块化流程编排**：将取数、上下文、LLM 分析、静态分析四个模块解耦，通过 `pipeline.py` 统一编排，CLI 和网页共用同一套逻辑
- **CJK 友好的评估匹配**：评估脚本使用子串匹配而非精确匹配，适配中文风险描述（`eval/run_eval.py`）

---

## ⚙️ 技术栈

Python · Anthropic Claude API (`claude-sonnet-4-6`) · requests · Streamlit · ruff
