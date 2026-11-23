# -*- coding: utf-8 -*-
"""今日外刊(P2):外媒 RSS 直连 + 知乎全网搜索兜底 + AI 中文导读(注明来源,不搬运正文)。"""
from app.services import rss, zhihu
from app.services.experience import _parse_search
from app.services.llm import DeepSeekChannel

# 通用查询(全网自由检索)
QUERIES = ["今日国际新闻 英文", "大学生 英语阅读 时事"]

# 权威外刊源定向检索(host 过滤,内容仅链接跳转不搬运)
SOURCES = [
    ("BBC", "www.bbc.com"),
    ("纽约时报 NYT", "www.nytimes.com"),
    ("CNN", "www.cnn.com"),
    ("卫报 The Guardian", "www.theguardian.com"),
    ("NPR", "www.npr.org"),
]

NEWS_PROMPT = """以下是英文新闻条目(标题+摘要+url):

{items}

请筛选出 5 条最适合大学生做英语阅读的新闻,**同一媒体最多 1 条(NPR 与 NPR Tech/NPR Music 视为同一媒体),尽量覆盖不同媒体**,按 JSON 输出,只输出 JSON:
{{"新闻": [{{"标题": "原标题(保留英文原文)", "导读": "一句话中文导读(30字内,帮助理解)", "来源": "媒体名(用条目中括号里的媒体名,如 NPR/CGTN/Global Times/BBC)", "链接": "url", "分类": "科技/国际/财经/文化/体育 等"}}]}}

要求:
- 只保留英文媒体的条目,丢弃中文来源;
- 链接必须原样使用给定条目中的 url,不得编造;
- 导读口语化,不评价立场;
- 只输出 JSON。"""


def fetch_news(keyword: str = "") -> dict:
    """外媒 RSS 直连为主,知乎全网搜索兜底,交给 DeepSeek 筛选+生成导读。

    keyword 为用户兴趣关键词(如 AI/篮球/音乐),为空时输出综合新闻。
    """
    kw = keyword.strip()[:30]
    items_text: str

    # 1) 外媒 RSS 直连(标题+链接,不搬运正文)
    rss_entries = rss.fetch_rss(kw)
    if rss_entries:
        items_text = "\n".join(
            f"- [{e['source']}] {e['title']} | {e['url']}\n  {e['text'][:120]}"
            for e in rss_entries[:20]
        )
    else:
        # 2) 兜底:知乎全网搜索(索引无外媒域名,只作最后手段)
        seen: set[str] = set()
        entries: list[dict] = []

        def add(raw: str) -> None:
            for e in _parse_search(raw):
                if e["url"] and e["url"] not in seen:
                    seen.add(e["url"])
                    entries.append(e)

        generic = [f"{kw} 英文新闻", f"{kw} 最新动态"] if kw else list(QUERIES)
        for query in generic:
            try:
                add(zhihu.search_global(query, count=5))
            except Exception:
                continue
        items_text = "\n".join(
            f"- {e['title']} | {e['url']}\n  {e['text'][:120]}" for e in entries[:18]
        ) or "(无)"

    data = DeepSeekChannel().chat_json(NEWS_PROMPT.format(items=items_text))
    news = data.get("新闻") or []
    return {"news": [n for n in news if isinstance(n, dict) and n.get("链接")][:5], "keyword": kw}
