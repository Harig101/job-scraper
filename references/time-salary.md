# 时间解析与薪资标准化

## parse_posted_time() — 时间解析

输入任意时间字符串，返回 Unix timestamp（秒），用于时间过滤。

### 支持格式优先级

| 格式 | 示例 | 说明 |
|------|------|------|
| `%Y.%m.%d` | `2026.03.19` | 点分隔，最常见 |
| `%Y-%m-%d` | `2026-03-19` | 标准日期 |
| `%Y/%m/%d` | `2026/03/19` | 斜杠分隔 |
| `%Y年%m月%d日` | `2026年03月09日` | 中文格式 |
| 相对时间 | `3天前`、`1周前` | 相对当前时间计算 |

### 处理流程

```
1. 去除首尾空白
2. 去掉 "发布"、"前" 等后缀
3. 依次尝试日期格式解析
4. 若失败，尝试中文日期格式（Fix 1 新增）
5. 若失败，尝试 "N天前" / "N周前" 相对时间
6. 若都不匹配，返回 None（保留该职位）
```

### 注意事项

- `posted_timestamp = None` 的职位视为最新，默认保留
- 相对时间以**爬取时刻**为基准计算，结果具有时效性

---

## normalize_salary() — 薪资解析

输入薪资字符串，返回 `(min, max)` 数值（单位：分）。

### 支持格式

| 格式 | 示例 | 解析逻辑 |
|------|------|---------|
| `150-250/天` | 日薪区间 | min=150×21, max=250×21（转月薪） |
| `10k-20k/月` | 月薪区间 | min=10000, max=20000 |
| `15k-25k` | k后缀 | min=15000, max=25000 |
| `15k` | 单值 | min=max=15000 |
| `面议` | 不解析 | 返回 (None, None) |

### 薪资单位换算

- `/天` → × 21 → 月薪（分）
- `k` / `K` → × 1000（分）

### 返回值

- `(None, None)` — 无法解析（如"面议"）
- `(15000, 21000)` — 解析成功（单位：分）

---

## validate() — 职位质量验证

每个 Parser 有独立的 validate() 实现，但共享以下规则：

```python
def validate(job: JobListing) -> bool:
    # 1. 排除关键词检测
    if check_excluded_keywords(job.title + job.company):
        return False  # 命中任一关键词 → 过滤

    # 2. 薪资下限检测
    if job.salary_min and job.salary_min < 150:
        return False  # 日薪 < 150元 → 过滤

    # 3. 标题长度检测
    if len(job.title) < 3:
        return False  # 标题过短 → 过滤

    return True
```

### 排除关键词列表

```
中介、代理、押金、培训费、贷款、传销、先交钱
```

### 公司规模过滤（run() 层面）

```python
def is_large_company(company_name: str) -> bool:
    # 检查是否在 KNOWN_LARGE_COMPANIES 名单中
    for large in KNOWN_LARGE_COMPANIES:
        if large in company_name or company_name in large:
            return True
    return False
```

### 默认大厂名单说明

KNOWN_LARGE_COMPANIES 覆盖：
- 互联网/科技（字节、腾讯、阿里、百度等）
- 金融（银行、保险、证券）
- 外资（Google、Meta、Apple、Tesla 等）
- 快消/零售（宝洁、联合利华、欧莱雅等）
- 医疗健康（恒瑞、迈瑞等）
- 汽车（比亚迪、特斯拉、蔚来等）

---
详细内容见 scraper.py 源码
