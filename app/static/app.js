// 搭子参谋前端逻辑:双场景(学习/生活)
const $ = (id) => document.getElementById(id);

// ---------- 场景切换(参谋/复习/记录) ----------
function switchScene(scene) {
  document.querySelectorAll(".top-tab").forEach((t) => t.classList.toggle("on", t.dataset.scene === scene));
  $("scene-chat").hidden = scene !== "chat";
  $("scene-study").hidden = scene !== "study";
  $("scene-notes").hidden = scene !== "notes";
  $("scene-records").hidden = scene !== "records";
  // 场景背景:生活暖色 / 学习蓝色
  document.body.classList.toggle("scene-chat", scene === "chat");
  document.body.classList.toggle("scene-study", scene === "study");
  if (scene === "chat") loadDaily();
}
document.querySelectorAll(".top-tab").forEach((tab) => {
  tab.addEventListener("click", () => switchScene(tab.dataset.scene));
});

// ---------- 生活参谋对话 ----------
function lifeEsc(s){ return String(s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;'); }

// 会话标识:本地生成,用于轻量记忆(无需登录)
function getSessionId() {
  let sid = localStorage.getItem("fm-session");
  if (!sid) { sid = "s" + Date.now().toString(36) + Math.random().toString(36).slice(2, 8); localStorage.setItem("fm-session", sid); }
  return sid;
}

// ---------- 我的位置(浏览器定位 + 逆地理编码,无外部 Key) ----------
function getMyLocation() {
  try { return localStorage.getItem("fm-loc") || ""; } catch (e) { return ""; }
}

async function locateMe() {
  const bar = $("loc-status");
  bar.textContent = "📍 正在定位…";
  try {
    const pos = await new Promise((resolve, reject) => {
      if (!navigator.geolocation) { reject(new Error("浏览器不支持定位")); return; }
      navigator.geolocation.getCurrentPosition(resolve, reject, { timeout: 8000, maximumAge: 600000, enableHighAccuracy: true });
    });
    const { latitude: lat, longitude: lon, accuracy } = pos.coords;
    // 精度差(>3km)说明走的是 IP/WiFi 粗略定位,可能偏到网络出口城市,不采信
    if (accuracy > 3000) {
      bar.innerHTML = `📍 定位精度较低(±${Math.round(accuracy / 1000)}km),可能不准 → <a href="javascript:void(0)" onclick="setLocationManual()"><b>点此设置你的城市</b></a>`;
      return;
    }
    // 双源反查交叉验证(市+区两级):两个免费源城市一致才采信,取更细的结果
    const results = await Promise.allSettled([
      fetch(`https://nominatim.openstreetmap.org/reverse?format=jsonv2&lat=${lat}&lon=${lon}&zoom=14&accept-language=zh`)
        .then((r) => r.json())
        .then((d) => {
          const a = d.address || {};
          const city = a.city || a.town || "";
          const sub = a.city_district || a.suburb || a.county || "";
          return city && sub && city !== sub ? `${city}${sub}` : (city || sub || "");
        }),
      fetch(`https://api.bigdatacloud.net/data/reverse-geocode-client?latitude=${lat}&longitude=${lon}&localityLanguage=zh`)
        .then((r) => r.json())
        .then((d) => {
          const city = d.city || "";
          const sub = d.locality || d.district || "";
          return city && sub && city !== sub ? `${city}${sub}` : (city || sub || "");
        }),
    ]);
    const vals = results.filter((r) => r.status === "fulfilled" && r.value).map((r) => r.value);
    const cityOf = (s) => (s.match(/^.+?市/) || [s])[0];
    const agree = vals.length >= 2 && cityOf(vals[0]) === cityOf(vals[1]);
    const loc = (agree || vals.length === 1) ? vals[0] : "";
    if (!loc) {
      bar.innerHTML = `📍 无法确认你的位置 → <a href="javascript:void(0)" onclick="setLocationManual()"><b>点此设置你的城市</b></a>(设置一次后自动记住)`;
      return;
    }
    localStorage.setItem("fm-loc", loc);
    bar.innerHTML = `📍 已定位:<b>${lifeEsc(loc)}</b> · 建议会结合你的位置 <a href="javascript:void(0)" onclick="setLocationManual()">不对?点此修改</a>`;
  } catch (e) {
    bar.innerHTML = `📍 定位失败 → <a href="javascript:void(0)" onclick="setLocationManual()"><b>点此设置你的城市</b></a>(设置一次后自动记住)`;
  }
}

function setLocationManual() {
  const v = prompt("你常在哪里?精确到区效果更好(如:江门市蓬江区 / 深圳南山)", getMyLocation() || "");
  if (v !== null && v.trim()) {
    localStorage.setItem("fm-loc", v.trim());
    const bar = $("loc-status");
    bar.innerHTML = `📍 已定位:<b>${lifeEsc(v.trim())}</b> · 建议会结合你的位置 <a href="javascript:void(0)" onclick="setLocationManual()">手动改</a>`;
  }
}

function initLocation() {
  const bar = $("loc-status");
  const loc = getMyLocation();
  if (loc) {
    bar.innerHTML = `📍 已定位:<b>${lifeEsc(loc)}</b> · 建议会结合你的位置 <a href="javascript:void(0)" onclick="setLocationManual()">不对?点此修改</a>`;
  } else {
    locateMe();
  }
}

// ---------- 今日回顾卡片 ----------
async function loadDaily() {
  try {
    const d = await (await fetch('/api/life/daily')).json();
    const card = $("daily-card");
    const parts = [];
    if (d.conversations_today > 0) parts.push(`💬 今天已问 ${d.conversations_today} 个问题`);
    if (d.pending_notes > 0) parts.push(`📝 未完成待办 ${d.pending_notes} 条`);
    if (d.notes_today > 0) parts.push(`今天新增 ${d.notes_today} 条记事`);
    if (d.days_left !== null && d.days_left !== undefined)
      parts.push(`📚 距「${d.course}」考试还有 ${d.days_left} 天`);
    if (parts.length) {
      card.innerHTML = `<div class="daily-inner">📅 今日回顾 · ${parts.join(' · ')}</div>`;
      card.hidden = false;
    } else {
      card.hidden = true;
    }
  } catch (e) { /* 静默失败,不阻塞主流程 */ }
}

async function lifeAsk() {
  const q = $("life-q");
  const text = q.value.trim();
  if (!text) return;
  const chat = $("life-chat");
  chat.insertAdjacentHTML('beforeend',
    `<div class="life-msg user"><div class="life-bubble">${lifeEsc(text)}</div></div>`);
  q.value = '';
  $("life-send").disabled = true;
  const tip = document.createElement('div');
  tip.className = 'life-msg ai';
  tip.innerHTML = '<div class="life-bubble">正在检索知乎真人经验 + 全网公开信息…</div>';
  chat.appendChild(tip);
  chat.scrollTop = chat.scrollHeight;
  try {
    // 追问上下文:上次 AI 追问且本次是简短回答(5分钟内),自动拼回原问题
    let sendText = text;
    try {
      const fu = JSON.parse(localStorage.getItem("fm-followup") || "null");
      if (fu && fu.q && Date.now() - fu.t < 5 * 60 * 1000 && text.length < 20) {
        sendText = fu.q + "。" + text;
      }
      localStorage.removeItem("fm-followup");
    } catch (e) { /* 忽略 */ }
    const r = await fetch('/api/life/chat', {
      method: 'POST', headers: {'Content-Type':'application/json'},
      body: JSON.stringify({message: sendText, session_id: getSessionId(), location: getMyLocation()})
    });
    const d = await r.json();
    tip.remove();
    if (d.detail) {
      chat.insertAdjacentHTML('beforeend',
        `<div class="life-msg ai"><div class="life-bubble">⚠️ ${lifeEsc(d.detail)}</div></div>`);
    } else if (d.is_study) {
      // 考试学习需求:引导到复习功能
      const course = d.intent?.["考试科目"] || "";
      const html = `<div class="advice-card">🎯 检测到<b>考试/学习</b>需求${course ? `(${lifeEsc(course)})` : ''}!<br>
        我可以在 30 秒内为你生成一份「有知乎真人经验背书」的复习方案:重点清单、抽认卡、模拟题、复习计划。<br><br>
        <button class="mini-btn" onclick="gotoStudy('${lifeEsc(course)}')">📚 去生成复习方案 →</button></div>`;
      chat.insertAdjacentHTML('beforeend',
        `<div class="life-msg ai"><div class="life-bubble">${html}</div></div>`);
    } else if (d.is_note) {
      const n = d.note || {};
      const qNames = {1:'Ⅰ 重要且紧急',2:'Ⅱ 重要不紧急',3:'Ⅲ 紧急不重要',4:'Ⅳ 不重要不紧急'};
      const html = `<div class="advice-card">📝 已记入记事本<br>
        <div class="sug">${lifeEsc(n.content || '')}</div>
        <div class="why">${lifeEsc(qNames[n.quadrant] || '')}${n.说明 ? ' · ' + lifeEsc(n.说明) : ''}</div>
        <button class="mini-btn" onclick="switchScene('notes')">🗂 去记事本查看 →</button></div>`;
      chat.insertAdjacentHTML('beforeend',
        `<div class="life-msg ai"><div class="life-bubble">${html}</div></div>`);
    } else if (d.is_followup) {
      // 记录追问上下文,用户回答后自动拼接原问题
      try { localStorage.setItem("fm-followup", JSON.stringify({ q: text, t: Date.now() })); } catch (e) {}
      chat.insertAdjacentHTML('beforeend',
        `<div class="life-msg ai"><div class="life-bubble"><div class="advice-card followup"><div class="sug">❓ 补充一个信息</div><div class="why">${lifeEsc(d.followup_question || '')}</div></div></div></div>`);
    } else if (d.is_position) {
      chat.insertAdjacentHTML('beforeend',
        `<div class="life-msg ai"><div class="life-bubble"><div class="advice-card"><div class="sug">📍 位置</div><div class="why">${lifeEsc(d.position_answer || '')}</div></div></div></div>`);
    } else if (d.is_memory) {
      chat.insertAdjacentHTML('beforeend',
        `<div class="life-msg ai"><div class="life-bubble"><div class="advice-card"><div class="sug">🧠 记忆</div><div class="why">${lifeEsc(d.memory_answer || '')}</div></div></div></div>`);
    } else if (d.is_compare) {
      const c = d.compare || {};
      const rows = (c.要素 || []).map(x =>
        `<tr><td class="dim">${lifeEsc(x.要素名 || '')}</td><td>${lifeEsc(x.A情况 || '?')}</td><td>${lifeEsc(x.B情况 || '?')}</td></tr>`).join('');
      const table = rows ? `<table class="cmp-table"><tr><th>维度</th><th>选项A</th><th>选项B</th></tr>${rows}</table>` : '';
      const verdict = c.结论 ? `<div class="advice-card"><div class="sug">✅ 结论</div><div class="why">${lifeEsc(c.结论)}</div></div>` : '';
      const worst = c.最坏结果 ? `<div class="advice-card"><div class="sug">🛡 最坏结果兜底</div><div class="why">${lifeEsc(c.最坏结果)}</div></div>` : '';
      const meta = `<div class="meta">🔍 双源交叉验证:检索 ${d.searched} 条知乎经验 · 内容均附来源可溯源</div>`;
      chat.insertAdjacentHTML('beforeend',
        `<div class="life-msg ai"><div class="life-bubble">${table}${verdict}${worst}${meta}</div></div>`);
    } else if (d.is_avoid) {
      const av = d.avoid || {};
      const items = (av.清单 || []).map(x =>
        `<div class="trap-card"><div class="sug">⚠️ ${lifeEsc(x.坑)}</div>` +
        `<div class="why">🔍 自查/避开:${lifeEsc(x.检测 || '')}</div>` +
        (x.来源链接 ? `<a href="${lifeEsc(x.来源链接)}" target="_blank">📎 ${lifeEsc(x.来源标题 || '查看来源')} →</a>` : '') +
        `</div>`).join('');
      const summaryHtml = av.总结 ? `<div class="advice-card summary"><div class="sug">📌 一句话总结</div><div class="why">${lifeEsc(av.总结)}</div></div>` : '';
      const meta = `<div class="meta">🔍 检索 ${d.searched} 条知乎真人经验 · 每条坑均附原帖可溯源</div>`;
      chat.insertAdjacentHTML('beforeend',
        `<div class="life-msg ai"><div class="life-bubble"><div class="trap-title">📋 避坑清单(按踩坑人数排序)</div>${items}${summaryHtml}${meta}</div></div>`);
    } else if (d.is_allowance) {
      const al = d.allowance || {};
      const rows = (al.方案 || []).map(x =>
        `<tr><td class="dim">${lifeEsc(x.项目 || '')}</td><td>${lifeEsc(x.金额 || '')}</td><td>${lifeEsc(x.占比 || '')}</td><td>${lifeEsc(x.说明 || '')}</td></tr>`).join('');
      const table = rows ? `<table class="cmp-table"><tr><th>项目</th><th>金额</th><th>占比</th><th>说明</th></tr>${rows}</table>` : '';
      const tips = (al.tips || []).map(t => `<div class="why">💡 ${lifeEsc(t)}</div>`).join('');
      const trapHtml = (al.traps || []).map(t =>
        `<div class="trap-card"><div class="sug">⚠️ ${lifeEsc(t.坑)}</div>` +
        (t.来源链接 ? `<a href="${lifeEsc(t.来源链接)}" target="_blank">📎 ${lifeEsc(t.来源标题 || '查看来源')} →</a>` : '') +
        `</div>`).join('');
      const meta = `<div class="meta">🔍 检索 ${d.searched} 条知乎真人经验 · 内容均附链接可溯源</div>`;
      chat.insertAdjacentHTML('beforeend',
        `<div class="life-msg ai"><div class="life-bubble">${table}${tips}${trapHtml}${meta}</div></div>`);
    } else {
      const intent = d.intent || {};
      window._lastAdvice = d.advice || [];
      const srcTag = (s) => s === 'web'
        ? '<span class="src-tag web">🌐 全网</span>'
        : '<span class="src-tag zhihu">🐱 知乎</span>';
      const cards = (d.advice || []).map((a, i) => {
        const trust = [];
        if (a.来源类型 === 'zhihu' && a.来源作者) trust.push(`答主 ${lifeEsc(a.来源作者)}`);
        if (a.来源类型 === 'zhihu' && (a.来源赞数 || 0) > 0) trust.push(`👍 ${a.来源赞数}`);
        const trustHtml = trust.length ? `<span class="trust">${trust.join(' · ')}</span>` : '';
        return `<div class="advice-card"><div class="sug">💡 ${lifeEsc(a.建议)} ${srcTag(a.来源类型)}</div>` +
          `<div class="why">${lifeEsc(a.理由)}</div>` +
          (a.来源链接 ? `<a href="${lifeEsc(a.来源链接)}" target="_blank">📎 ${lifeEsc(a.来源标题 || '查看来源')} →</a>` + trustHtml : '') +
          `<div class="advice-actions"><button class="mini-btn" id="todo-btn-${i}" onclick="adviceToTodo(${i})">📌 加入我的计划</button></div>` +
          `</div>`;
      }).join('');
      const trapCards = (d.traps || []).map(t =>
        `<div class="trap-card"><div class="sug">⚠️ ${lifeEsc(t.坑)}</div>` +
        (t.来源链接 ? `<a href="${lifeEsc(t.来源链接)}" target="_blank">📎 ${lifeEsc(t.来源标题 || '查看来源')} →</a>` : '') +
        `</div>`).join('');
      const trapHtml = trapCards ? `<div class="trap-title">🚨 避坑雷达(被多人踩过的坑)</div>${trapCards}` : '';
      const tripHtml = d.trip ? `<div class="advice-card trip"><div class="sug">📍 行程建议</div><div class="why">${lifeEsc(d.trip)}</div></div>` : '';
      const transportHtml = d.transport ? `<div class="advice-card transport"><div class="sug">🚇 怎么去</div><div class="why">${lifeEsc(d.transport)}</div></div>` : '';
      const meta = `<div class="meta">类别:${lifeEsc(intent.类别 || '?')} · 地点:${lifeEsc(intent.地点 || '未指定')} · 🔍 双源交叉验证:知乎 ${d.searched} 篇真人经验 + 全网 ${d.web_searched} 条公开信息 · 建议均附链接可溯源</div>`;
      const summaryHtml = d.summary ? `<div class="advice-card summary"><div class="sug">📌 一句话总结</div><div class="why">${lifeEsc(d.summary)}</div></div>` : '';
      chat.insertAdjacentHTML('beforeend',
        `<div class="life-msg ai"><div class="life-bubble">${cards || '暂时没搜到合适的信息,换个说法试试?'}${tripHtml}${transportHtml}${trapHtml}${summaryHtml}${meta}</div></div>`);
    }
  } catch(e) {
    tip.remove();
    chat.insertAdjacentHTML('beforeend',
      `<div class="life-msg ai"><div class="life-bubble">⚠️ 请求失败,请重试</div></div>`);
  }
  $("life-send").disabled = false;
  chat.scrollTop = chat.scrollHeight;
  loadDaily();  // 对话数/待办可能变化,刷新今日回顾
}

$("life-send").addEventListener("click", lifeAsk);
$("life-q").addEventListener("keydown", (e) => { if (e.key === "Enter") lifeAsk(); });

// 校园规则解读:上传文件 → 人话解读+隐藏陷阱
$("life-rule-btn").addEventListener("click", () => $("life-rule-file").click());
$("life-rule-file").addEventListener("change", async (e) => {
  const f = e.target.files[0];
  if (!f) return;
  const chat = $("life-chat");
  chat.insertAdjacentHTML('beforeend',
    `<div class="life-msg user"><div class="life-bubble">📄 ${lifeEsc(f.name)}</div></div>`);
  const tip = document.createElement('div');
  tip.className = 'life-msg ai';
  tip.innerHTML = '<div class="life-bubble">正在解读规则文件…</div>';
  chat.appendChild(tip);
  try {
    const fd = new FormData();
    fd.append("file", f);
    const r = await fetch('/api/life/rule', { method: 'POST', body: fd });
    const d = await r.json();
    tip.remove();
    if (d.detail) {
      chat.insertAdjacentHTML('beforeend',
        `<div class="life-msg ai"><div class="life-bubble">⚠️ ${lifeEsc(d.detail)}</div></div>`);
    } else {
      const items = (d.要点 || []).map(x =>
        `<div class="advice-card"><div class="sug">📖 ${lifeEsc(x.条款 || '')}</div><div class="why">${lifeEsc(x.人话 || '')}</div></div>`).join('');
      const traps = (d.陷阱 || []).map(x =>
        `<div class="trap-card"><div class="sug">⚠️ ${lifeEsc(x.坑 || '')}</div><div class="why">${lifeEsc(x.说明 || '')}</div></div>`).join('');
      const trapHtml = traps ? `<div class="trap-title">🚨 隐藏陷阱</div>${traps}` : '';
      const summaryHtml = d.总结 ? `<div class="advice-card summary"><div class="sug">📌 一句话总结</div><div class="why">${lifeEsc(d.总结)}</div></div>` : '';
      chat.insertAdjacentHTML('beforeend',
        `<div class="life-msg ai"><div class="life-bubble"><div class="trap-title">📋 人话解读</div>${items}${trapHtml}${summaryHtml}</div></div>`);
    }
  } catch (err) {
    tip.remove();
    chat.insertAdjacentHTML('beforeend',
      `<div class="life-msg ai"><div class="life-bubble">⚠️ 解读失败,请重试</div></div>`);
  }
  e.target.value = '';
  chat.scrollTop = chat.scrollHeight;
});

// 识图取链:粘贴截图(Ctrl+V)或上传图片 → OCR+二维码提取可点击链接
async function extractLinks(file) {
  const chat = $("life-chat");
  chat.insertAdjacentHTML('beforeend',
    `<div class="life-msg user"><div class="life-bubble">📷 [识图取链] ${lifeEsc(file.name || '剪贴板截图')}${file.size ? ` (${Math.round(file.size/1024)}KB)` : ''}</div></div>`);
  const tip = document.createElement('div');
  tip.className = 'life-msg ai';
  tip.innerHTML = '<div class="life-bubble">正在识别图片中的链接和二维码…</div>';
  chat.appendChild(tip);
  chat.scrollTop = chat.scrollHeight;
  try {
    const fd = new FormData();
    fd.append("file", file);
    const r = await fetch('/api/life/link-extract', { method: 'POST', body: fd });
    const d = await r.json();
    tip.remove();
    if (d.detail) {
      chat.insertAdjacentHTML('beforeend',
        `<div class="life-msg ai"><div class="life-bubble">⚠️ ${lifeEsc(d.detail)}</div></div>`);
    } else {
      const links = d.links || [];
      const cards = links.map(l =>
        `<div class="link-card"><span class="tag">${l.source === '二维码' ? '🔳 二维码' : '🔤 文字'}</span>` +
        `<a class="url" href="${lifeEsc(l.url)}" target="_blank">${lifeEsc(l.url)}</a>` +
        `<button class="btn" onclick="navigator.clipboard.writeText('${lifeEsc(l.url)}').then(()=>{this.textContent='已复制'})">复制</button></div>`
      ).join('');
      const html = links.length
        ? `<div class="advice-card"><div class="sug">🔗 识别到 ${links.length} 个链接,点击直接打开</div>${cards}</div>`
        : `<div class="advice-card"><div class="sug">🔗 识图取链</div><div class="why">${lifeEsc(d.hint || '没识别出链接,换个清晰一点的截图试试')}</div></div>`;
      chat.insertAdjacentHTML('beforeend',
        `<div class="life-msg ai"><div class="life-bubble">${html}</div></div>`);
    }
  } catch (e) {
    tip.remove();
    chat.insertAdjacentHTML('beforeend',
      `<div class="life-msg ai"><div class="life-bubble">⚠️ 识别失败,请重试</div></div>`);
  }
  chat.scrollTop = chat.scrollHeight;
}

// 悬浮截图按钮:通过 screenlink:// 协议拉起本机置顶悬浮截图工具
$("life-float-btn").addEventListener("click", () => {
  const chat = $("life-chat");
  chat.insertAdjacentHTML('beforeend',
    `<div class="life-msg ai"><div class="life-bubble"><div class="advice-card"><div class="sug">🖼 悬浮截图按钮</div><div class="why">1. 浏览器若弹出「打开外部应用」提示,点允许<br>2. 屏幕右侧会出现一个可拖动的 📷 悬浮按钮<br>3. 看视频时点它 → 框选链接区域 → 自动识别并打开链接<br>(右键悬浮按钮可退出)</div></div></div></div>`);
  chat.scrollTop = chat.scrollHeight;
  // 必须在用户点击手势内同步跳转,否则浏览器会静默拦截外部协议
  location.href = "screenlink://start";
});

$("life-pic-btn").addEventListener("click", () => $("life-pic-file").click());
$("life-pic-file").addEventListener("change", (e) => {
  const f = e.target.files[0];
  if (f) extractLinks(f);
  e.target.value = '';
});
document.addEventListener("paste", (e) => {
  const items = (e.clipboardData || {}).items;
  if (!items) return;
  for (const it of items) {
    if (it.type && it.type.startsWith("image/")) {
      const f = it.getAsFile();
      if (f) { e.preventDefault(); extractLinks(f); }
      break;
    }
  }
});

// 把采纳的建议转成执行待办(进四象限记事本)
async function adviceToTodo(i) {
  const a = window._lastAdvice && window._lastAdvice[i];
  if (!a) return;
  const btn = document.getElementById(`todo-btn-${i}`);
  if (btn) { btn.disabled = true; btn.textContent = "⏳ 加入中…"; }
  try {
    const r = await fetch('/api/life/todo', {
      method: 'POST', headers: {'Content-Type':'application/json'},
      body: JSON.stringify({content: a.建议 || ''})
    });
    const d = await r.json();
    if (btn) { btn.textContent = d.ok ? "✅ 已加入记事本" : "⚠️ 失败,重试"; btn.disabled = !d.ok; }
    loadDaily();
  } catch (e) {
    if (btn) { btn.textContent = "⚠️ 失败,重试"; btn.disabled = false; }
  }
}

// 今日外刊:全网公开英文新闻 + AI 中文导读
async function loadNews() {
  const box = $("news-result");
  box.innerHTML = '<div class="empty">正在拉取全网公开新闻…(约10-20秒)</div>';
  try {
    const d = await (await fetch('/api/news/today')).json();
    if (d.detail) { box.innerHTML = `<div class="empty">⚠️ ${lifeEsc(d.detail)}</div>`; return; }
    const news = d.news || [];
    if (!news.length) { box.innerHTML = '<div class="empty">暂时没拉到新闻,稍后再试</div>'; return; }
    box.innerHTML = news.map(n =>
      `<div class="news-card"><span class="tag">${lifeEsc(n.分类 || '新闻')}</span>` +
      `<a class="t" href="${lifeEsc(n.链接)}" target="_blank">${lifeEsc(n.标题)}</a>` +
      `<div class="zh">💡 ${lifeEsc(n.导读)}</div>` +
      `<div class="src">来源:${lifeEsc(n.来源 || '公开网页')} · 点击标题查看原文</div></div>`
    ).join('');
  } catch (e) { box.innerHTML = '<div class="empty">⚠️ 拉取失败,请重试</div>'; }
}
$("btn-news").addEventListener("click", loadNews);

// 数据洞察:大脑地图 / 每周反思 / 人物卡片
async function loadInsight(kind) {
  const box = $("insight-result");
  box.innerHTML = '<div class="empty">⏳ 分析中…</div>';
  try {
    if (kind === "map") {
      const d = await (await fetch('/api/insight/map')).json();
      const cats = d.categories || [];
      const max = Math.max(1, ...cats.map(c => c.n));
      const bars = cats.map(c =>
        `<div class="cat-bar"><span class="cat-name">${lifeEsc(c.name)}</span>` +
        `<span class="cat-track"><i style="width:${Math.round(c.n / max * 100)}%"></i></span>` +
        `<span class="cat-n">${c.n}</span></div>`).join('');
      const tl = (d.timeline || []).slice(0, 12).map(t =>
        `<div class="tl-item"><span class="tl-time">${lifeEsc(t.time)}</span>` +
        `<span class="tl-cat">${lifeEsc(t.category)}</span>${lifeEsc(t.message)}</div>`).join('');
      const fb = d.feedbacks || {};
      box.innerHTML =
        `<div class="insight-title">🗺 话题分布</div>${bars || '<div class="empty">还没有对话数据</div>'}` +
        `<div class="insight-title">🕐 近期动向时间线</div>${tl || '<div class="empty">暂无</div>'}` +
        `<div class="insight-title">📊 反馈闭环</div><div class="empty">有用 ${fb.useful || 0} · 有误 ${fb.wrong || 0} — 你的反馈会用于持续改进内容质量</div>`;
    } else if (kind === "weekly") {
      const d = await (await fetch('/api/insight/weekly', { method: 'POST' })).json();
      box.innerHTML = `<div class="advice-card"><div class="sug">📅 每周反思卡片</div>` +
        `<div class="why">🔍 ${lifeEsc(d.回顾 || '')}</div>` +
        `<div class="why">💡 ${lifeEsc(d.建议 || '')}</div>` +
        `<div class="why">🌟 ${lifeEsc(d.亮点 || '')}</div></div>`;
    } else if (kind === "persons") {
      const d = await (await fetch('/api/insight/persons', { method: 'POST' })).json();
      const ps = d.persons || [];
      box.innerHTML = ps.length
        ? `<div class="insight-title">👥 提到的人</div>` + ps.map(p =>
          `<div class="person-card"><div class="p-name">${lifeEsc(p.称呼 || '')}</div>` +
          `<div class="why">💬 ${lifeEsc(p.话题 || '')}</div>` +
          (p.建议 ? `<div class="why">💡 ${lifeEsc(p.建议)}</div>` : '') + `</div>`).join('')
        : '<div class="empty">最近的对话里没有提到具体的人</div>';
    }
  } catch (e) { box.innerHTML = '<div class="empty">⚠️ 分析失败,请重试</div>'; }
}
$("btn-insight-map").addEventListener("click", () => loadInsight("map"));
$("btn-insight-weekly").addEventListener("click", () => loadInsight("weekly"));
$("btn-insight-persons").addEventListener("click", () => loadInsight("persons"));

// 快捷提问
document.querySelectorAll(".quick-chip").forEach((chip) => {
  chip.addEventListener("click", () => {
    $("life-q").value = chip.dataset.q;
    lifeAsk();
  });
});

// 从参谋跳转到复习功能
function gotoStudy(course) {
  switchScene("study");
  if (course) {
    $("course").value = course;
    $("course").dispatchEvent(new Event("change"));
    syncButton();
  }
}

// ---------- 四象限记事本 ----------
const Q_INFO = {
  1: { title: "Ⅰ 重要且紧急", color: "#e5484d", bg: "#fdeeee" },
  2: { title: "Ⅱ 重要不紧急", color: "#b8860b", bg: "#fdf6e8" },
  3: { title: "Ⅲ 紧急不重要", color: "#0060e6", bg: "#eaf4ff" },
  4: { title: "Ⅳ 不重要不紧急", color: "#8a919f", bg: "#f4f6f9" },
};

async function loadNotes() {
  const data = await (await fetch("/api/notes")).json();
  const board = $("note-board");
  if (!board) return;
  board.innerHTML = [1, 2, 3, 4].map((q) => {
    const items = (data.items || []).filter((n) => n.quadrant === q);
    return `<div class="note-quad" style="background:${Q_INFO[q].bg}">
      <div class="note-quad-title" style="color:${Q_INFO[q].color}">${Q_INFO[q].title}</div>
      ${items.map((n) => `
        <div class="note-item ${n.done ? "done" : ""}">
          <input type="checkbox" ${n.done ? "checked" : ""} onchange="toggleNote(${n.id})">
          <span>${lifeEsc(n.content)}</span>
          <button class="note-del" onclick="delNote(${n.id})">✕</button>
        </div>`).join("") || '<div class="note-empty">(空)</div>'}
    </div>`;
  }).join("");
}

async function addNote() {
  const content = $("note-text").value.trim();
  if (!content) return;
  await fetch("/api/notes", {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ content, quadrant: parseInt($("note-quadrant").value) }),
  });
  $("note-text").value = "";
  loadNotes();
}

