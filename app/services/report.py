# -*- coding: utf-8 -*-
"""D8 报告渲染:把管线结果渲染成单文件 HTML(可打印、可分享)。"""
import html
from datetime import datetime

from app.services.mathtext import normalize

LEVEL_COLORS = {"高频": "#e5484d", "中频": "#f5a623", "低频": "#8e8e93"}

CSS = """
:root { --primary:#0084ff; --primary-deep:#0060e6; --ink:#1a1a1a; --ink-2:#555; --muted:#8a919f; --line:#e5e8ee; }
* { margin:0; padding:0; box-sizing:border-box; }
body { font-family:'PingFang SC','Microsoft YaHei',sans-serif; background:linear-gradient(160deg,#eef4ff,#f8fafd 40%,#e6f1ff); color:var(--ink); line-height:1.7; }
.wrap { max-width:900px; margin:0 auto; padding:28px 20px 80px; }
header.hero { background:linear-gradient(135deg,#0084ff,#0060e6 70%,#0048b8); color:#fff; border-radius:22px; padding:36px 34px; margin-bottom:26px;
  box-shadow:0 16px 44px rgba(0,96,230,.28); position:relative; overflow:hidden; }
header.hero::after { content:''; position:absolute; width:300px; height:300px; border-radius:50%; background:rgba(255,255,255,.10); top:-130px; right:-70px; }
header.hero h1 { font-size:27px; margin-bottom:12px; position:relative; z-index:1; }
header.hero .meta { font-size:13.5px; opacity:.95; position:relative; z-index:1; }
header.hero .badge { display:inline-block; background:rgba(255,255,255,.18); border:1px solid rgba(255,255,255,.25);
  border-radius:999px; padding:4px 14px; margin:0 8px 6px 0; backdrop-filter:blur(4px); }
section { background:#fff; border-radius:18px; padding:28px; margin-bottom:20px;
  box-shadow:0 2px 10px rgba(30,60,110,.06); transition:box-shadow .2s; }
section:hover { box-shadow:0 8px 26px rgba(30,60,110,.10); }
h2 { font-size:19px; margin-bottom:16px; padding-left:12px; border-left:4px solid var(--primary); }
.point { padding:16px 0; border-bottom:1px dashed var(--line); }
.point:last-child { border-bottom:none; }
.point .name { font-weight:700; font-size:16px; }
.point .lv { display:inline-block; color:#fff; border-radius:999px; font-size:12px; padding:2px 12px; margin-left:8px; vertical-align:2px; box-shadow:0 2px 6px rgba(0,0,0,.15); }
.point .dir, .point .base { color:var(--ink-2); font-size:13px; margin-top:5px; }
.exp { background:#f0f7ff; border-left:4px solid var(--primary); border-radius:10px; padding:11px 15px; margin-top:9px; font-size:13px; }
.exp a { color:var(--primary-deep); text-decoration:none; font-weight:600; }
.exp a:hover { text-decoration:underline; }
.cards { display:grid; grid-template-columns:repeat(auto-fill,minmax(240px,1fr)); gap:14px; }
.card { border:1px solid var(--line); border-radius:14px; padding:18px; cursor:pointer; min-height:120px;
  background:linear-gradient(180deg,#fafcff,#fff); transition:all .18s; position:relative; }
.card:hover { transform:translateY(-3px); box-shadow:0 10px 24px rgba(0,96,230,.14); border-color:#bcd4f2; }
.card .q { font-weight:600; }
.card .a { display:none; margin-top:10px; color:var(--primary-deep); }
.card.open .a { display:block; }
.card.open { background:#f0f7ff; border-color:#8fc2ff; }
.card .hint { font-size:12px; color:#999; margin-top:10px; }
.qitem { padding:14px 0; border-bottom:1px dashed var(--line); }
.qitem .ans { display:none; background:#f7f9fc; border-radius:10px; padding:11px 15px; margin-top:8px; font-size:14px; color:#333; border-left:4px solid #4db3ff; }
.qitem.open .ans { display:block; }
.plan-day { display:flex; gap:14px; padding:13px 0; border-bottom:1px dashed var(--line); align-items:flex-start; }
.plan-day .day { flex:0 0 64px; font-weight:800; color:var(--primary); font-size:15px; }
.plan-day .content { flex:1; font-size:14px; }
.plan-day .tips { font-size:12px; color:var(--muted); margin-top:4px; }
.chan { font-size:14px; padding:8px 0; }
.ai-tag { display:inline-block; font-size:11px; color:var(--muted); background:#f4f6f9; border-radius:10px; padding:1px 9px; margin-left:6px; vertical-align:2px; }
.point-actions { margin-top:9px; display:flex; gap:8px; flex-wrap:wrap; }
.mini-btn { font-size:12px; padding:5px 14px; border-radius:999px; border:1px solid var(--line); background:#fff; color:var(--ink-2); cursor:pointer; transition:all .15s; }
.mini-btn:hover { border-color:var(--primary); color:var(--primary); transform:translateY(-1px); }
.ask-panel { position:fixed; bottom:0; left:50%; transform:translateX(-50%); width:min(620px,96%); background:#fff;
  border-radius:18px 18px 0 0; box-shadow:0 -4px 24px rgba(0,0,0,.18); padding:16px; display:none; z-index:99; }
.ask-panel.open { display:block; }
.ask-head { display:flex; justify-content:space-between; align-items:center; font-weight:700; font-size:15px; }
.ask-close { cursor:pointer; color:var(--muted); border:none; background:none; font-size:16px; }
.ask-log { max-height:260px; overflow:auto; margin-top:10px; font-size:14px; }
.ask-msg { margin-bottom:10px; }
.ask-msg .u { color:var(--primary); }
.ask-msg .a { background:#f4f6f9; border-radius:10px; padding:8px 12px; }
.ask-input { display:flex; gap:8px; margin-top:10px; }
.ask-input input { flex:1; padding:9px 13px; border:1px solid var(--line); border-radius:10px; font-size:14px; outline:none; }
.ask-input input:focus { border-color:var(--primary); }
.ask-input button { border:none; background:linear-gradient(135deg,#0084ff,#0060e6); color:#fff; border-radius:10px; padding:0 16px; cursor:pointer; }
.tree-module { font-weight:700; margin:13px 0 4px; font-size:15px; }
.tree-leaf { font-size:14px; padding:2px 0 2px 18px; color:#444; }
.quadrant { display:grid; grid-template-columns:1fr 1fr; gap:12px; }
.quad { border-radius:14px; padding:15px; border:1px solid var(--line); transition:box-shadow .15s; }
.quad:hover { box-shadow:0 6px 16px rgba(30,60,110,.08); }
.quad h3 { font-size:14px; margin-bottom:8px; }
.quad.q1 { background:linear-gradient(180deg,#fff5f4,#fff); border-color:#f7d8d0; } .quad.q1 h3 { color:#e5484d; }
.quad.q2 { background:linear-gradient(180deg,#fdf8ec,#fff); border-color:#f4e3bd; } .quad.q2 h3 { color:#b8860b; }
.quad.q3 { background:linear-gradient(180deg,#f0f7ff,#fff); border-color:#d6e7fb; } .quad.q3 h3 { color:#0060e6; }
.quad.q4 { background:linear-gradient(180deg,#f3fbf6,#fff); border-color:#cfeeda; } .quad.q4 h3 { color:#1e7a46; }
.quad label { display:block; font-size:13px; padding:4px 0; cursor:pointer; }
.quad input { margin-right:6px; accent-color:var(--primary); }
footer { text-align:center; color:var(--muted); font-size:12px; margin-top:32px; }
.mjx-chtml { font-size:105% !important; margin:.4em 0; }
.qitem .q, .qitem .ans, .card .q, .card .a { overflow-wrap:anywhere; }
@media (max-width:640px) {
  .wrap { padding:16px 12px 60px; }
  header.hero { padding:26px 20px; border-radius:16px; }
  header.hero h1 { font-size:22px; }
  section { padding:20px 16px; border-radius:14px; }
  .quadrant { grid-template-columns:1fr; }
  .plan-day .day { flex:0 0 48px; }
}
@media print { section { box-shadow:none; border:1px solid #ddd; } .card .a { display:block; } .qitem .ans { display:block; } }
"""

