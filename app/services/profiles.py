# -*- coding: utf-8 -*-
"""科目族配置:数学族 / 英语族。

族决定:划重点提示词、题型风格、复习计划模板、经验检索词。
加新科目 = 在对应族列表里加一行,不改管线。
"""

FAMILY_MATH = "math"
FAMILY_ENGLISH = "english"

PROFILES: dict[str, dict] = {
    FAMILY_MATH: {
        "name": "数学族",
        "subjects": ["高中数学", "高等数学", "高数", "线性代数", "概率论"],
        "highlight_prompt": (
            "你是资深的大学/高中数学老师,正在为《{course}》做期末复习重点梳理。\n"
            "以下是课件的一部分内容:\n\n{chunk}\n\n"
            "请找出其中值得复习的知识点,按 JSON 格式输出,格式如下:\n"
            '{{"points": [{{"知识点": "概念或方法名称", "考点等级": "高频/中频/低频", '
            '"出题方向": "会怎么考,如计算题/证明题/选择题", "依据": "原文关键句(必须引用原文)"}}]}}\n'
            "要求:最多 5 个点;只覆盖文中真实出现的内容,不得编造;考点等级要有区分度。"
        ),
        "exam_prompt": (
            "你是《{course}》的出题老师。根据以下高频考点出一套模拟题:\n\n{points}\n\n"
            "按 JSON 输出:{{\"questions\": [{{\"题干\": \"...\", \"参考答案\": \"...\", \"考点\": \"...\"}}]}}\n"
            "题型要求:计算题为主,适当搭配概念辨析选择题;难度贴合期末考;共 5 题。\n"
            "数学公式必须用 \\(...\\) 行内包裹并写规范 LaTeX:幂次用花括号 x^{{2}}、"
            "积分 \\int_{{a}}^{{b}}、分数 \\frac{{}}{{}};禁止 Unicode 数学符号(∫、²、α、→ 等);"
            "不要使用 \\[...\\] 多行公式,长推导分写成多个 \\(...\\) 短式。"
        ),
        "search_queries": [
            "{course} 期末复习 重点",
            "{course} 期末 必考 考点",
            "{course} 挂科 经验 难点",
        ],
        # 无文件模式下的在线资料检索词
        "material_queries": [
            "{course} 知识点总结 重点归纳",
            "{course} 重点公式 定理 汇总",
            "{course} 必考知识点 大纲",
        ],
        # 大纲 JSON 提示词(无文件模式:一步产出重点清单)
        "outline_json_prompt": (
            "你是考试辅导专家。请输出《{course}》的知识点大纲,严格按以下 JSON 格式输出,只输出 JSON,不要任何其他文字:\n"
            '{{"points": [{{"知识点": "具体考点名称(如:两个重要极限)", "考点等级": "高频/中频/低频", '
            '"出题方向": "常见题型(如:计算题/选择题)", "依据": "所属章节或模块名"}}]}}\n'
            "考试范围:{chapters}。"
            "要求:按教材章节组织,覆盖指定范围,共 {points_target} 个点,等级要有区分度(高频不超过一半)。"
        ),
        # 搜索条目标题相关性过滤关键词
        "title_keywords": ["数学", "高数", "微积分", "函数", "极限", "导数", "积分", "几何", "代数"],
    },
    FAMILY_ENGLISH: {
        "name": "英语族",
        "subjects": ["高中英语", "大学英语", "四级", "六级", "四六级", "雅思", "托福", "考研英语"],
        "highlight_prompt": (
            "你是资深英语考试辅导老师,正在为《{course}》做备考重点梳理。\n"
            "以下是学习资料的一部分内容:\n\n{chunk}\n\n"
            "请找出其中的备考重点,按 JSON 格式输出:\n"
            '{{"points": [{{"知识点": "词汇/语法/题型/技巧名称", "考点等级": "高频/中频/低频", '
            '"出题方向": "会在什么题型中考查(听力/阅读/写作/翻译/口语)", "依据": "原文关键句(必须引用原文)"}}]}}\n'
            "要求:最多 5 个点;只覆盖文中真实出现的内容,不得编造。"
        ),
        "exam_prompt": (
            "你是《{course}》的出题老师。根据以下高频考点出一套模拟题:\n\n{points}\n\n"
            "按 JSON 输出:{{\"questions\": [{{\"题干\": \"...\", \"参考答案\": \"...\", \"考点\": \"...\"}}]}}\n"
            "题型要求:词汇/语法选择题为主,搭配 1 道写作题;难度贴合目标考试;共 5 题。\n"
            "题目中的英文短语、例句等保持原样;涉及数学或音标等特殊符号时用规范 LaTeX 并包裹,禁止 Unicode 特殊符号。"
        ),
        "search_queries": [
            "{course} 备考 经验 技巧",
            "{course} 高频词汇 重点",
            "{course} 备考 避坑 误区",
        ],
        # 无文件模式下的在线资料检索词(英语族按技能模块)
        "material_queries": [
            "{course} 考试题型 分值 结构",
            "{course} 高频词汇 语法 归纳",
            "{course} 备考 方法 攻略",
        ],
        # 大纲 JSON 提示词(无文件模式:一步产出重点清单,英语族按技能模块)
        "outline_json_prompt": (
            "你是英语考试辅导专家。请输出《{course}》的备考知识点大纲,严格按以下 JSON 格式输出,只输出 JSON,不要任何其他文字:\n"
            '{{"points": [{{"知识点": "具体考点名称(如:听力篇章主旨题)", "考点等级": "高频/中频/低频", '
            '"出题方向": "所属题型(听力/阅读/写作/翻译/词汇/语法)", "依据": "所属技能模块名"}}]}}\n'
            "考试范围:{chapters}。"
            "要求:覆盖指定范围内的各模块,共 {points_target} 个点,等级要有区分度(高频不超过一半)。"
        ),
        # 搜索条目标题相关性过滤关键词
        "title_keywords": ["英语", "四级", "六级", "雅思", "托福", "词汇", "语法", "听力", "阅读", "写作", "翻译", "CET"],
    },
}


