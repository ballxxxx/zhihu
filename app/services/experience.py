# -*- coding: utf-8 -*-
"""D5 经验检索增强:知乎搜索"过来人经验" + 真题获取渠道。

流程:搜索(zhihu-cli)→ LLM 提取经验要点(DeepSeek,带出处)→ 按知识点关键词对齐到重点清单。
"""
import json

from app.services import profiles, zhihu
from app.services.llm import DeepSeekChannel, LLMError

EXTRACT_PROMPT = """以下是知乎上关于《{course}》期末复习/备考的真实讨论(来自知乎搜索,内容已截断):

{results}

请从中提取"过来人经验",按 JSON 格式输出:
{{"experiences": [{{"经验": "一句话经验(如:第3章必考大题/老师喜欢出证明题/XX容易挂)", "相关知识点": "用于匹配章节的关键词,2-4个", "来源标题": "帖子标题", "来源链接": "url"}}]}}
要求:每条必须来自给定内容,不得编造;最多 6 条;优先提取:必考章节、老师出题习惯、易错点、高效复习方法。"""

CHANNEL_PROMPT = """以下是关于《{course}》真题/试卷获取渠道的搜索结果:

{results}

请提取**官方或正规**的真题获取渠道,按 JSON 输出:
{{"channels": [{{"渠道": "名称", "链接": "url", "说明": "该渠道有什么"}}]}}
硬性规则:只保留官网、教育考试院、大学出版社等正规渠道;盗版网站、网盘合集、公众号一律丢弃;没有明确链接的不输出;最多 5 条。"""


def _parse_search(raw: str) -> list[dict]:
    """解析 zhihu-cli search 的 JSON 返回,得到截断后的条目列表。

    保留 author/votes 字段用于前端"可信度标识"(赞数+答主)。
    """
    data = json.loads(raw)
    items = data.get("Data", {}).get("Items") or []
    entries = []
    for it in items:
        text = (it.get("ContentText") or it.get("Summary") or "").strip().replace("\n", " ")
        if not text:
            continue
        entries.append(
            {
                "title": it.get("Title", ""),
                "url": it.get("Url", ""),
                "text": text[:400],
                "author": (it.get("AuthorName") or "").strip() or it.get("AuthorSignature") or "",
                "votes": it.get("VoteUpCount") or 0,
            }
        )
    return entries


def search_experiences(course: str, per_query: int = 5) -> list[dict]:
    """按科目族的检索词模板搜索知乎,合并去重结果。"""
    profile = profiles.get_profile(course)
    seen_urls: set[str] = set()
    entries: list[dict] = []
    for query_tpl in profile["search_queries"]:
        query = query_tpl.format(course=course)
        try:
            entries_raw = _parse_search(zhihu.search_zhihu(query, count=per_query))
        except (zhihu.ZhihuCliError, json.JSONDecodeError):
            continue  # 单个查询失败不阻塞整体
        for e in entries_raw:
            if e["url"] and e["url"] not in seen_urls:
                seen_urls.add(e["url"])
                entries.append(e)
    return entries


def extract_experiences(course: str, entries: list[dict]) -> list[dict]:
    """LLM 从搜索结果中提取经验要点。"""
    if not entries:
        return []
    results_text = "\n".join(f"- {e['title']} | {e['url']}\n  {e['text']}" for e in entries[:15])
    data = DeepSeekChannel().chat_json(EXTRACT_PROMPT.format(course=course, results=results_text))
    exps = data.get("experiences")
    if not isinstance(exps, list):
        raise LLMError(f"经验提取格式错误: {str(data)[:200]}")
    return [e for e in exps if isinstance(e, dict) and e.get("经验")]


def search_channels(course: str) -> list[dict]:
    """搜索并提取真题获取的正规渠道。"""
    query = f"{course} 历年真题 官网 下载"
    try:
        entries = _parse_search(zhihu.search_zhihu(query, count=8))
    except (zhihu.ZhihuCliError, json.JSONDecodeError):
        return []
    if not entries:
        return []
    results_text = "\n".join(f"- {e['title']} | {e['url']}\n  {e['text']}" for e in entries)
    data = DeepSeekChannel().chat_json(CHANNEL_PROMPT.format(course=course, results=results_text))
    channels = data.get("channels")
    if not isinstance(channels, list):
        return []
    return [c for c in channels if isinstance(c, dict) and c.get("渠道")]


def _match_score(keywords: str, point_name: str) -> int:
    """经验的关键词与知识点名的重合度(简单子串匹配)。"""
    score = 0
    for kw in str(keywords).replace(",", " ").replace("、", " ").split():
        if kw and kw in point_name:
            score += 1
    return score


def enrich(course: str, points: list[dict]) -> dict:
    """把经验与真题渠道挂到重点清单上。

    返回 {experiences_matched: [{point_index, experiences[]}], general: [], channels: []}
    """
    entries = search_experiences(course)
    experiences = extract_experiences(course, entries)
    channels = search_channels(course)

    matched: dict[int, list[dict]] = {}
    general: list[dict] = []
    for exp in experiences:
        keywords = str(exp.get("相关知识点", ""))
        best_idx, best_score = -1, 0
        for idx, p in enumerate(points):
            score = _match_score(keywords, str(p.get("知识点", "")))
            if score > best_score:
                best_idx, best_score = idx, score
        if best_score > 0:
            matched.setdefault(best_idx, []).append(exp)
        else:
            general.append(exp)

    return {
        "experiences_matched": matched,
        "general": general,
        "channels": channels,
        "searched": len(entries),
    }