MATHJAX = """
<script>
window.MathJax = {
  tex: { inlineMath: [['\\(', '\\)'], ['$', '$']], displayMath: [['\\[', '\\]']] },
  options: { enableMenu: false },
  startup: {
    ready: () => {
      MathJax.startup.defaultReady();
      // 兜底:MathJax 解析失败的公式块(保留原文)转成可读文本
      MathJax.startup.promise.then(() => {
        document.querySelectorAll('mjx-merror, .MathJax_Error').forEach(el => {
          el.textContent = tex2text(el.textContent);
          el.style.color = 'inherit';
          el.style.fontSize = 'inherit';
        });
      });
    }
  }
};
function tex2text(s) {
  s = s.replace(/\\\\frac\\{([^{}]*)\\}\\{([^{}]*)\\}/g, '($1)/($2)');
  s = s.replace(/\\\\sqrt\\{([^{}]*)\\}/g, '√($1)');
  s = s.replace(/\\\\int(?:_\\{([^{}]*)\\})?\\^\\{([^{}]*)\\}/g, '∫[$1,$2]');
  s = s.replace(/\\\\int/g, '∫');
  s = s.replace(/\\\\lim(?:_\\{([^{}]*)\\})?/g, 'lim$1');
  s = s.replace(/\\^\\{([^{}]*)\\}/g, '^($1)');
  s = s.replace(/\\^([A-Za-z0-9])/g, '^$1');
  s = s.replace(/\\\\to/g, '→');
  s = s.replace(/\\\\cdot/g, '·');
  s = s.replace(/\\\\alpha/g, 'α').replace(/\\\\beta/g, 'β').replace(/\\\\pi/g, 'π').replace(/\\\\theta/g, 'θ').replace(/\\\\infty/g, '∞');
  s = s.replace(/\\\\qquad|\\\\quad|\\\\;/g, ' ');
  s = s.replace(/\\\\left|\\\\right|\\\\begin\\{[^{}]*\\}|\\\\end\\{[^{}]*\\}/g, '');
  s = s.replace(/\\\\\\\\(?!\\\\)/g, ' ');
  s = s.replace(/[\\\\[\\]\\(\\)]/g, '');
  return s;
}
</script>
<script id="MathJax-script" async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-chtml.js"></script>
"""

