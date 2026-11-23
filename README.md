# 搭子参谋 FinalMate

知乎黑客松 S3・湾区共创季 | 赛道:AI × 知识与探索 | 大学生第一 AI 参谋

**公网地址**: https://finalmate-352354-12-1538712646.sh.run.tcloudbase.com

上传课件/只填课程名 → 30 秒生成「有知乎过来人经验背书」的复习方案;生活决策对话,每条建议带知乎原帖链接可溯源。

## 功能全景(五 tab)

| Tab | 功能 |
|---|---|
| 💬 参谋 | 生活决策对话:意图理解→知乎经验+全网信息+记忆→建议/行程/交通/避坑,每条带来源;主动追问;一键转待办;规则文件解读;**识图取链**(粘贴/上传截图→OCR+二维码提取链接) |
| 📚 复习 | 复习方案生成(重点+抽认卡+模拟题+遗忘曲线计划),依据逐字校验,风格库,伴随式问AI,反馈闭环 |
| 📝 记事 | 四象限记事本(AI 建议象限/打卡),对话"帮我记一下"自动入本 |
| 🗂 记录 | 历史任务、双通道知识库检索、🧠数据洞察(大脑地图/每周反思/人物卡片) |
| 📰 外刊 | 今日外刊(全网公开英文新闻+AI中文导读)+ 外刊源导航 |

## 技术栈

- **后端**: Python 3.12+ / FastAPI / sqlite3(FTS5)
- **AI**: DeepSeek(意图/建议/批量生成,强制 JSON+容错解析)、知乎开放平台(zhihu-cli 0.6.3:搜索/全网搜索/直答)
- **识图**: RapidOCR + OpenCV QRCodeDetector
- **前端**: 原生 HTML/CSS/JS(无框架),单文件 HTML 报告 + MathJax
- **部署**: CloudBase 云托管(Dockerfile,Python 3.12-slim)

## 本地开发(Windows)

```powershell
# 1. 环境:Python 3.14 用 py 启动器;依赖
py -m pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
py -m pip install pdfplumber python-docx rapidocr_onnxruntime opencv-python numpy -i https://pypi.tuna.tsinghua.edu.cn/simple

# 2. 配置 .env(已 gitignore,不会上传)
#    DEEPSEEK_API_KEY=sk-xxx
#    ZHIHU_CLI=C:\Users\<你>\AppData\Local\ZhihuCLI\current\zhihu-cli.exe
#    另需环境变量 ZHIHU_ACCESS_SECRET(知乎开放平台 Access Secret,CLI 自动读取)

# 3. 启动
py -m uvicorn app.main:app --port 8000
# 打开 http://127.0.0.1:8000/ (健康检查 /api/v1/health)
```

> 知乎额度:搜索 5000/天、全网搜索 5000/天、直答 100/天(免费)。

## 测试

```powershell
py scripts/e2e_smoke.py                      # 本地 36 项端到端回归
py scripts/e2e_smoke.py https://公网地址     # 云端回归(云端无历史任务时自动先触发生成)
py scripts/boundary_smoke.py                 # 边界测试(空输入/超长/搜索无结果兜底)
py scripts/test_json_fix.py                  # LLM JSON 解析容错单测
```

## 目录结构

```
app/
├── main.py            # FastAPI 入口(挂载全部路由)
├── config.py          # 配置(.env + 环境变量)
├── models.py          # sqlite 数据层(表:documents/tasks/conversations/notes/feedbacks)
├── routers/           # ai(伴随问答/待办分析) generate(复习) history(历史/检索/报告)
│                      # life(参谋对话/规则解读/识图取链) more(外刊/数据洞察) notes upload
├── services/          # life(参谋核心) llm(双通道) zhihu(cli封装) linkx(识图取链)
│                      # news(外刊) insight(数据洞察) pipeline(复习管线) report(报告渲染)
│                      # highlight/cards/exam/plan/experience/parser/chunker/verify/material/profiles/mathtext
├── static/            # app.css(设计令牌体系) app.js
├── templates/         # index.html(五tab主页) life.html(旧独立参谋页,非主入口)
data/                  # finalmate.db(运行生成,已gitignore) + samples(样例课件)
scripts/               # e2e/边界测试/部署脚本/数据修复工具
Dockerfile             # 云端镜像(python:3.12-slim + zhihu-cli linux版 + 腾讯云pypi镜像)
requirements-cloud.txt # 云端依赖清单
```

## 部署(CloudBase)

- 环境:`near-rattlesnake-d3evklx68a01eb0`(体验版,ap-shanghai,3000 资源点/月)
- 需要 `npm i -g @cloudbase/cli` + `tcb login`(需环境权限)
- 部署命令(在项目根目录):

```powershell
"" | tcb cloudrun deploy -e near-rattlesnake-d3evklx68a01eb0 -s finalmate --source "D:/claude code projects/final-mate" --port 8000 --min-num 0 --max-num 2 --force --wait
```

- 密钥走**控制台环境变量**(不要写进命令行):DEEPSEEK_API_KEY、ZHIHU_ACCESS_SECRET
- 体验版 min-num=0 会休眠,访问时冷启动 10~30 秒,演示前先"暖机"
- 踩坑:控制台向导的「构建目录」必须为 `.`(曾误填 Dockerfile 导致构建失败);ps5.1 传含引号参数会搅乱命令行,别带 --env-params

## 协作流程

1. clone 本仓库 → 按「本地开发」跑通
2. 改动 → 本地 `py scripts/e2e_smoke.py` 回归 → 提交 PR
3. 需要上线验证时告知仓库 owner 部署(或由 owner 给 CloudBase 权限)

## 红线(比赛 FAQ 明确禁止)

- ❌ 收集/搬运真实真题(用 AI 按风格生成模拟卷)
- ❌ 爬虫抓取美团/点评(只用官方开放 API 的公开搜索)
- ❌ 编造来源(每条建议/坑必须来自检索结果,链接原样保留)
- ❌ 搬运受版权保护的教材/外刊内容(只做来源导航)
