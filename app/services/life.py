# -*- coding: utf-8 -*-
"""「生活参谋」核心:生活决策问题 → 意图理解 → 知乎经验检索 → 建议清单。

与期末搭子的区别:场景从"备考"换成"生活决策"(美食/出行/购物/游玩),
检索目标从"复习经验"换成"真实消费经验与避坑",引擎完全复用。

输出结构:advice(建议)+ trip(行程)+ transport(交通)+ traps(避坑)。
"""
import json
import re

from app.services import zhihu
from app.services.experience import _parse_search
from app.services.llm import DeepSeekChannel, LLMError

GLOBAL_QUERY_TPL = "{kw} 人均 评分 营业时间"

INTENT_PROMPT = """分析用户的需求,按 JSON 输出,只输出 JSON:

{{"类别": "美食/出行/购物/游玩/考试学习/记事/记忆查询/对比选择/生活费/避坑清单/其他", "考试科目": "若类别为考试学习,写出科目名(如:大学英语四级、高等数学),否则空字符串", "地点": "用户想了解/要去的**目标地点**(城市/区/商圈/景点/学校名,如:深圳湾、北京、五邑大学)。**重要:用户说'我在A,想了解B/去B'时,地点=B(目标地点),绝不能填当前位置A**。必须从原文提取,没有提到目标地点才留空", "关键词": "2-4个搜索关键词,空格分隔,必须包含核心需求词(如:海鲜、火锅、民宿、健身)", "补充": "人数/预算/时间等约束,没有则空", "追问": "若需求是求推荐/求建议类但关键信息不足(没说预算/人数/时间/地点),写一句自然的追问(如:预算大概多少?几个人?);信息足够则输出空字符串"}}

按以下优先级判断类别:
1. 用户提到考试、复习、备考、课程、成绩等 → "考试学习";
2. 用户让记住某件事/设置提醒/记待办(如"帮我记一下""提醒我""记个待办")→ "记事";
3. 用户问自己之前说过/问过/聊过什么(如"我之前说过""我上次问的""还记得吗")→ "记忆查询";
4. 用户拿两个选项对比选择(如"A还是B""两家店哪个好""二选一")→ "对比选择";
5. 用户问生活费怎么花/预算分配(如"生活费""每月花销""省钱")→ "生活费";
6. 用户要某个场景的避坑清单/指南/要注意什么/有哪些坑(如"考研择校避坑""租房要注意什么""第一次买XX有什么坑")→ "避坑清单";
7. 其余按内容判断。

用户当前位置(浏览器定位):{location}

追问补充规则:
- 位置已知且用户说"附近/周边/这附近/这里"等时,地点视为已知(即当前位置),即使没提预算/人数也**不要追问**,直接给推荐(按人均50-100元的通用预算);
- 位置未知(显示"未知")且用户说"附近/周边/这附近"时,**必须追问位置**(问"你在哪个城市?");
- 其余情况仅当预算/人数/时间等关键信息不足时才追问。
用户输入:「{text}」"""

MEMORY_QA_PROMPT = """以下是用户在本产品中留下的历史记录(按时间倒序):

{history}

用户现在问:{text}

请基于历史记录回答用户的问题(如"你之前说过想吃XX"),按 JSON 输出,只输出 JSON:
{{"回答": "直接回答用户的问题,引用历史记录中的具体内容;若历史记录中没有相关信息,明确说'你还没跟我提过这个'"}}
要求:只依据历史记录回答,不得编造;回答 1-3 句话,口语化。"""

