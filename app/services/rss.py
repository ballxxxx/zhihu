# -*- coding: utf-8 -*-
"""外媒 RSS 直连:只取标题+链接跳转原文(不搬运正文,合规新闻聚合)。

注意:部分外媒源在国内网络不可达(BBC/Guardian/NYT 等会被墙),
本模块对单源失败静默跳过,保证整体可用。
"""
import re
import xml.etree.ElementTree as ET

import httpx

FEEDS = [
    ("NPR", "https://feeds.npr.org/1001/rss.xml"),
    ("NPR Tech", "https://feeds.npr.org/1019/rss.xml"),
    ("NPR Music", "https://feeds.npr.org/1039/rss.xml"),
    ("CGTN", "https://www.cgtn.com/subscribe/rss/section/world.xml"),
    ("ECNS", "http://www.ecns.cn/rss/rss.xml"),
    ("Korea Times", "https://www.koreatimes.co.kr/www/rss/rss.xml"),
    ("France 24", "https://www.france24.com/en/rss"),
    # 以下源国内可能不可达,失败自动跳过
    ("BBC", "https://feeds.bbci.co.uk/news/world/rss.xml"),
    ("The Guardian", "https://www.theguardian.com/international/rss"),
]

MAX_PER_FEED = 6  # 每源采样上限,避免单一源挤占全部候选


def _clean(text: str) -> str:
    text = re.sub(r"<[^>]+>", "", text or "")
    return re.sub(r"\s+", " ", text).strip()


def _match_kw(kw: str, title: str, text: str) -> bool:
    """关键词匹配:纯 ASCII 用词边界(避免 explain 误含 ai),含中文直接子串匹配。"""
    if not kw:
        return True
    if kw.isascii():
        return bool(re.search(rf"\b{re.escape(kw)}\b", title, re.IGNORECASE)) or bool(
            re.search(rf"\b{re.escape(kw)}\b", text, re.IGNORECASE)
        )
    return kw in title or kw in text


def fetch_rss(keyword: str = "", timeout: float = 12.0) -> list[dict]:
    """拉取各源 RSS,返回 [{title,url,text,source}];单源失败静默跳过,每源最多 MAX_PER_FEED 条。"""
    kw = keyword.strip()
    out: list[dict] = []
    seen: set[str] = set()
    for source, url in FEEDS:
        try:
            resp = httpx.get(
                url, timeout=timeout, follow_redirects=True,
                headers={"User-Agent": "Mozilla/5.0 (FinalMate RSS reader)"},
            )
            if resp.status_code != 200:
                continue
            root = ET.fromstring(resp.text)
        except Exception:
            continue
        taken = 0
        for item in root.iter():
            if not item.tag.endswith("item") or taken >= MAX_PER_FEED:
                continue
            fields: dict[str, str] = {}
            for child in item:
                tag = child.tag.split("}")[-1]
                if tag in ("title", "link", "description", "summary", "pubDate"):
                    fields[tag] = _clean(child.text or "")
            title = fields.get("title", "")
            link = fields.get("link", "")
            text = fields.get("description") or fields.get("summary", "")
            if not title or not link:
                continue
            if not _match_kw(kw, title, text):
                continue
            if link in seen:
                continue
            seen.add(link)
            taken += 1
            out.append({"title": title, "url": link, "text": text[:300], "source": source})
    return out