async function suggestNote() {
  const content = $("note-text").value.trim();
  if (!content) { alert("先输入事项内容"); return; }
  $("note-suggest-result").textContent = "AI 分析中…";
  const r = await fetch("/api/notes/suggest", {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ content }),
  });
  const d = await r.json();
  if (d.detail) { $("note-suggest-result").textContent = d.detail; return; }
  $("note-quadrant").value = String(d["象限"]);
  $("note-suggest-result").textContent = `🤖 建议放「${d["象限名"]}」—— ${d["说明"]}`;
}

async function toggleNote(id) { await fetch(`/api/notes/${id}/toggle`, { method: "POST" }); loadNotes(); }
async function delNote(id) { await fetch(`/api/notes/${id}`, { method: "DELETE" }); loadNotes(); }

$("btn-note-add").addEventListener("click", addNote);
$("btn-note-suggest").addEventListener("click", suggestNote);
$("note-text").addEventListener("keydown", (e) => { if (e.key === "Enter") addNote(); });
document.querySelectorAll(".top-tab[data-scene='notes']").forEach((t) => t.addEventListener("click", loadNotes));
loadNotes();

// ---------- 上传区 ----------
const drop = $("drop");
const fileInput = $("file");
const btnGenerate = $("btn-generate");
let currentDocId = null;
let currentFilename = null;

