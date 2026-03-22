# Job Scraper Skill (OpenClaw Compatible)

## 概述
多源招聘信息爬虫，从多个平台抓取真实招聘信息，过滤低质量条目。

## 使用方式
```
python3 scraper.py --sources shixiseng niukewang offershow --output jobs.json
```

## 来源配置

| 来源 | 优先级 | 稳定性 | 说明 |
|------|--------|--------|------|
| shixiseng | 1 | 高 | 实习僧，主招实习生 |
| niukewang | 2 | 高 | 牛客网，校招/实习 |
| offershow | 3 | 中 | OfferShow，需Playwright |

## 过滤规则

### 必排关键词
- 中介、代理、押金、培训费、贷款、传销、先交钱

### 薪资过滤
- 日薪低于 50 元视为可疑

### 去重维度
- 公司 + 职位名称 + 城市

## 输出格式
```json
{
  "source": "shixiseng",
  "company": "字节跳动",
  "title": "后端研发实习生",
  "city": "北京",
  "salary": "400-600/天",
  "salary_min": 8400,
  "salary_max": 12600,
  "job_type": "实习",
  "deadline": "2026-04-01",
  "posted_time": "2026-03-20",
  "hash_id": "a1b2c3d4e5f6"
}
```

## OpenClaw 调用示例
```
claw run job_scraper --sources shixiseng --format json
```