JS = """
function flip(el){ el.classList.toggle('open'); }
let ASK_POINT = null;
function askAI(i){
  ASK_POINT = i;
  document.getElementById('ask-title').textContent = '💬 问AI · 知识点 ' + (i+1);
  document.getElementById('ask-log').innerHTML = '<div class="ask-msg a">你好!关于这个知识点有什么想问的?比如"能举个例子吗"、"考试会怎么考"。</div>';
  document.getElementById('ask-panel').classList.add('open');
}
function askClose(){ document.getElementById('ask-panel').classList.remove('open'); }
function askSend(){
  const input = document.getElementById('ask-q');
  const q = input.value.trim();
  if(!q || ASK_POINT === null) return;
  const log = document.getElementById('ask-log');
  log.insertAdjacentHTML('beforeend', '<div class="ask-msg u">我:' + q.replace(/</g,'&lt;') + '</div>');
  input.value = '';
  log.insertAdjacentHTML('beforeend', '<div class="ask-msg a">思考中…</div>');
  fetch('/api/ask', {method:'POST', headers:{'Content-Type':'application/json'},
    body: JSON.stringify({task_id: TASK_ID, point_index: ASK_POINT, question: q})})
  .then(r => r.json())
  .then(d => {
    log.lastElementChild.textContent = d.answer || (d.detail || '回答失败,请重试');
  });
}
function vote(i, v, el){
  fetch('/api/feedback', {method:'POST', headers:{'Content-Type':'application/json'},
    body: JSON.stringify({task_id: TASK_ID, point_index: i, vote: v})})
  .then(r => r.json()).then(() => {
    el.textContent = v === 'useful' ? '✓ 已标记' : '✗ 已标记';
    el.style.color = v === 'useful' ? '#00a854' : '#e5484d';
    el.disabled = true;
  });
}
// 四象限打卡:localStorage 保存勾选状态
(function(){
  const KEY = 'fm-quad-' + TASK_ID;
  let state = {};
  try { state = JSON.parse(localStorage.getItem(KEY) || '{}'); } catch(e){}
  document.querySelectorAll('.quad-check').forEach(cb => {
    const id = cb.dataset.q + '-' + cb.dataset.i;
    cb.checked = !!state[id];
    cb.addEventListener('change', () => {
      state[id] = cb.checked;
      try { localStorage.setItem(KEY, JSON.stringify(state)); } catch(e){}
    });
  });
})();
"""


