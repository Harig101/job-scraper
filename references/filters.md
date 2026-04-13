# 过滤规则详解

## 过滤链路（按执行顺序）

```
所有职位
  ↓
1. validate() 初步过滤（Parser 级别）
  ↓
2. 去重（hash_id 去重）
  ↓
3. 城市过滤（--cities）
  ↓
4. 职位类型过滤（--job-type）
  ↓
5. 薪资下限过滤（--salary-min）
  ↓
6. 时间范围过滤（--posted-within-days）
  ↓
7. 公司规模过滤（500+ 人）
  ↓
8. POST_AFTER 时间过滤（全局默认，2026-03-01）
  ↓
最终结果
```

---

## 1. validate() 初步过滤（Parser 级别）

每个 Parser 独立验证：

```python
def validate(job: JobListing) -> bool:
    # 排除关键词（标题+公司名）
    if check_excluded_keywords(job.title + job.company):
        return False

    # 薪资下限：日薪 < 150元 → 过滤
    if job.salary_min and job.salary_min < 150:
        return False

    # 标题过短：< 3 字符 → 过滤
    if len(job.title) < 3:
        return False

    return True
```

---

## 2. 去重

**维度**：`source` + `company` + `title` + `city`

**hash_id 生成**：
```python
job.hash_id = md5(f"{source}{company}{title}{city}").hexdigest()[:12]
```

**同类职位保留第一条**（按遍历顺序）

---

## 3. 城市过滤

**多城市 OR 逻辑**：任意一个城市匹配即保留

```python
if cities:
    matched = [j for j in jobs if j.city and any(cf in j.city for cf in cities)]
    # offershow/xiaohongshu 城市为空时保留（视为未知）
    unknown_city = [j for j in jobs if not j.city and j.source in SOURCES_WITHOUT_CITY]
    jobs = matched + unknown_city
```

**已知问题**：offershow 城市提取依赖公司名，"深圳市xxx" 能提取，但"腾讯"无法判断城市。

---

## 4. 职位类型过滤

**支持三种类型**（模糊匹配）：

| 参数值 | 匹配关键词 |
|--------|-----------|
| `实习` | 实习 |
| `校招` | 校招、春招、秋招、应届、校园招聘 |
| `社招` | 社招、社会招聘、全职 |

**注意**：job_type 字段由各平台提供，若平台不填则无法过滤。

---

## 5. 薪资下限过滤

```python
if salary_min:
    jobs = [j for j in jobs if j.salary_min and j.salary_min >= salary_min]
```

**单位**：分（如 `--salary-min 200` 实际是 `200×21=4200` 分/天）

---

## 6. 时间范围过滤

```python
if posted_within_days:
    cutoff_ts = (now - timedelta(days=posted_within_days)).timestamp()
    jobs = [j for j in jobs if j.posted_timestamp is None or j.posted_timestamp >= cutoff_ts]
```

**特性**：`posted_timestamp = None` 的职位默认保留（视为最新）

---

## 7. 公司规模过滤

```python
def is_large_company(company_name: str) -> bool:
    for large in KNOWN_LARGE_COMPANIES:
        if large in company_name or company_name in large:
            return True
    return False
```

**匹配方式**：双向包含匹配（"字节跳动" in "字节跳动（北京）" → True）

**跳过方式**：`--no-verify-size`

---

## 8. POST_AFTER 时间过滤（全局）

```python
POST_AFTER = datetime(2026, 3, 1, 0, 0, 0)
post_after_ts = int(POST_AFTER.timestamp())

jobs = [j for j in jobs if j.posted_timestamp is None or j.posted_timestamp >= post_after_ts]
```

**特性**：无时间戳的职位默认保留（假设为最新）

---

## 过滤规则汇总表

| 过滤项 | 默认行为 | 控制参数 |
|--------|---------|---------|
| 排除关键词 | 命中即过滤 | 无（硬编码） |
| 薪资下限 | 日薪 < 150元过滤 | 无 |
| 标题长度 | < 3字符过滤 | 无 |
| 城市 | 不过滤 | `--cities` |
| 职位类型 | 不过滤 | `--job-type` |
| 薪资下限 | 不过滤 | `--salary-min` |
| 时间范围 | 保留所有 | `--posted-within-days` |
| 公司规模 | 只保留 500+ 人 | `--no-verify-size` |
| 发布时间 | 保留 2026-03-01 之后 | 无（硬编码） |

---
详细内容见 scraper.py 源码
