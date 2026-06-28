# Job Application Assistant

秋招 **AI 产品岗**投递助手：JD 驱动改简历、生成 Boss 招呼语与邮箱话术，数据本地存储。

> **不是海投工具，是过滤器。** 匹配度低于 60 时系统会建议 skip——你的时间比盲目定制更值钱。  
> **AI 评估，人做决定。** 本工具只生成文案，不会在 Boss 或邮箱自动发送；请核对后再粘贴。

## What is this

面向国内秋招 AI 产品岗（产品经理 / 产品运营）的**本地 Web 助手**：录入 JD → 匹配分析 → 可选微调 → 生成 Boss 招呼语或邮件正文 → 人工复制到 Boss / 邮箱客户端。

第一次生成效果可能一般——请先录入足够的经历素材与简历，必要时添加根目录 `voice-dna.md` 约束文风（见 [examples/voice-dna.example.md](./examples/voice-dna.example.md)）。

## 功能

| 模块 | 说明 |
|------|------|
| 经历素材库 | 沉淀实习 / 项目经历，按标签检索 |
| 多版本简历 | Markdown 简历，支持默认版本 |
| 岗位库 | 录入 JD，跟踪 Boss / 邮箱投递状态 |
| AI 工作台 | 结构化匹配（A–F 六块）、微调、Boss / 邮箱、**一键流水线** |
| 生成审计 | `data/generations.json` + `reports/` Markdown 报告 |

详细需求见 [docs/PRD.md](./docs/PRD.md)。架构与数据边界见 [docs/ARCHITECTURE.md](./docs/ARCHITECTURE.md)、[docs/DATA_CONTRACT.md](./docs/DATA_CONTRACT.md)。

## How it works

```
粘贴 JD + 选择简历
        │
        ▼
   匹配度分析（A–F 六块 + 0–100 分）
        │
        ├─ score < 60  → recommendation: skip
        ├─ 60–74       → consider
        └─ ≥ 75        → apply
        │
        ▼
   可选：简历微调建议
        │
        ▼
   Boss 招呼语 / 邮箱话术
        │
        ▼
   人工复制 → Boss / 邮箱 → 更新岗位状态
```

## 技术栈

- **前端**：HTML + CSS + 原生 JS
- **后端**：Python 3.11+ / FastAPI
- **AI**：DeepSeek API（Prompt 规格在 `templates/prompts/`）
- **存储**：`data/` JSON + `reports/` Markdown

## 目录结构

```
job-application-assistant/
├── docs/PRD.md, ARCHITECTURE.md, DATA_CONTRACT.md
├── config/profile.example.yml
├── templates/states.yml, prompts/
├── data/          # 本地数据（gitignore）
├── reports/       # AI 报告（gitignore）
├── jds/ output/   # JD 存档 / 导出（gitignore）
├── examples/      # 样例 JD、简历
└── src/backend, frontend
```

## 快速开始

### 1. 环境准备

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt
```

### 2. 环境自检（doctor）

```bash
python -m src.backend.doctor
```

或启动服务后访问 <http://127.0.0.1:8000/api/doctor>。

### 3. 配置 API Key

```bash
cp .env.example .env
# 编辑 DEEPSEEK_API_KEY
```

或在应用 **设置** 页写入（保存至 `data/settings.json`）。

可选：复制 `config/profile.example.yml` → `config/profile.yml` 填写画像。

### 4. 启动

```bash
python -m src.backend.main
```

浏览器访问 <http://127.0.0.1:8000>。

### 5. 推荐工作流

1. **设置** → DeepSeek API Key  
2. **经历素材** → STAR 描述  
3. **简历** → 至少一版 Markdown（可参考 `examples/sample-resume.md`）  
4. **岗位库** → 粘贴 JD，标记 Boss / 邮箱  
5. **AI 工作台** → **一键流水线** 或分步生成 → 复制发送 → 更新岗位状态  

## 匹配度阈值

| 分数 | recommendation | 含义 |
|------|----------------|------|
| ≥ 75 | apply | 值得定制投递 |
| 60–74 | consider | 可权衡 |
| < 60 | skip | 不建议深度定制 |

阈值定义于 [templates/states.yml](./templates/states.yml)。

## 本地数据

| 文件 | 内容 |
|------|------|
| `data/experiences.json` | 经历素材 |
| `data/resumes.json` | 简历版本 |
| `data/jobs.json` | 岗位库 |
| `data/generations.json` | AI 生成历史 |
| `data/settings.json` | API Key 等 |

## Disclaimer

1. **数据在本地**：简历、JD、Key 存于本机 `data/`，不会提交 Git；调用 DeepSeek 时会发送 JD 与简历相关内容。  
2. **AI 可能出错**：生成内容可能幻觉或夸大，**发送前务必人工核对**；禁止虚构经历。  
3. **不自动投递**：本工具不会代你在 Boss 或邮箱发送消息。  
4. **合规使用**：请遵守 Boss 直聘、目标企业邮箱等平台的使用规范，勿 spam。

## 开发路线

- [x] M0：项目初始化
- [x] M1：文档契约、Prompt 外置、Auto-Pipeline、doctor
- [ ] M2：CRUD 编辑体验、岗位 dedup
- [ ] M3：voice-dna 优化、PDF 导出
- [ ] M4：状态流转 UI、筛选排序

## License

Private — 个人秋招使用