def _badge(level: str) -> str:
    color = LEVEL_COLORS.get(level, "#8e8e93")
    return f'<span class="lv" style="background:{color}">{html.escape(str(level))}</span>'


def _render_points(points: list, experiences: dict) -> str:
    rows = []
    for idx, p in enumerate(points):
        exps = experiences.get(str(idx), [])
        exp_html = ""
        for e in exps:
            title = html.escape(str(e.get("来源标题", ""))[:40])
            link = html.escape(str(e.get("来源链接", "")))
            text = html.escape(str(e.get("经验", "")))
            exp_html += f'<div class="exp">💬 {text} — <a href="{link}" target="_blank">{title}</a></div>'
        rows.append(
            f'<div class="point" id="point-{idx}"><div class="name">{html.escape(str(p.get("知识点", "")))}'
            f'{_badge(p.get("考点等级", ""))}<span class="ai-tag">🤖 AI生成</span></div>'
            f'<div class="dir">🎯 {html.escape(str(p.get("出题方向", "")))}</div>'
            f'<div class="base">📖 依据:{html.escape(str(p.get("依据", "")))}</div>'
            f'{exp_html}'
            f'<div class="point-actions">'
            f'<button class="mini-btn" onclick="askAI({idx})">💬 问AI</button>'
            f'<button class="mini-btn" onclick="vote({idx}, &#39;useful&#39;, this)">✓ 有用</button>'
            f'<button class="mini-btn" onclick="vote({idx}, &#39;wrong&#39;, this)">✗ 有误</button>'
            f'</div></div>'
        )
    return "\n".join(rows)


def _render_cards(cards: list) -> str:
    items = []
    for c in cards:
        q = html.escape(normalize(str(c.get("q", ""))))
        a = html.escape(normalize(str(c.get("a", ""))))
        items.append(
            f'<div class="card" onclick="flip(this)"><div class="q">❓ {q}</div>'
            f'<div class="a">✅ {a}</div>'
            f'<div class="hint">点击卡片查看答案</div></div>'
        )
    return "\n".join(items)


def _render_exam(exam: list) -> str:
    items = []
    for i, q in enumerate(exam, 1):
        stem = html.escape(normalize(str(q.get("题干", ""))))
        ans = html.escape(normalize(str(q.get("参考答案", ""))))
        point = html.escape(str(q.get("考点", "")))
        items.append(
            f'<div class="qitem" onclick="flip(this)"><div class="q">第{i}题.{stem}</div>'
            f'<div class="ans">参考答案:{ans}　考点:{point}</div></div>'
        )
    return "\n".join(items)


def _render_plan(plan: dict) -> str:
    rows = []
    for day in plan.get("days", []):
        learn = "、".join(p.get("知识点", "") for p in day.get("learn", [])) or "—"
        review = "、".join(p.get("知识点", "") for p in day.get("review", [])) or "—"
        rows.append(
            f'<div class="plan-day"><div class="day">Day {day.get("day")}</div>'
            f'<div class="content">🆕 新学:{html.escape(learn)}<br>🔁 复习:{html.escape(review)}'
            f'<div class="tips">💡 {html.escape(str(day.get("tips", "")))}</div></div></div>'
        )
    return "\n".join(rows)


QUADRANTS = [
    ("q1", "Ⅰ 重要且紧急 · 高频考点,优先攻克", "高频"),
    ("q2", "Ⅱ 重要不紧急 · 中频考点,按计划推进", "中频"),
    ("q3", "Ⅲ 紧急不重要 · 每日打卡(抽认卡/错题)", "__daily__"),
    ("q4", "Ⅳ 不重要不紧急 · 低频考点,有空再看", "低频"),
]


def _render_quadrant(points: list, task_id: int | None) -> str:
    """四象限任务看板:按考点等级分象限,可勾选打卡。"""
    cells = []
    for cls, title, level in QUADRANTS:
        if level == "__daily__":
            items = [
                "今天过一遍所有抽认卡(点击卡片翻面自测)",
                "重做模拟题中的错题",
                "睡前复述一遍今天新学的知识点",
            ]
        else:
            items = [str(p.get("知识点", "")) for p in points if str(p.get("考点等级", "")) == level]
        if not items:
            items = ["(暂无)"]
        body = "".join(
            f'<label><input type="checkbox" class="quad-check" data-task="{task_id}" data-q="{cls}" data-i="{i}"> {html.escape(t)}</label>'
            for i, t in enumerate(items)
        )
        cells.append(f'<div class="quad {cls}"><h3>{title}</h3>{body}</div>')
    return "\n".join(cells)


