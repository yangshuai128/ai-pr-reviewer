import argparse
from src.pipeline import run_review
from src.reporter import format_report, build_markdown_comment
from src.github_client import parse_pr_url, post_pr_comment


def review(pr_url, post_comment=False):
    print("正在拉取并分析 PR...")
    result = run_review(pr_url)
    if result["analysis"] is None:
        print("没有可分析的代码改动")
        return
    print(format_report(result["analysis"], result["pr_title"]))

    if post_comment:
        owner, repo, pr_number = parse_pr_url(pr_url)
        body = build_markdown_comment(result)
        print("\n正在发布评论到 GitHub PR...")
        html_url = post_pr_comment(owner, repo, pr_number, body)
        print(f"✅ 评论已发布：{html_url}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AI PR Review 命令行工具")
    parser.add_argument("url", nargs="?", help="GitHub PR 链接（不传则交互式输入）")
    parser.add_argument(
        "--post-comment",
        action="store_true",
        help="分析完成后自动将评审结果发布为 GitHub PR 评论",
    )
    args = parser.parse_args()

    url = args.url or input("请输入 GitHub PR 链接: ").strip()
    review(url, post_comment=args.post_comment)
