# 期末搭子 FinalMate

知乎黑客松 S3・湾区共创季 | 赛道:AI × 知识与探索

上传课件/笔记,30 秒生成带知乎社区经验背书的期末复习方案(重点清单 + 抽认卡 + 模拟题 + 遗忘曲线复习计划)。

## 科目体系(两大科目族)

| 族 | 科目 | 驱动方式 | 核心功能 |
|---|---|---|---|
| 数学族 | 高中数学、高等数学 | 章节驱动:上传课件→划重点 | 重点清单 + 计算/证明题模拟 |
| 英语族 | 高中英语、四六级、雅思托福 | 技能驱动:词汇/语法/听力/阅读/写作分模块 | 单词/口语抽认卡 + 真题型模拟 |

输入物:数学族=课件 PDF;英语族=词汇表/真题/目标分数(可无课件直接生成)。
架构上科目族是配置项,新科目=加一行配置,不改管线与界面。

## 技术栈

- FastAPI + sqlite3
- LLM 双通道:知乎直答(划重点,有检索依据)/ DeepSeek(批量生成)
- zhihu-cli(经验检索:知乎搜索 5000 次/天)

## 当前进度

- [x] D1 项目骨架 + LLM 双通道封装(已实测通过)
- [ ] D2 文档解析(pdf/docx/txt)
- [ ] D3 OCR + 上传接口
- [ ] D4 AI 划重点管线
- [ ] D5 知乎经验检索增强
- [ ] D6 抽认卡 + 模拟题生成
- [ ] D7 复习计划(遗忘曲线)
- [ ] D8+ HTML 报告 / Web 界面 / 部署

## 运行

```powershell
cd D:\claude code projects\final-mate
py -m pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
py -m uvicorn app.main:app --reload
```

- 健康检查:http://127.0.0.1:8000/api/v1/health
- 通道调试:http://127.0.0.1:8000/api/v1/llm/test?channel=deepseek&q=你好
- 测试:py tests\test_llm.py

## 配置

`.env`(已 gitignore):DEEPSEEK_API_KEY、DEEPSEEK_BASE_URL、DEEPSEEK_MODEL、ZHIDA_MODEL、ZHIHU_CLI 路径

## 目录结构

```
app/
├── main.py            # FastAPI 入口
├── config.py          # 配置(.env)
└── services/
    ├── llm.py         # LLM 双通道统一接口
    └── zhihu.py       # zhihu-cli 封装
```