drop.addEventListener("click", () => fileInput.click());
drop.addEventListener("dragover", (e) => { e.preventDefault(); drop.classList.add("over"); });
drop.addEventListener("dragleave", () => drop.classList.remove("over"));
drop.addEventListener("drop", (e) => {
  e.preventDefault();
  drop.classList.remove("over");
  if (e.dataTransfer.files.length) { fileInput.files = e.dataTransfer.files; onFile(); }
});
fileInput.addEventListener("change", onFile);

// 按钮启用条件:课程名非空即可(文件为可选项)
function syncButton() {
  btnGenerate.disabled = !$("course").value.trim();
}
$("course").addEventListener("input", syncButton);

// ---------- 快速选课按钮 ----------
document.querySelectorAll(".course-chip").forEach((chip) => {
  chip.addEventListener("click", () => {
    $("course").value = chip.dataset.course;
    $("course").dispatchEvent(new Event("change"));
    syncButton();
    document.querySelectorAll(".course-chip").forEach((c) => c.classList.remove("picked"));
    chip.classList.add("picked");
  });
});

// ---------- 章节选择 + 试卷风格 ----------
let selectedChapters = [];

$("course").addEventListener("change", async () => {
  const course = $("course").value.trim();
  selectedChapters = [];
  const box = $("chapters-box");
  // 风格库
  try {
    const st = await (await fetch("/api/styles?course=" + encodeURIComponent(course))).json();
    const sel = $("exam-style");
    sel.innerHTML = '<option value="">默认</option>' +
      (st.styles || []).map((s) => `<option value="${s}">${s}</option>`).join("");
  } catch { /* 忽略 */ }
  if (!course) { box.hidden = true; return; }
  try {
    const data = await (await fetch("/api/syllabus?course=" + encodeURIComponent(course))).json();
    if (!data.chapters || !data.chapters.length) { box.hidden = true; return; }
    $("chapters-grid").innerHTML = data.chapters.map((ch) =>
      `<span class="chapter-chip on" data-ch="${ch}">${ch}</span>`).join("");
    selectedChapters = [...data.chapters];  // 默认全选
    document.querySelectorAll(".chapter-chip").forEach((chip) => {
      chip.addEventListener("click", () => {
        chip.classList.toggle("on");
        selectedChapters = [...document.querySelectorAll(".chapter-chip.on")].map((c) => c.dataset.ch);
      });
    });
    box.hidden = false;
  } catch { box.hidden = true; }
});

