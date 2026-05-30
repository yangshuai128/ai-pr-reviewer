"""
模块1：GitHub 取数
职责：把一个 PR 链接 -> 结构化的 PR 数据（标题、描述、改动文件及其 diff）
单独运行可自测：python src/github_client.py
"""
import re
import os
import requests
from urllib.parse import unquote
from dotenv import load_dotenv

load_dotenv()  # 读取 .env 里的密钥


def parse_pr_url(url: str):
    """从 PR 链接中解析出 owner / repo / pr_number。
    支持形如 https://github.com/owner/repo/pull/123 的链接。

    URL 清洗（自评审 PR #2 时发现的真实 bug）：
    1. unquote 解码 URL 编码字符（如 %20 → 空格）
    2. 截断中文字符及其后内容（用户粘贴时可能带入中文说明文字）
    3. strip 去除首尾空白
    """
    url = unquote(url).strip()
    # 截断第一个中文字符（及之后所有内容），避免脏 URL 干扰正则匹配
    url = re.sub(r'[\u4e00-\u9fff\s].*$', '', url)
    pattern = r"github\.com/([^/]+)/([^/]+)/pull/(\d+)"
    match = re.search(pattern, url)
    if not match:
        raise ValueError(f"无法解析的 PR 链接：{url}")
    return match.group(1), match.group(2), int(match.group(3))


def _headers():
    """构造请求头，带上 token（如果有的话）。"""
    headers = {"Accept": "application/vnd.github+json"}
    token = os.getenv("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def _fetch_all_files(base: str):
    """拉取 PR 的所有改动文件，自动翻页。
    GitHub /files 接口默认每页 30 个、最多 100 个，大 PR 必须翻页，否则会漏文件。
    """
    files_data, page = [], 1
    while True:
        resp = requests.get(
            base + "/files",
            headers=_headers(),
            params={"per_page": 100, "page": page},
            timeout=30,
        )
        resp.raise_for_status()
        batch = resp.json()
        files_data.extend(batch)
        if len(batch) < 100:        # 最后一页
            break
        page += 1
        if page > 30:               # 安全上限，避免极端大 PR 无限翻页
            break
    return files_data


def fetch_pr(url: str):
    """拉取 PR 基本信息和所有改动文件的 diff。
    返回 dict：{title, description, files:[{filename,status,additions,deletions,patch}]}
    """
    owner, repo, pr_number = parse_pr_url(url)
    base = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}"

    pr_resp = requests.get(base, headers=_headers(), timeout=30)
    pr_resp.raise_for_status()
    pr_data = pr_resp.json()

    files_data = _fetch_all_files(base)

    files = [{
        "filename": f.get("filename"),
        "status": f.get("status"),
        "additions": f.get("additions", 0),
        "deletions": f.get("deletions", 0),
        "patch": f.get("patch", ""),
    } for f in files_data]

    return {
        "title": pr_data.get("title", ""),
        # 防御性处理：body 字段可能为 None（PR 无描述时 GitHub API 返回 null）
        # 用 (... or "") 避免 None，再 .strip() 去除首尾空白，防止 NoneType 崩溃
        "description": (pr_data.get("body") or "").strip(),
        "files": files,
    }


if __name__ == "__main__":
    data = fetch_pr(input("输入 GitHub PR 链接来测试：").strip())
    print(f"\n标题：{data['title']}")
    print(f"改动文件数：{len(data['files'])}\n")
    for f in data["files"]:
        print(f"  - {f['filename']} ({f['status']}, +{f['additions']} -{f['deletions']})")
