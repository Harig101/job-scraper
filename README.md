# job-scraper

多源招聘信息爬虫 - 从 OfferShow、实习僧、牛客网 等平台抓取真实招聘信息

## 功能特性

- 支持多个招聘平台（OfferShow、实习僧、牛客网、小红书）
- **城市过滤**：`job-{city}` 格式触发，自动筛选指定城市
- **公司规模过滤**：优先大厂（500+ 人公司）
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
# 抓取所有来源
python3 scraper.py

# 抓取指定城市（触发 job-{city} 模式）
python3 scraper.py --city 深圳
python3 scraper.py --city 上海
python3 scraper.py --city 北京

# 抓取单个来源
python3 scraper.py --sources offershow
python3 scraper.py --sources shixiseng

# 跳过公司规模验证（获取所有公司）
python3 scraper.py --no-verify-size

# 导出 CSV
python3 scraper.py --format csv --output jobs.csv
```

### OpenClaw

```
claw run job-scraper.scrape
claw run job-scraper.scrape-city --city 北京
```

## 触发条件

当用户询问以下内容时自动激活：

- "帮我抓取招聘信息"
- "爬取招聘网站"
- "最新的实习信息"
- "校招信息有哪些"
- "job-深圳"
- "job-上海"
- "offer多多多"
- ...

## 输出格式

```json
{
  "source": "shixiseng",
  "company": "字节跳动",
  "title": "后端研发实习生",
  "city": "深圳",
  "salary": "400-600/天",
  "url": "https://..."
}
```

## 支持平台

| 平台 | 状态 | 说明 |
|------|------|------|
| OfferShow | ✅ 已完成 | SPA，需要 Playwright，校招/实习 |
| 实习僧 | ✅ 已完成 | SPA，需要 Playwright，实习信息 |
| 牛客网 | ✅ 已完成 | SPA，需要 Playwright |
| 小红书 | ✅ 已完成 | WebSearch 验证，需大厂认证 |

## 过滤规则

- **城市过滤**：通过 `--city` 参数指定
- **公司规模**：500+ 人大厂（已知大厂名单）
- 排除关键词：中介、代理、押金、培训费、贷款、传销
- 日薪低于 50 元视为可疑
- 按公司+职位+城市去重

## License

MIT