function onFile() {
  const f = fileInput.files[0];
  if (f) {
    currentFilename = f.name;
    drop.querySelector(".drop-text").innerHTML = `已选择:<strong>${f.name}</strong><br><small>点击可重新选择(不选也行,将在线生成)</small>`;
  }
}

const STAGE_NAMES = {
  material: "🌐 在线检索课程资料…",
  highlighting: "✍️ AI 划重点中…",
  searching: "🔍 检索知乎过来人经验…",
  cards: "🃏 生成抽认卡…",
  exam: "📝 生成模拟题…",
  plan: "📅 排复习计划…",
  done: "完成!",
  failed: "生成失败",
};

btnGenerate.addEventListener("click", async () => {
  const f = fileInput.files[0];
  const course = $("course").value.trim();
  if (!course) { alert("请先填写课程名"); return; }
  btnGenerate.disabled = true;
  $("progress").hidden = false;
  $("result").hidden = true;
  setStage("uploading", "📤 上传中…");
  try {
    if (f) {
      // 1a. 上传文件
      const fd = new FormData();
      fd.append("file", f);
      const up = await fetch("/api/upload", { method: "POST", body: fd });
      const upData = await up.json();
      if (!up.ok) throw new Error(upData.detail || "上传失败");
      currentDocId = upData.doc_id;
    } else {
      currentDocId = null;
    }

    // 2. 创建生成任务(doc_id=null 时为无文件在线模式;chapters 为勾选范围)
    const gen = await fetch("/api/generate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        doc_id: currentDocId,
        course,
        exam_date: $("exam_date").value || null,
        chapters: currentDocId ? null : (selectedChapters.length ? selectedChapters : null),
        style: $("exam-style").value || null,
      }),
    });
    const genData = await gen.json();
    if (!gen.ok) throw new Error(genData.detail || "创建任务失败");
    pollTask(genData.task_id);
  } catch (err) {
    setStage("failed", "❌ " + err.message);
    btnGenerate.disabled = false;
  }
});

