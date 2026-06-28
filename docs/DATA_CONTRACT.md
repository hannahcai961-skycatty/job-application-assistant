# Data Contract

本文档定义 **User Layer**（用户数据，永不被代码更新覆盖）与 **System Layer**（系统逻辑，可随版本升级替换）的边界。

## User Layer（禁止自动覆盖）

| 路径 | 用途 |
|------|------|
| `data/experiences.json` | 经历素材库 |
| `data/resumes.json` | 多版本简历 |
| `data/jobs.json` | 岗位库与投递状态 |
| `data/generations.json` | AI 生成历史审计 |
| `data/settings.json` | DeepSeek API Key、默认简历等 |
| `config/profile.yml` | 候选人画像（从 `profile.example.yml` 复制） |
| `cv.md` | 主简历 Markdown（可选，与 JSON 简历并存） |
| `voice-dna.md` | 个人写作风格约束（可选） |
| `jds/*` | 按岗位存档的原始 JD |
| `reports/*` | 每次匹配/微调/流水线的 Markdown 报告 |
| `output/*` | 导出的招呼语、邮件正文等 |

## System Layer（可安全升级）

| 路径 | 用途 |
|------|------|
| `src/` | FastAPI 后端与前端静态资源 |
| `docs/` | PRD、架构、本契约 |
| `templates/states.yml` | 岗位状态机唯一真相源 |
| `templates/prompts/*.md` | AI Prompt 规格 |
| `config/profile.example.yml` | 画像配置模板 |
| `examples/` | 样例 JD、简历、生成结果 |
| `requirements.txt`、`.env.example` | 依赖与环境模板 |

## 规则

1. **User Layer 文件**：任何升级、拉代码、重装依赖时，不得读取后写回、删除或覆盖。
2. **System Layer 文件**：可随项目版本更新替换；用户自定义应放在 User Layer。
3. **敏感数据**：`data/`、`config/profile.yml`、`.env` 已列入 `.gitignore`，禁止提交至 Git。
4. **Prompt 迭代**：修改 AI 行为优先编辑 `templates/prompts/`，无需改 Python 业务代码。

## 备份建议

定期备份整个 `data/` 目录及 `config/profile.yml`、`cv.md`、`voice-dna.md`。
