# -*- coding: utf-8 -*-
"""今日外刊(P2):全网搜索拉公开英文新闻 + AI 中文导读(注明来源,不搬运付费内容)。"""
from app.services import zhihu
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

NEWS_PROMPT = """以下是全网搜索到的新闻条目(标题+摘要+url):

{items}

请筛选出 5 条最适合大学生做英语阅读的新闻,**同一媒体最多 1 条,尽量覆盖不同媒体**,按 JSON 输出,只输出 JSON:
{{"新闻": [{{"标题": "原标题(保留原文语言)", "导读": "一句话中文导读(30字内,帮助理解)", "来源": "媒体名(从 url 域名判断,如 BBC/NYT/CNN/卫报/NPR,写英文简称即可)", "链接": "url", "分类": "科技/国际/财经/文化/体育 等"}}]}}

要求:
- 链接必须原样使用给定条目中的 url,不得编造;
- 导读口语化,不评价立场;
- 只输出 JSON。"""


def fetch_news(keyword: str = "") -> dict:
    """聚合权威源定向检索 + 全网自由检索,交给 DeepSeek 筛选+生成导读。

    keyword 为用户兴趣关键词(如 AI/篮球/音乐),为空时输出综合新闻。
    """
    kw = keyword.strip()[:30]
    seen: set[str] = set()
    entries: list[dict] = []

    def add(raw: str) -> None:
        for e in _parse_search(raw):
            if e["url"] and e["url"] not in seen:
                seen.add(e["url"])
                entries.append(e)

    # 1) 权威外刊源定向(host 过滤);有关键词时按兴趣检索
    source_queries = [f"{kw} news", f"{kw} report"] if kw else ["news", "world news"]
    for _name, host in SOURCES:
        for q in source_queries:
            try:
                add(zhihu.search_global(q, count=5, filter_expr=f'host=="{host}"'))
            except Exception:
                continue
    # 2) 全网自由检索兜底
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