async function pollTask(taskId) {
  const t = await (await fetch(`/api/task/${taskId}`)).json();
  setStage(t.status, STAGE_NAMES[t.status.split(":")[0]] || t.status);
  if (t.status === "done") {
    $("report-link").href = `/api/report/${taskId}`;
    $("result").hidden = false;
    btnGenerate.disabled = false;
    loadHistory();
    return;
  }
  if (t.status === "failed") {
    setStage("failed", "❌ 生成失败:" + (t.status.split(":").slice(1).join(":") || "未知错误"));
    btnGenerate.disabled = false;
    return;
  }
  setTimeout(() => pollTask(taskId), 2000);
}

function setStage(stage, text) {
  const steps = ["uploading", "material", "highlighting", "searching", "cards", "exam", "plan"];
  const idx = steps.indexOf(stage.split(":")[0]);
  $("bar-fill").style.width = stage === "done" ? "100%" : Math.max(8, ((idx + 1) / (steps.length + 1)) * 100) + "%";
  $("stage-text").textContent = text;
}

// ---------- 历史 ----------
async function loadHistory() {
  const data = await (await fetch("/api/tasks")).json();
  const items = data.items || [];
  if (!items.length) { $("history").innerHTML = '<div class="empty">还没有生成记录,上传课件试试!</div>'; return; }
  $("history").innerHTML = items.map((t) => {
    const isDone = t.status === "done";
    const st = t.status.split(":")[0];
    return `<div class="item">
      <span>${t.course} <small style="color:#8a919f">${t.exam_date || ""}</small></span>
      <span><span class="st ${st}">${st}</span>${isDone ? ` <a href="/api/report/${t.id}" target="_blank">查看报告 →</a>` : ""}</span>
    </div>`;
  }).join("");
}
loadHistory();
loadDaily();
initLocation();