COMPARE_PROMPT = """用户正在两个选项之间纠结,以下是检索到的相关信息:

【选项相关经验】
{results}

【用户近期动向】
{memory}

用户需求:{text}

请帮用户做结构化对比,按 JSON 输出,只输出 JSON:
{{"要素": [{{"要素名": "对比维度(如:人均、口味、环境、排队、交通)", "A情况": "选项A在该维度的情况(来自给定内容,未知则'信息不足')", "B情况": "选项B在该维度的情况"}}],
 "结论": "一句话结论(倾向哪个,为什么,基于给定内容)",
 "最坏结果": "如果选错了,最坏的结果是什么(帮用户做心理兜底)"}}
要求:
- 要素最多 5 个,每个都必须来自给定内容或明确标注"信息不足",不得编造;
- 结论必须有依据(引用正反两方的观点);
- 结合用户近期动向(如用户近期健身,口味维度可提清淡)。"""

AVOID_PROMPT = """用户想要某个场景的避坑清单,以下是检索到的真实经验:

【知乎真人经验】
{results}

用户需求:{text}

请把经验整理成**可执行的结构化避坑清单**,按 JSON 输出,只输出 JSON:
{{"清单": [{{"坑": "一句话坑名(如:推免占比过高,统考名额是个位数)", "检测": "怎么自查/怎么避开(1-2句话,必须是给定内容里的方法,如:查近3年拟录取名单数推免人数)", "来源标题": "标题", "来源链接": "url"}}],
 "总结": "一句话总结:最该先查的3件事(不超过60字)"}}
要求:
- 每条坑都必须来自给定内容,检测方法也来自给定内容,不得编造;
- 清单最多 8 条,按踩坑人数/后果严重程度排序;
- 链接必须原样使用给定内容中的 url。"""

RULE_PROMPT = """以下是一份校园规则/制度文件的原文:

{text}

请帮学生解读这份文件,按 JSON 输出,只输出 JSON:
{{"要点": [{{"条款": "条款名", "人话": "用大白话解释这条是什么意思、对学生意味着什么"}}],
 "陷阱": [{{"坑": "容易被忽略/容易踩坑的条款", "说明": "为什么坑+怎么避免"}}],
 "总结": "一句话总结:这份文件对你最重要的是什么(不超过60字)"}}
要求:
- 基于原文,不得编造;要点最多 8 条,陷阱最多 4 条;
- 重点突出与学生利益相关的部分:评优/保研/奖学金/毕业要求/加分项/截止时间/隐藏条件。"""

ALLOWANCE_PROMPT = """用户想规划生活费,以下是检索到的真实经验:

【知乎经验】
{results}

用户需求:{text}

请为用户生成一份生活费分配方案,按 JSON 输出,只输出 JSON:
{{"方案": [{{"项目": "支出类别(如:吃饭、日用、社交、储蓄)", "金额": "建议金额(元/月)", "占比": "百分比", "说明": "一句话说明"}}],
 "tips": ["2-3条实用建议,来自给定内容"],
 "traps": [{{"坑": "一句话避坑(如:别碰网贷/奶茶凑单是隐形消费)", "来源标题": "标题", "来源链接": "url"}}]}}
要求:全部来自给定内容,不得编造;方案最多 6 项;金额要与用户给的生活费总额匹配。"""

NOTE_PROMPT = """用户想让 AI 记下一件事。请提炼为一条简洁的待办事项,并按"重要程度 × 紧急程度"判断象限,按 JSON 输出,只输出 JSON:

{{"事项": "一句话待办(保留时间、地点等关键信息,如:周六上午9点体检)", "象限": 1|2|3|4, "说明": "一句话理由"}}

象限定义:
1 = 重要且紧急(立即做)
2 = 重要不紧急(计划做,别拖成紧急)
3 = 紧急不重要(快速处理或委托)
4 = 不重要不紧急(暂缓或放弃)

用户输入:「{text}」"""

# 检索词模板:{kw} 为关键词,{place} 为用户提到的地点
SEARCH_TEMPLATES = [
    "{kw} 推荐 哪里好",
    "{kw} 避坑 踩雷 经验",
    "{kw} 本地人 推荐",
]
PLACE_TEMPLATES = [
    "{place} {kw} 推荐",
    "{place} 必吃 攻略 避坑",
]

