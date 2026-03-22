# job-scraper

多源招聘信息爬虫 - 从 OfferShow、实习僧、牛客网 等平台抓取真实招聘信息

## 功能特性

- 支持多个招聘平台（OfferShow、实习僧、牛客网）
- 自动过滤虚假招聘（押金、培训费等诈骗关键词）
- 自动去重（公司 + 职位 + 城市）
- 支持 JSON/CSV 格式导出
- **公司规模过滤**（优先大厂，500+ 人公司）

## 安装依赖

```bash
pip install playwright
playwright install chromium
```

## 使用方法

### 命令行

```bash
# 抓取所有来源
python3 scraper.py

# 抓取单个来源
python3 scraper.py --sources offershow
python3 scraper.py --sources shixiseng

# 导出 CSV
python3 scraper.py --format csv --output jobs.csv
```

### OpenClaw

```
claw run job-scraper.scrape
```

## 触发条件

当用户询问以下内容时自动激活：

- "帮我抓取招聘信息"
- "爬取招聘网站"
- "最新的实习信息"
- "校招信息有哪些"
- "有哪些公司在招人"
- "帮我找实习"
- ...

## 输出格式

```json
{
  "source": "shixiseng",
  "company": "字节跳动",
  "title": "后端研发实习生",
  "city": "北京",
  "salary": "400-600/天",
  "url": "https://..."
}
```

## 支持平台

| 平台 | 状态 | 说明 |
|------|------|------|
| OfferShow | ✅ 已完成 | SPA，需要 Playwright |
| 实习僧 | ✅ 已完成 | SPA，需要 Playwright |
| 牛客网 | ✅ 已完成 | SPA，需要 Playwright |

## 过滤规则

- 排除关键词：中介、代理、押金、培训费、贷款、传销
- 日薪低于 50 元视为可疑
- 按公司+职位+城市去重
- **优先大规模公司**（500+ 人）

## License

MIT
