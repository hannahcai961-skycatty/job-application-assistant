"""One-off: import experiences from 项目简历.pptx structured data."""
import json
from datetime import datetime
from pathlib import Path
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
now = datetime.now().isoformat()

experiences = [
    {
        "id": str(uuid4()),
        "title": "恒聚愿景 · 产品实习生 · 车载语音小模型评测",
        "category": "internship",
        "tags": ["LLM", "Dify", "车载语音", "评测框架", "AI产品"],
        "content": "2026年1月至今，北京恒聚愿景科技有限公司。主导车载语音助手小模型 baseline 测试框架搭建，在 Dify 实现自动化多轮测试，为核心目标筛选/验证 7B 级小模型在真实车载多轮对话场景下的表现。",
        "bullets": [
            "独立设计 9 大类车载实体池（参考 COVESA VSS、Tesla Fleet API），人工 100 条 + LLM 扩展至 500 条，支持 10–60 实体梯度压测",
            "制定三大维度量化指标与淘汰基线：上下文≥7轮、噪声≥15%、意图匹配率≥78%",
            "在 Dify Workflow 搭建 test_cases 迭代→实体注入→多轮记忆→JSON 解析→自动评估（意图匹配+槽位F1+实体准确率）全链路",
            "构建 100+ case 自动化框架，单次全流程 <3 分钟；量化 7 轮后意图匹配衰减至 35%，支撑模型选型",
            "产出 Markdown+JSON 结构化评估报告（四大维度衰减曲线），供团队后续模型迭代决策",
        ],
        "created_at": now,
        "updated_at": now,
    },
    {
        "id": str(uuid4()),
        "title": "境一科技 · 产品助理 · AI古法起名",
        "category": "internship",
        "tags": ["AI产品", "智能体", "数据基建", "运营", "0-1"],
        "content": "2025年8月–11月，北京境一科技。产品上线前及推广期，负责数据基建与运营支持：好名数据库、古代名人库结构化，以及小红书代运营团队 0-1 搭建。",
        "bullets": [
            "利用阿里云百炼构建「史学家」AI 智能体+史书知识库，一周内 batch 录入 12 万条历史名人数据，保障「好名参考」如期上线",
            "将原需数周的人工数据处理压缩至一周，提升效率与准确性",
            "独立搭建小红书代运营团队：薪酬调研、SOP、招聘 3 人，建立数据监控与周度复盘机制",
        ],
        "created_at": now,
        "updated_at": now,
    },
    {
        "id": str(uuid4()),
        "title": "产品项目 · 迎新百事通（功能+运营）",
        "category": "project",
        "tags": ["0-1", "用户调研", "PRD", "KANO", "小程序"],
        "content": "面向大学新生的「迎新百事通」小程序：从 0-1 功能设计到上线运营。203 份问卷+4 项竞品分析；运营阶段 30+ 访谈、200+ 问卷，KANO 确定八项核心需求。",
        "bullets": [
            "功能设计：迎新/地图/社交三大模块，流程图+交互原型+PRD；信息架构覆盖 14 校后台数据整合",
            "运营：USP+裂变促活、5 项 KPI（含 CTR/注册率）与 ROI；商家入驻条款与 BD 话术",
            "成功上线小程序并完成用户增长与商家入驻方案",
        ],
        "created_at": now,
        "updated_at": now,
    },
    {
        "id": str(uuid4()),
        "title": "产品项目 · 求职规划 AI 小程序",
        "category": "project",
        "tags": ["AI产品", "Prompt", "用户调研", "PRD", "文心一言"],
        "content": "从 0-1 设计大学生「求职规划」小程序：180 份问卷+用户访谈，三大功能求职规划/AI简历/求职日历。",
        "bullets": [
            "阿里云百炼调用文心一言，设计 Prompt 生成 AI 简历与求职日历内容",
            "产出流程图、交互原型与完整 PRD",
        ],
        "created_at": now,
        "updated_at": now,
    },
    {
        "id": str(uuid4()),
        "title": "福特优行创新营 · 越野搭子智能推荐（一等奖）",
        "category": "project",
        "tags": ["用户访谈", "原型", "BP", "竞品"],
        "content": "基于「纵横野」小程序，设计「野迹」智能匹配越野搭子系统。7 位越野小白访谈，三大功能：路线同步导航/搭子匹配/菜鸟老炮交流区。",
        "bullets": [
            "用户访谈明确「找不到搭子、活动信息模糊、缺少归属感」等痛点",
            "制作原型并在目标用户中二次迭代，产出 BP 展演获福特优行创新营一等奖",
        ],
        "created_at": now,
        "updated_at": now,
    },
    {
        "id": str(uuid4()),
        "title": "猿点科技 · 项目助理 · 元宇宙品牌",
        "category": "internship",
        "tags": ["项目运营", "招商", "直播"],
        "content": "2024年9月–11月，猿点科技（猿宇宙/元宇宙地标）。协助项目负责人客户信息整理、进度跟进与活动运营。",
        "bullets": [
            "贵州大地标招商讲解与客户维系；村超期间公众号内容与直播主持",
            "单场直播自然流量近 400 人，招募 2 家合作意向商",
        ],
        "created_at": now,
        "updated_at": now,
    },
    {
        "id": str(uuid4()),
        "title": "海百川科技 · 总经理助理 · 具身机器人",
        "category": "internship",
        "tags": ["项目管理", "展会", "机器人"],
        "content": "2025年1月–4月，海百川科技（具身机器人）。项目管理、早会汇报、人形机器人展会筹备。",
        "bullets": [
            "每日早会协调 15 名实习生任务进度，输出管理层决策依据",
            "展会教程编写与品宣，现场获 5 家潜在客户咨询",
        ],
        "created_at": now,
        "updated_at": now,
    },
    {
        "id": str(uuid4()),
        "title": "SODA 开放数据创新应用大赛 · 河道洄淤监测",
        "category": "competition",
        "tags": ["数据分析", "小程序", "UI设计"],
        "content": "2023年5月–12月，基于 GLDAS+激光雨滴谱仪构建河道洄淤模型并开发监测小程序，全国百强。",
        "bullets": [
            "需求分析：淤堵可视化提升清淤效率",
            "构建核心算法并完成 UI 设计",
        ],
        "created_at": now,
        "updated_at": now,
    },
    {
        "id": str(uuid4()),
        "title": "国信合创 CHA · 校园大使",
        "category": "other",
        "tags": ["活动组织", "AI孵化"],
        "content": "参与 CHA 人工智能共创理事会校园合伙人计划：指标制定、活动发起、评审组长。",
        "bullets": [
            "发起并参与企业参访；制定校园大使筛选标准与评审流程",
        ],
        "created_at": now,
        "updated_at": now,
    },
]