// ---------- 知识库检索 ----------
// (旧按钮已移除,事件绑定见下方双通道逻辑)

// ---------- 知识库检索(双通道) ----------
let searchMode = "local";
$("btn-search-local").addEventListener("click", () => { searchMode = "local"; syncTabs(); doSearch(); });
$("btn-search-global").addEventListener("click", () => { searchMode = "global"; syncTabs(); doSearch(); });
$("search-q").addEventListener("keydown", (e) => { if (e.key === "Enter") doSearch(); });

function syncTabs() {
  $("btn-search-local").classList.toggle("on", searchMode === "local");
  $("btn-search-global").classList.toggle("on", searchMode === "global");
}

async function doSearch() {
  const q = $("search-q").value.trim();
  if (!q) return;
  const data = await (await fetch("/api/search?q=" + encodeURIComponent(q) + "&mode=" + searchMode)).json();
  const hits = data.hits || [];
  if (!hits.length) { $("search-result").innerHTML = `<div class="empty">"${q}" 没有命中</div>`; return; }
  if (searchMode === "local") {
    $("search-result").innerHTML = hits.map((h) =>
      `<div class="hit">${h.snippet}<div class="file">来自:${h.filename} · <a href="/api/document/${h.doc_id}/raw" target="_blank">查看原文 →</a></div></div>`
    ).join("");
  } else {
    $("search-result").innerHTML = hits.map((h) =>
      `<div class="hit"><strong>${h.title}</strong><div>${h.snippet}</div><a href="${h.url}" target="_blank">知乎原帖 →</a></div>`
    ).join("");
  }
}

// ---------- 待办识别 ----------
$("btn-todo").addEventListener("click", doTodo);
$("todo-text").addEventListener("keydown", (e) => { if (e.key === "Enter") doTodo(); });

async function doTodo() {
  const text = $("todo-text").value.trim();
  if (!text) return;
  $("todo-result").innerHTML = '<div class="empty">AI 分析中…</div>';
  const data = await (await fetch("/api/todo/analyze", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text }),
  })).json();
  if (data.detail) { $("todo-result").innerHTML = `<div class="empty">${data.detail}</div>`; return; }
  const isExam = data.type === "考试" && data["考试科目"];
  const tip = isExam
    ? `建议:去上方上传/生成「${data["考试科目"]}」的复习方案(日期 ${data["考试日期"] || "未提到"})。`
    : `建议:${data.建议 || "—"}`;
  $("todo-result").innerHTML = `<div class="hit">
    类型:<strong>${data.type || "?"}</strong>${data["考试科目"] ? ` · 科目:${data["考试科目"]}` : ""}
    ${data["考试日期"] ? ` · 日期:${data["考试日期"]}` : ""}
    <div>${tip}</div></div>`;
}