def _render_tree(points: list) -> str:
    """知识结构树:按依据(章节/模块)分组。"""
    groups: dict[str, list[str]] = {}
    for p in points:
        key = str(p.get("依据", "")).strip() or "其他"
        groups.setdefault(key, []).append(str(p.get("知识点", "")))
    rows = []
    for module, items in groups.items():
        leaves = "".join(f'<div class="tree-leaf">· {html.escape(i)}</div>' for i in items)
        rows.append(f'<div class="tree-module">📂 {html.escape(module)}</div>{leaves}')
    return "\n".join(rows)


def render_report(result: dict, task_id: int | None = None) -> str:
    """把管线结果渲染为单文件 HTML。task_id 用于反馈与问AI接口。"""
    course = result.get("course", "")
    exam_date = result.get("exam_date") or "未设置"
    days = result.get("days", 7)
    points = result.get("points", [])
    experiences = result.get("experiences", {})
    general = result.get("general_experiences", [])
    cards = result.get("cards", [])
    exam = result.get("exam", [])
    plan = result.get("plan", {"days": []})
    channels = result.get("channels", [])
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    general_html = "\n".join(
        f'<div class="exp">💬 {html.escape(str(e.get("经验", "")))} — '
        f'<a href="{html.escape(str(e.get("来源链接", "")))}" target="_blank">{html.escape(str(e.get("来源标题", ""))[:40])}</a></div>'
        for e in general
    )
    channels_html = "\n".join(
        f'<div class="chan">🔗 <a href="{html.escape(str(c.get("链接", "")))}" target="_blank">{html.escape(str(c.get("渠道", "")))}</a>'
        f' — {html.escape(str(c.get("说明", "")))}</div>'
        for c in channels
    ) or '<div class="chan">本课程暂无公开官方真题渠道,建议以课件+模拟题为主复习。</div>'

    return f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(course)}期末复习方案 - 期末搭子</title>
<style>{CSS}</style></head>
<body><div class="wrap">
<header class="hero">
  <h1>📚 {html.escape(course)} · 期末复习方案</h1>
  <div class="meta">
    <span class="badge">考试日期:{html.escape(str(exam_date))}</span>
    <span class="badge">剩余 {days} 天</span>
    <span class="badge">生成于 {now}</span>
  </div>
</header>

<section><h2>一、AI 划重点({len(points)} 个 · AI 生成,仅供参考,欢迎反馈)</h2>
{_render_tree(points)}
</section>

<section><h2>二、重点详解</h2>
{_render_points(points, experiences)}</section>

<section><h2>三、知乎过来人经验(来自真实用户,点击可看原帖)</h2>
{general_html or '<p>暂无</p>'}</section>

<section><h2>四、抽认卡({len(cards)} 张 · 点击翻面)</h2>
<div class="cards">{_render_cards(cards)}</div></section>

<section><h2>五、模拟题({len(exam)} 题 · 点击题目看答案)</h2>
{_render_exam(exam)}</section>

<section><h2>六、复习计划({len(plan.get("days", []))} 天 · 遗忘曲线)</h2>
{_render_plan(plan)}</section>

<section><h2>七、四象限任务看板(勾选打卡,进度自动保存)</h2>
<div class="quadrant">{_render_quadrant(points, task_id)}</div></section>

<section><h2>八、真题获取渠道</h2>
{channels_html}</section>

<footer>由「期末搭子」生成 · 重点与经验数据来自知乎开放平台(保留原始链接)· 内容仅供学习参考</footer>
</div>
<div class="ask-panel" id="ask-panel">
  <div class="ask-head"><span id="ask-title">💬 问AI</span><button class="ask-close" onclick="askClose()">✕</button></div>
  <div class="ask-log" id="ask-log"></div>
  <div class="ask-input">
    <input id="ask-q" placeholder="输入你的问题,回车发送" onkeydown="if(event.key==='Enter')askSend()">
    <button onclick="askSend()">发送</button>
  </div>
</div>
<script>const TASK_ID = {task_id or 'null'};</script>
<script>{JS}</script>{MATHJAX}</body></html>"""