exp_ids = [e["id"] for e in experiences[:5]]

resume_content = """# 蔡浩蕾

- 手机：15118204386 | 邮箱：hannahcai961@gmail.com
- 北京语言大学 · 法语 · 本科 · GPA 3.5/4 · 2023.09–2027.06
- 求职目标：AI 产品实习生 / 产品实习生

## 教育背景

北京语言大学 法语专业本科。自学产品集训营、Python 训练营、运营实训。

## 实习经历

### 北京恒聚愿景科技有限公司 | 产品实习生 | 2026.01–至今

- 主导车载语音小模型 baseline 测试框架：Dify 自动化多轮测试，500 条实体池，100+ case，单次执行 <3min
- 制定上下文/噪声/意图匹配量化基线，产出结构化评估报告支撑 7B 模型选型

### 北京境一科技有限公司 | 产品助理 | 2025.08–2025.11

- 百炼 AI 智能体 batch 处理 12 万条历史名人数据，保障起名产品按期上线
- 0-1 搭建小红书代运营团队（3 人）与 SOP、周度复盘体系

### 猿点科技 | 项目助理 | 2024.09–2024.11

- 元宇宙项目客户跟进、招商与直播运营；单场直播自然流量近 400

## 项目经历

### 迎新百事通 / 求职规划 AI 小程序 | 产品负责人

- 203/180 份问卷+竞品分析，0-1 产出 PRD、原型；求职规划含 Prompt+文心一言 AI 生成模块
- 迎新百事通：KANO 分析、14 校信息架构、增长与商家入驻方案，成功上线

### 福特优行创新营 · 越野搭子 | 一等奖

- 7 用户访谈→原型→二次迭代→BP 展演

## 技能

Python（基础）、Prompt/Dify、Pixso/墨刀、问卷与用户调研、Office/剪映/Pr

## 其他

SODA 数据创新大赛全国百强 | CET-4 | CHA 校园大使 | 社团运营
"""

resume = {
    "id": str(uuid4()),
    "name": "ai-pm-default",
    "description": "从项目简历.pptx 整理的 AI 产品岗默认版",
    "content": resume_content,
    "experience_ids": exp_ids,
    "is_default": True,
    "created_at": now,
    "updated_at": now,
}

if __name__ == "__main__":
    DATA.mkdir(exist_ok=True)
    (DATA / "experiences.json").write_text(
        json.dumps({"items": experiences}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (DATA / "resumes.json").write_text(
        json.dumps({"items": [resume]}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    if not (DATA / "jobs.json").exists():
        (DATA / "jobs.json").write_text(
            json.dumps({"items": []}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    print(f"Imported {len(experiences)} experiences, 1 resume")
