# 来源配置

## 支持的平台

| 来源 | 优先级 | 稳定性 | 说明 |
|------|--------|--------|------|
| offershow | 1 | 中 | OfferShow，校招/实习信息，知名企业内推，城市字段需从公司名提取 |
| shixiseng | 2 | 高 | 实习僧，主招实习生，需验证公司规模，城市提取正常 |
| niukewang | 3 | 高 | 牛客网，校招+实习信息，需登录 Cookie |
| xiaohongshu | 4 | 低 | 小红书，WebSearch 验证，需大厂认证 |

## 平台差异 — 城市字段处理

- **shixiseng / niukewang**：平台直接提供 city 字段，过滤精准
- **offershow**：城市需从公司名中提取（如"深圳市xxx" → "深圳"），若提取失败为空，过滤时空 city 会被保留

```python
SOURCES_WITHOUT_CITY = {"offershow", "xiaohongshu"}
```

---

## 实习僧 (shixiseng)

**页面类型**：SPA（JavaScript 动态渲染）

**必需工具**：Playwright

**DOM 选择器**：
```javascript
items: document.querySelectorAll('.intern-wrap.interns-point.intern-item')

title:  item.querySelector('.intern-detail__job .title')
        // 优先 title 属性，其次 innerText（需清理 icon font 乱码）
company: item.querySelector('.intern-detail__company .title')
link:   item.querySelector('a.title')
```

**城市提取**：从文本行匹配 `城市 |` 格式，用已知城市列表验证

**薪资提取**：查找包含 `/天` 或 `面议` 的行

**登录状态**：无需登录

**Cookie 路径**：无

---

## 牛客网 (niukewang)

**页面类型**：SPA

**必需工具**：Playwright

**DOM 选择器**（依次尝试）：
```javascript
selectors: [
    '.job-list .job-item',
    '.job-item',
    '[class*="job-item"]',
    '[class*="job-card"]',
    '.recruit-list .recruit-item',
    '[class*="recruit-item"]'
]
```

**城市提取**：整行匹配已知城市名（精确匹配）

**公司名提取**：行中包含公司关键词（有限、集团、科技、公司、银行、基金等）

**薪资提取**：包含 `/天`、`/月`、`k` 的行

**登录状态**：需要（Cookie 保存于 /tmp/nowcoder_cookies.json）

---

## OfferShow (offershow)

**页面类型**：SPA

**必需工具**：Playwright

**城市提取**：从公司名字段前缀匹配已知城市（精确匹配）

**薪资提取**：同实习僧

**登录状态**：无需登录

---

## 小红书 (xiaohongshu)

**页面类型**：WebSearch（搜索引擎验证）

**必需工具**：无需 Playwright，使用 WebSearch 验证公司真实性

**城市字段**：不提供，视为 SOURCES_WITHOUT_CITY

---

## 添加新来源

1. 在 skill.json `sources` 数组中添加配置
2. 在 scraper.py 中实现对应的 Parser 类，继承 `BaseParser`
3. 在 `JobScraper.parsers` 字典中注册
4. 实现 `parse(page)` 和 `validate(job)` 两个方法

```python
class NewParser(BaseParser):
    def __init__(self):
        super().__init__("newplatform")

    def parse(self, page) -> List[JobListing]:
        # 解析逻辑
        pass

    def validate(self, job: JobListing) -> bool:
        # 验证逻辑（可用父类默认验证）
        return super().validate(job)
```

---
详细内容见 scraper.py 源码
