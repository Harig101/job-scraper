# Job Scraper Skill (OpenClaw Compatible)

## 概述

多源招聘信息爬虫，从多个平台抓取真实招聘信息，过滤低质量条目。

## 快速使用

```bash
# 抓取所有来源
python3 scraper.py

# 多城市 + 职位类型 + 薪资过滤
python3 scraper.py --cities 深圳 上海 --job-type 实习 --salary-min 200
```

## 核心过滤规则

| 规则 | 说明 |
|------|------|
| 公司规模 | 500+ 人（已知大厂名单） |
| 薪资下限 | 日薪 ≥ 150 元 |
| 去重维度 | 公司 + 职位 + 城市 |
| 时间过滤 | 2026-03-01 之后 |

详细规则见 `references/filters.md`

## OpenClaw 调用

```bash
claw run job_scraper --sources shixiseng --format json
claw run job_scraper --cities 深圳 --job-type 实习
```

## 目录结构（渐进式披露）

```
job_scraper/
├── SKILL.md              ← Level 2：核心概念（本文档）
├── references/
│   ├── filters.md        ← Level 3：过滤链路与规则详解
│   ├── sources.md        ← Level 3：各平台解析逻辑与选择器
│   ├── output.md         ← Level 3：输出格式与飞书同步
│   └── time-salary.md    ← Level 3：时间解析与薪资标准化
├── examples/
│   └── run_examples.sh    ← 常用命令示例
└── scripts/
    └── validate.py        ← jobs.json 数据校验工具
```
