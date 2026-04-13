# job-scraper

多源招聘信息爬虫 v2.0.0 - 从 OfferShow、实习僧、牛客网 等平台抓取真实招聘信息

## 功能特性

- 支持多个招聘平台（OfferShow、实习僧、牛客网、小红书）
- **多城市过滤**：`--cities` 支持多城市 OR 匹配
- **职位类型过滤**：`--job-type` 支持实习/校招/社招
- **薪资下限过滤**：`--salary-min` 日薪过滤
- **时间范围过滤**：`--posted-within-days` 最近 N 天职位
- **公司规模过滤**：优先大厂（500+ 人公司）
- 自动过滤虚假招聘（押金、培训费等诈骗关键词）
- 自动去重（公司 + 职位 + 城市）
- 支持 JSON/CSV 格式导出

## 安装依赖

```bash
pip install playwright
playwright install chromium
```

## 命令行使用

```bash
# 基础抓取
python3 scraper.py

# 多城市过滤
python3 scraper.py --cities 深圳 上海 北京

# 职位类型 + 薪资过滤
python3 scraper.py --cities 深圳 --job-type 实习 --salary-min 150

# 最近 7 天内的职位
python3 scraper.py --cities 深圳 --posted-within-days 7

# 组合使用
python3 scraper.py --cities 深圳 上海 --job-type 实习 --salary-min 200 --posted-within-days 3

# 抓取单个来源
python3 scraper.py --sources offershow
python3 scraper.py --sources shixiseng

# 跳过公司规模验证
python3 scraper.py --no-verify-size

# 导出格式
python3 scraper.py --format json --output jobs.json
python3 scraper.py --format csv --output jobs.csv
```

## OpenClaw

```
claw run job-scraper.scrape
claw run job-scraper.scrape-city --cities 深圳
claw run job-scraper.scrape-city --cities 深圳 上海 --job-type 实习
```

## 过滤规则

| 过滤项 | 默认行为 | 参数 |
|--------|---------|------|
| 公司规模 | 只保留 500+ 人 | `--no-verify-size` 跳过 |
| 薪资下限 | 日薪 ≥ 150 元 | `--salary-min` |
| 去重 | 公司 + 职位 + 城市 | — |
| 时间过滤 | 2026-03-01 之后 | `--posted-within-days` |
| 城市 | 全部保留 | `--cities` |
| 职位类型 | 全部保留 | `--job-type` |
| 排除关键词 | 中介/代理/押金/培训费等 | 硬编码 |

## 支持平台

| 平台 | 状态 | 说明 |
|------|------|------|
| OfferShow | ✅ | SPA，需要 Playwright，城市从公司名提取 |
| 实习僧 | ✅ | SPA，需要 Playwright，城市字段正常 |
| 牛客网 | ✅ | SPA，需要 Playwright，需要登录 Cookie |
| 小红书 | ✅ | WebSearch 验证，需大厂认证 |

## 目录结构（渐进式披露）

```
job_scraper/
├── SKILL.md              ← Level 2：核心概念
├── references/
│   ├── filters.md        ← Level 3：过滤链路详解
│   ├── sources.md        ← Level 3：平台解析逻辑与选择器
│   ├── output.md         ← Level 3：输出格式与飞书同步
│   └── time-salary.md    ← Level 3：时间解析与薪资标准化
├── examples/
│   └── run_examples.sh    ← 常用命令示例
├── scripts/
│   └── validate.py        ← 数据校验工具
└── scraper.py             ← 主程序
```

## License

MIT