# 意图分析失败/关键词为空时,从原句兜底提取
_STOPWORDS = {
    "周末", "周中", "今天", "明天", "后天", "这周", "下周", "去", "吃", "玩", "逛",
    "求推荐", "推荐", "帮我", "给我", "一下", "请问", "哪里", "怎么", "什么",
    "个人", "人", "人均", "预算", "多少钱", "想", "要", "个", "的", "了", "吗", "呢", "呀", "吧",
}
_PLACE_SUFFIX = ("湾", "区", "市", "街", "路", "广场", "城", "公园", "商圈", "景区", "大学", "学校")


def _fallback_keywords(text: str) -> str:
    """意图分析为空时,从原句提取关键词:去停用词/数字/标点,取前4个词。"""
    cleaned = re.sub(r"[\d,\.]+", " ", text)
    words = [
        w for w in re.split(r"[，。！？、\s,]", cleaned)
        if w and w not in _STOPWORDS
    ]
    return " ".join(words[:4])


def _extract_place(text: str) -> str:
    """从原句兜底提取地点:找以地名后缀结尾的词。"""
    for w in re.split(r"[，。！？、\s,]", text):
        if len(w) >= 2 and w.endswith(_PLACE_SUFFIX):
            return w
    return ""


def _build_queries(keywords: str, place: str) -> list[str]:
    """按关键词×模板生成查询;有地点时加地点模板并前置地点模板。"""
    queries: list[str] = []
    kws = str(keywords).split()[:3] or ["推荐"]
    if place:
        for kw in kws:
            queries.extend(tpl.format(place=place, kw=kw) for tpl in PLACE_TEMPLATES)
    for kw in kws:
        queries.extend(tpl.format(kw=kw) for tpl in SEARCH_TEMPLATES)
    return queries


ADVICE_PROMPT = """以下是为用户需求检索到的两层信息:

【知乎真人经验】
{results}

【全网公开信息(美团/点评公开页、官网、媒体等)】
{web_info}

【用户近期动向(记忆)】
{memory}

【用户记事本待办】
{notes}

用户需求:{text}
用户提到的地点:{place}
用户当前位置(浏览器定位):{location}

请整合两层信息给出实用建议,按 JSON 输出,只输出 JSON:
{{"advice": [{{"建议": "一句话具体建议", "理由": "为什么(引用帖子或网页里的事实,尽量包含正反两个视角:推荐方怎么说、踩坑方怎么说;如有双源印证请写明,如:知乎3篇帖子推荐+全网评分4.5)", "来源标题": "标题", "来源链接": "url", "来源类型": "zhihu或web(该条主要依据来自知乎还是全网)", "来源作者": "作者名(没有则空)", "来源赞数": 数字(知乎赞数,没有则0)}}],
 "trip": "行程建议:结合用户的时间/人数/预算,给到达时间与错峰建议(1-3句话)",
 "transport": "怎么去建议:基于搜索结果中的位置与交通信息给出(1-3句话),搜索结果没有交通信息时,给通用提示(如'打开地图搜店名即可导航,海鲜市场周边停车紧张建议地铁出行'这类,不得编造具体地铁线路/停车场)",
 "traps": [{{"坑": "一句话避坑提示(被多人踩过的坑/差评集中点/常见骗局)", "来源标题": "标题", "来源链接": "url", "来源作者": "作者名(没有则空)", "来源赞数": 数字(知乎赞数,没有则0)}}],
 "总结": "一句话总结(给赶时间的用户,不超过60字):直接说去哪/选哪个+什么时间去+预算注意+怎么去"}}

要求:
- **用户给出了具体地点时(地点不为空),advice 必须优先给出该地点的具体店铺/方案:店名、位置、人均、营业时间等,全部来自给定内容原文,每条带来源链接;搜索结果确实没有该地点店铺时,才明确告知"没搜到该地点的具体店铺信息"并给选店通用原则**;
- 每条建议/坑必须来自给定内容,不得编造;建议最多 6 条,坑最多 4 条;
- 知乎经验优先(它代表真人踩坑结论),全网信息用于补充人均/评分/位置等客观数据;
- **在理由中做双源印证**:推荐具体店/方案时,如知乎和全网信息都有涉及,写明两边的信息(如"知乎N篇帖子推荐,全网显示人均XX元");
- **结合用户当前位置**:用户提问未提地点但当前位置已知时,以当前位置为默认地点给建议;transport 中说明从用户当前位置出发的交通思路(公共交通/自驾/停车),搜索结果没有该地点的交通信息时给通用提示,不得编造具体线路;
- 结合用户近期动向做个性化(如用户近期吃清淡,可提示考虑口味偏好的店);
- **记事本待办仅在与本次建议有直接关联时提及(如时间冲突),不要让待办喧宾夺主,不得把待办写成建议第一条**;
- 链接必须原样使用给定内容中的 url。"""