# E2 章节模板:常见教材/考试的章节树,供用户勾选考试范围
SYLLABUS_TEMPLATES: list[dict] = [
    {
        "family": FAMILY_MATH,
        "course": "高等数学",
        "aliases": ["高数", "微积分"],
        "chapters": [
            "函数与极限", "导数与微分", "微分中值定理与导数应用", "不定积分",
            "定积分", "定积分应用", "微分方程", "多元函数微分学", "重积分", "无穷级数",
        ],
    },
    {
        "family": FAMILY_MATH,
        "course": "高中数学",
        "aliases": ["高考数学"],
        "chapters": [
            "集合与逻辑", "函数与导数", "三角函数", "数列", "不等式",
            "立体几何", "解析几何", "平面向量", "概率与统计", "复数",
        ],
    },
    {
        "family": FAMILY_ENGLISH,
        "course": "大学英语四级",
        "aliases": ["四级", "CET4", "CET-4"],
        "chapters": ["词汇", "语法", "听力", "阅读", "写作", "翻译"],
    },
    {
        "family": FAMILY_ENGLISH,
        "course": "大学英语六级",
        "aliases": ["六级", "CET6", "CET-6"],
        "chapters": ["词汇", "语法", "听力", "阅读", "写作", "翻译"],
    },
    {
        "family": FAMILY_ENGLISH,
        "course": "雅思",
        "aliases": ["IELTS", "ielts"],
        "chapters": ["听力", "口语", "阅读", "写作"],
    },
    {
        "family": FAMILY_ENGLISH,
        "course": "托福",
        "aliases": ["TOEFL", "toefl"],
        "chapters": ["阅读", "听力", "口语", "写作"],
    },
]


# E5 风格库:模拟卷风格(按族)。style_guide 为出卷细节描述,用于生成时拼入提示词。
EXAM_STYLES: dict[str, dict[str, str]] = {
    FAMILY_MATH: {
        "标准期末卷": "题量适中(约20题):选择题40%、填空20%、解答40%;难度分布 基础60%/中等30%/拔高10%,覆盖全部勾选章节,贴近常规期末考",
        "全国卷风格": "全国卷模式:12选择+4填空+6解答;难度 基础50%/中等35%/压轴15%;压轴题放导数与数列综合;解答题设3小问层层递进",
        "新高考Ⅰ卷风格": "新高考模式:8单选+4多选+4填空+6解答;多选题选对部分给分;第1-2道解答题为基础送分题;压轴题为圆锥曲线与导数",
        "北京卷风格": "北京卷模式:选择+填空+6道解答;出题重视概念理解与过程书写,压轴题偏创新探究(新定义类),难度坡度缓但最后一问难",
    },
    FAMILY_ENGLISH: {
        "标准模拟卷": "常规模拟卷:听力+阅读+完形+写作;难度适中,词汇量控制在目标考试大纲内",
        "四级真题风格": "四级模式:短篇新闻听力+长对话+篇章听力;仔细阅读2篇+选词填空+段落匹配;翻译为汉译英段落(中国话题);写作150-200词",
        "六级真题风格": "六级模式:听力语速加快、题材偏学术讲座;阅读长难句密度高;翻译段落更长更抽象;写作180-220词",
        "雅思真题风格": "雅思模式:听力4部分(填空+选择+地图);阅读3篇学术文章40题;小作文图表+大作文250词议论文",
        "托福真题风格": "托福模式:听力为学术讲座+对话;阅读每篇10题;综合写作+独立写作;学术词汇要求高",
    },
}


def get_styles(course: str) -> list[str]:
    return list(EXAM_STYLES.get(detect_family(course), EXAM_STYLES[FAMILY_MATH]).keys())


def get_style_guide(style: str) -> str:
    """按风格名取细节描述;未知风格返回空(不影响生成)。"""
    for styles in EXAM_STYLES.values():
        if style in styles:
            return styles[style]
    return ""


def match_syllabus(course: str) -> dict | None:
    """按课程名匹配章节模板,匹配不到返回 None(前端走自动模式)。"""
    c = course.lower()
    for t in SYLLABUS_TEMPLATES:
        if t["course"].lower() in c or c in t["course"].lower():
            return t
        for alias in t["aliases"]:
            if alias.lower() in c:
                return t
    return None


def detect_family(course: str) -> str:
    """按课程名关键词判断所属科目族。"""
    for family, profile in PROFILES.items():
        for subject in profile["subjects"]:
            if subject.lower() in course.lower():
                return family
    # 默认按数学族(章节驱动)处理
    return FAMILY_MATH


def get_profile(course: str) -> dict:
    return PROFILES[detect_family(course)]
