# Architecture

## 系统概览

```
┌─────────────────────────────────────────────────────────┐
│                    Browser (SPA)                         │
│  仪表盘 · 经历 · 简历 · 岗位库 · AI 工作台 · 设置        │
└──────────────────────────┬──────────────────────────────┘
                           │ REST /api/*
┌──────────────────────────▼──────────────────────────────┐
│                  FastAPI (127.0.0.1)                     │
│  routers: experiences · resumes · jobs · ai · settings   │
└──────┬───────────────────────────────┬──────────────────┘
       │                               │
       ▼                               ▼
┌──────────────┐              ┌─────────────────┐
│ data/*.json  │              │  DeepSeek API    │
│ reports/     │              │  (deepseek-chat) │
│ jds/         │              └─────────────────┘
└──────────────┘
       ▲
       │ templates/prompts/*.md
       │ templates/states.yml
```

## 评估与生成流程

### 单步 AI 调用

1. 前端选择简历 + JD（或岗位库记录）
2. API 加载 `data/resumes.json`、`data/experiences.json`
3. 从 `templates/prompts/` 加载 Prompt，注入 JD、简历、经历要点
4. 可选注入 `voice-dna.md` 写作约束
5. 调用 DeepSeek，解析 JSON / 纯文本
6. 匹配分析附加 `recommendation`（apply / consider / skip）
7. 写入 `data/generations.json`；匹配/流水线另存 `reports/*.md`

### Auto-Pipeline（一键流水线）

```
选岗位 + 简历 + 渠道(boss|email)
        │
        ▼
   POST /api/ai/match
        │
        ├─ score < 60 → recommendation: skip（仍生成报告，提示不建议定制）
        │
        ├─ score >= 60 且 include_tune → POST tune-resume
        │
        ▼
   boss-greeting 或 email-draft
        │
        ▼
   generations.json + reports/{slug}-pipeline.md
```

## 数据流

| 输入 | 存储 | 输出 |
|------|------|------|
| JD 粘贴 | `data/jobs.json`、`jds/`（可选） | — |
| 经历 / 简历 | `data/experiences.json`、`data/resumes.json` | — |
| AI 匹配 | — | `reports/*-match.md`、`generations.json` |
| Boss / 邮箱 | — | 前端展示 + `output/`（未来导出） |

## API 端点

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/health` | 存活检查 |
| GET | `/api/doctor` | 环境自检 |
| GET | `/api/states` | 岗位状态机（来自 `templates/states.yml`） |
| CRUD | `/api/experiences`、`/api/resumes`、`/api/jobs` | 数据层 |
| POST | `/api/ai/match` | 结构化匹配评估 |
| POST | `/api/ai/tune-resume` | 简历微调建议 |
| POST | `/api/ai/boss-greeting` | Boss 招呼语 |
| POST | `/api/ai/email-draft` | 邮箱话术 |
| POST | `/api/ai/auto-pipeline` | 一键流水线 |
| GET/PUT | `/api/settings` | 本地设置 |

## 匹配度与推荐阈值

| 分数 | recommendation | 含义 |
|------|----------------|------|
| ≥ 75 | `apply` | 值得花时间定制投递 |
| 60–74 | `consider` | 可投，但需权衡 |
| < 60 | `skip` | 不建议花时间定制 |

阈值可在 `data/settings.json` 的 `match_thresholds` 覆盖（未来扩展）。

## Pipeline Integrity

| 能力 | 实现 |
|------|------|
| 环境自检 | `GET /api/doctor`、`python -m src.backend.doctor` |
| 生成审计 | `data/generations.json` |
| 报告存档 | `reports/` Markdown |
| 状态一致性 | `templates/states.yml` 为唯一真相源 |

## 隐私与安全

- 服务仅绑定 `127.0.0.1`
- API Key 存 `data/settings.json` 或 `.env`
- 日志不输出 Key 与完整简历
- JD / 简历片段会发送至 DeepSeek API

详见 [PRD.md](./PRD.md) 与 [DATA_CONTRACT.md](./DATA_CONTRACT.md)。