def search_web_info(keywords: str, count: int = 5, place: str = "") -> list[dict]:
    """全网搜索公开信息(商家页/评分/人均),返回截断条目。"""
    entries: list[dict] = []
    seen: set[str] = set()
    queries = [GLOBAL_QUERY_TPL.format(kw=kw) for kw in str(keywords).split()[:2]]
    if place:
        queries.insert(0, f"{place} 人气 评分")
    for query in queries:
        try:
            raw = zhihu.search_global(query, count=count)
            for e in _parse_search(raw):
                if e["url"] and e["url"] not in seen:
                    seen.add(e["url"])
                    e["source"] = "web"
                    entries.append(e)
        except Exception:
            continue
    return entries[:8]


def analyze_intent(text: str, location: str = "") -> dict:
    data = DeepSeekChannel().chat_json(
        INTENT_PROMPT.format(text=text, location=str(location or "未知"))
    )
    return data


def search_experiences(keywords: str, count: int = 5, place: str = "") -> list[dict]:
    """按关键词组合搜索知乎,合并去重;有地点时优先地点查询。"""
    seen: set[str] = set()
    entries: list[dict] = []
    for query in _build_queries(keywords, place):
        try:
            raw = zhihu.search_zhihu(query, count=count)
            for e in _parse_search(raw):
                if e["url"] and e["url"] not in seen:
                    seen.add(e["url"])
                    e["source"] = "zhihu"
                    entries.append(e)
        except Exception:
            continue
    return entries[:15]


