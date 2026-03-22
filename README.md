# job-scraper

多源招聘信息爬虫 - 从 OfferShow、实习僧、牛客网 等平台抓取真实招聘信息

## 功能特性

- 支持多个招聘平台（OfferShow、实习僧、牛客网）
- 自动过滤虚假招聘（押金、培训费等诈骗关键词）
- 自动去重（公司 + 职位 + 城市）
- 支持 JSON/CSV 格式导出

## 安装依赖

```bash
pip install playwright
playwright install chromium
```

## 使用方法

### 命令行

```bash
# 抓取 OfferShow（推荐，稳定）
python3 scraper.py --sources offershow

# 抓取所有来源
python3 scraper.py

# 导出 CSV
python3 scraper.py --format csv --output jobs.csv
```

### OpenClaw

```json
{
  "name": "job-scraper",
  "commands": {
    "scrape": "python3 {{skill_path}}/scraper.py --sources offershow"
  }
}
```

## 输出格式

```json
{
  "source": "offershow",
  "company": "华为云软件研发",
  "title": "华为云软件研发27届实习生招聘",
  "city": "",
  "salary": null,
  "salary_min": null,
  "salary_max": null,
  "job_type": "",
  "deadline": null,
  "requirements": "",
  "url": "",
  "posted_time": "2026-03-19",
  "hash_id": "a51da5d28552"
}
```

## 支持平台

| 平台 | 状态 | 说明 |
|------|------|------|
| OfferShow | ✅ 已完成 | SPA 站点，需要 Playwright 渲染 |
| 实习僧 | 🔧 开发中 | HTTP 抓取，需调试解析规则 |
| 牛客网 | 🔧 开发中 | HTTP 抓取，需调试解析规则 |

## 过滤规则

- 排除关键词：中介、代理、押金、培训费、贷款、传销
- 日薪低于 50 元视为可疑
- 按公司+职位+城市去重

## License

MIT
