# 输出格式与飞书同步

## JSON 输出格式

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
  "posted_timestamp": 1742515200,
  "hash_id": "a1b2c3d4e5f6",
  "requirements": "",
  "url": "https://..."
}
```

## 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| source | string | 来源平台名 |
| company | string | 公司名称（原始） |
| title | string | 职位名称（原始） |
| city | string | 城市（已标准化） |
| salary | string | 原始薪资字符串 |
| salary_min | int | 最低薪资（分），日薪×21 或 k×1000 |
| salary_max | int | 最高薪资（分） |
| job_type | string | 实习/校招/社招 |
| deadline | string | 截止日期（原始字符串） |
| posted_time | string | 发布时间（原始字符串） |
| posted_timestamp | int | 发布时间（Unix 秒），用于过滤 |
| hash_id | string | MD5 前12位，用于去重 |
| requirements | string | 岗位要求（若有） |
| url | string | 原始职位链接 |

## CSV 导出字段

```
source,company,title,city,salary,job_type,posted_time
```

## 飞书同步 (sync_feishu.py)

### 数据流向

```
scraper.py → jobs.json → sync_feishu.py → 飞书多维表格
```

### jobs_to_records 转换逻辑

```python
def jobs_to_records(jobs: List[dict]) -> List[dict]:
    for job in jobs:
        record = {
            "公司": job["company"],
            "职位": job["title"],
            "城市": job["city"],
            "薪资": job["salary"],
            "来源": job["source"],
            "类型": job.get("job_type", ""),
            "发布时间": timestamp_ms,  # Unix ms
            "链接": job.get("url", ""),
        }
        records.append(record)
    return records
```

### 时间戳处理（Fix 2）

```python
# 若 posted_timestamp 存在，用它
if job.get("posted_timestamp"):
    ts = job["posted_timestamp"] * 1000  # 秒 → 毫秒
    record_fields["发布时间"] = ts
else:
    # 时间解析失败时，用当天日期兜底（Fix 2 新增）
    record_fields["发布时间"] = int(datetime.now().timestamp() * 1000)
```

### 飞书多维表格字段

| 字段名 | 类型 | 说明 |
|--------|------|------|
| 公司 | 文本 | 公司名称 |
| 职位 | 文本 | 职位名称 |
| 城市 | 文本 | 城市 |
| 薪资 | 文本 | 原始薪资字符串 |
| 来源 | 文本 | 平台名 |
| 类型 | 文本 | 实习/校招/社招 |
| 发布时间 | 数字（时间戳） | Unix 毫秒 |
| 链接 | 超链接 | 原始职位 URL |

### 同步触发条件

- 手动运行：`claw run job-scraper.sync`（需配置飞书 API）
- 自动：爬虫完成后回调触发

---
飞书同步配置见 sync_feishu.py