def build_advice(text: str, session_id: str | None = None, location: str | None = None) -> dict:
    """一次完整调用:意图 → 知乎经验 + 全网信息 + 用户记忆 → 整合建议清单。

    类别为"考试学习"时走轻量分支:不检索生活信息,直接引导复习功能。
    location 为浏览器定位/手动设置的位置:用户没提地点时作为默认地点。
    """
    from app import models

    # 位置查询:直接回答,不走 LLM 检索(用户问"我在哪/我的位置")
    if any(p in text for p in ("我在哪", "我在哪里", "我的位置", "我定位", "定位到哪", "我在什么位置")):
        loc = str(location or "").strip()
        if loc:
            answer = f"你设置的位置是:{loc}。问'附近有什么好吃的'之类的需求,我都会按这个位置给你找。"
        else:
            answer = "你还没有设置位置。点击参谋页顶部的定位条,允许定位或手动输入你的城市(如:江门市),设置一次后我会一直记得。"
        return {
            "intent": {"类别": "位置查询", "地点": loc or "", "关键词": "", "补充": ""},
            "advice": [],
            "searched": 0,
            "web_searched": 0,
            "is_study": False,
            "is_position": True,
            "position_answer": answer,
        }

    intent = analyze_intent(text, location)
    if intent.get("类别") == "考试学习":
        return {
            "intent": intent,
            "advice": [],
            "searched": 0,
            "web_searched": 0,
            "is_study": True,
        }
    # 求推荐/建议类信息不足时先追问,不硬生成(灵感:蚂蚁阿福主动追问)
    followup = str(intent.get("追问") or "").strip()
    if followup and intent.get("类别") in ("美食", "出行", "购物", "游玩", "其他"):
        return {
            "intent": intent,
            "advice": [],
            "searched": 0,
            "web_searched": 0,
            "is_study": False,
            "is_followup": True,
            "followup_question": followup,
        }
    if intent.get("类别") == "记事":
        # 记事意图:提炼事项 + 建议象限 → 直接写入四象限记事本
        note_data = DeepSeekChannel().chat_json(NOTE_PROMPT.format(text=text))
        content = str(note_data.get("事项") or "").strip() or text.strip()
        quadrant = note_data.get("象限") if note_data.get("象限") in (1, 2, 3, 4) else 2
        note_id = models.insert_note(content, quadrant)
        return {
            "intent": intent,
            "advice": [],
            "searched": 0,
            "web_searched": 0,
            "is_study": False,
            "is_note": True,
            "note": {
                "id": note_id,
                "content": content,
                "quadrant": quadrant,
                "说明": str(note_data.get("说明") or ""),
            },
        }
    if intent.get("类别") == "记忆查询":
        # 记忆查询:从会话历史回答"我之前说过XX来着"
        history_text = "(无历史记录)"
        if session_id:
            recent = models.get_recent_conversations(session_id, limit=30)
            if recent:
                history_text = "\n".join(
                    f"- [{r['category'] or '?'}] {r['message'][:80]}" for r in reversed(recent)
                )
        data = DeepSeekChannel().chat_json(
            MEMORY_QA_PROMPT.format(history=history_text, text=text)
        )
        return {
            "intent": intent,
            "advice": [],
            "searched": 0,
            "web_searched": 0,
            "is_study": False,
            "is_memory": True,
            "memory_answer": str(data.get("回答") or "你还没跟我提过这个"),
        }
    if intent.get("类别") == "对比选择":
        # 对比选择:A 还是 B → 检索两个选项的经验 → 结构化对比表
        keywords = str(intent.get("关键词") or "").strip() or _fallback_keywords(text)
        entries = search_experiences(keywords, place=intent.get("地点") or "")
        results_text = "\n".join(
            f"- {e['title']} | {e['url']}\n  {e['text'][:200]}" for e in entries[:10]
        ) or "(无)"
        memory_text = "(无历史)"
        if session_id:
            recent = models.get_recent_conversations(session_id, limit=6)
            if recent:
                memory_text = "\n".join(
                    f"- [{r['category'] or '?'}] {r['message'][:60]}" for r in reversed(recent)
                )
        data = DeepSeekChannel().chat_json(
            COMPARE_PROMPT.format(results=results_text, memory=memory_text, text=text)
        )
        return {
            "intent": intent,
            "advice": [],
            "searched": len(entries),
            "web_searched": 0,
            "is_study": False,
            "is_compare": True,
            "compare": data,
        }
    if intent.get("类别") == "避坑清单":
        # 避坑清单:检索相关经验 → 结构化"坑+检测方法"清单
        keywords = str(intent.get("关键词") or "").strip() or _fallback_keywords(text)
        entries = search_experiences(f"{keywords} 避坑 踩雷", place=intent.get("地点") or "")
        if not entries:
            entries = search_experiences(_fallback_keywords(text) or "避坑 指南")
        results_text = "\n".join(
            f"- {e['title']} | {e['url']}\n  {e['text'][:250]}" for e in entries[:12]
        ) or "(无)"
        data = DeepSeekChannel().chat_json(
            AVOID_PROMPT.format(results=results_text, text=text)
        )
        items = data.get("清单")
        if not isinstance(items, list):
            items = []
        return {
            "intent": intent,
            "advice": [],
            "searched": len(entries),
            "web_searched": 0,
            "is_study": False,
            "is_avoid": True,
            "avoid": {
                "清单": [x for x in items if isinstance(x, dict) and x.get("坑")],
                "总结": str(data.get("总结") or ""),
            },
        }
    if intent.get("类别") == "生活费":
        # 生活费规划:检索大学生生活费经验 → 生成分配方案
        entries = search_experiences("大学生 生活费 分配 省钱 记账")
        results_text = "\n".join(
            f"- {e['title']} | {e['url']}\n  {e['text'][:200]}" for e in entries[:10]
        ) or "(无)"
        data = DeepSeekChannel().chat_json(
            ALLOWANCE_PROMPT.format(results=results_text, text=text)
        )
        return {
            "intent": intent,
            "advice": [],
            "searched": len(entries),
            "web_searched": 0,
            "is_study": False,
            "is_allowance": True,
            "allowance": data,
        }
    # 意图为空/地点缺失时兜底提取,保证搜索质量
    place = str(intent.get("地点") or "").strip()
    # 原文明确提到的目标地点优先(如"我在江门想了解深圳湾附近的美食" → 深圳湾)
    explicit = _extract_place(text)
    if explicit and explicit not in place:
        place = explicit
    loc_text = str(location or "").strip()
    # 仍无地点且定位是中文地名(非纯坐标)时,用定位作为默认地点
    if not place and loc_text and re.search(r"[一-鿿]", loc_text):
        place = loc_text
    keywords = str(intent.get("关键词") or "").strip() or _fallback_keywords(text)
    intent["地点"] = place
    intent["关键词"] = keywords

    entries = search_experiences(keywords, place=place)
    if not entries:
        # 关键词为空或搜索无结果时,用原句拆词兜底
        entries = search_experiences(
            _fallback_keywords(text) or "生活 推荐", place=place
        )

    web_entries = search_web_info(keywords or _fallback_keywords(text), place=place)

    results_text = "\n".join(
        f"- {e['title']} | 作者:{e['author'] or '?'} | 赞:{e['votes']} | {e['url']}\n  {e['text'][:250]}"
        for e in entries[:12]
    ) or "(无)"
    web_text = "\n".join(
        f"- {e['title']} | {e['url']}\n  {e['text'][:200]}" for e in web_entries
    ) or "(无)"
    # 用户近期动向(轻量记忆)
    memory_text = "(无历史)"
    if session_id:
        recent = models.get_recent_conversations(session_id, limit=6)
        if recent:
            memory_text = "\n".join(
                f"- [{r['category'] or '?'}] {r['message'][:60]}" for r in reversed(recent)
            )
    # 用户记事本待办(未完成的)
    notes_text = "(无待办)"
    pending_notes = [n for n in models.list_notes() if not n["done"]][:8]
    if pending_notes:
        q_names = {1: "重要紧急", 2: "重要不紧急", 3: "紧急不重要", 4: "不重要不紧急"}
        notes_text = "\n".join(
            f"- [{q_names.get(n['quadrant'], '?')}] {n['content'][:60]}" for n in pending_notes
        )

    data = DeepSeekChannel().chat_json(
        ADVICE_PROMPT.format(
            results=results_text, web_info=web_text, memory=memory_text,
            notes=notes_text, text=text, place=place or "(用户未提及)",
            location=loc_text or "(未知)",
        )
    )
    advice = data.get("advice")
    if not isinstance(advice, list):
        raise LLMError(f"建议格式错误: {str(data)[:200]}")
    traps = data.get("traps")
    if not isinstance(traps, list):
        traps = []
    trip = data.get("trip") if isinstance(data.get("trip"), str) else ""
    transport = data.get("transport") if isinstance(data.get("transport"), str) else ""
    summary = data.get("总结") if isinstance(data.get("总结"), str) else ""
    return {
        "intent": intent,
        "advice": [a for a in advice if isinstance(a, dict) and a.get("建议")],
        "traps": [t for t in traps if isinstance(t, dict) and t.get("坑")],
        "trip": trip,
        "transport": transport,
        "summary": summary,
        "searched": len(entries),
        "web_searched": len(web_entries),
        "is_study": False,
        "memory_count": 0 if memory_text == "(无历史)" else len(recent),
    }
