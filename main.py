from src.pipeline import run_review
from src.reporter import format_report

def review(pr_url):
    print("正在拉取并分析 PR...")
    result = run_review(pr_url)
    if result["analysis"] is None:
        print("没有可分析的代码改动")
        return
    print(format_report(result["analysis"], result["pr_title"]))

if __name__ == "__main__":
    url = input("请输入 GitHub PR 链接: ").strip()
    review(url)
