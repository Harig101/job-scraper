#!/usr/bin/env python3
"""
多源招聘信息爬虫框架
支持：实习僧、牛客网、offershow.cn
"""

import json
import re
import time
import hashlib
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict
from abc import ABC, abstractmethod
import sys

# ---------------------- Data Models ----------------------

@dataclass
class JobListing:
    """招聘信息标准化数据结构"""
    source: str
    company: str
    title: str
    city: str
    salary: Optional[str] = None
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    job_type: str = ""  # 实习、校招、春招等
    deadline: Optional[str] = None
    requirements: str = ""
    url: str = ""
    posted_time: Optional[str] = None
    hash_id: str = ""  # 用于去重

    def __post_init__(self):
        if not self.hash_id:
            self.hash_id = hashlib.md5(
                f"{self.source}{self.company}{self.title}{self.city}".encode()
            ).hexdigest()[:12]

    def to_dict(self) -> dict:
        return asdict(self)


# ---------------------- Base Parser ----------------------

class BaseParser(ABC):
    """爬虫解析器基类"""

    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def parse(self, html: str) -> List[JobListing]:
        """解析 HTML/JSON 返回标准化职位列表"""
        pass

    @abstractmethod
    def validate(self, job: JobListing) -> bool:
        """验证职位是否符合质量标准"""
        pass

    def normalize_salary(self, salary_str: str) -> tuple:
        """解析薪资字符串，返回 (min, max) 数值"""
        if not salary_str:
            return None, None

        # 匹配各种薪资格式：150-250/天, 10k-20k/月, 15-25K*14薪
        patterns = [
            r'(\d+)-(\d+)[kK]/天',  # 150-250/天
            r'(\d+)-(\d+)[kK]/月',  # 10k-20k/月
            r'(\d+)[kK]-(\d+)[kK]',  # 15k-25k
            r'(\d+)[kK]',  # 15k (取估算值)
        ]

        for pattern in patterns:
            match = re.search(pattern, salary_str)
            if match:
                min_val = int(match.group(1))
                max_val = int(match.group(2))

                if '/天' in salary_str:
                    min_val *= 21  # 转换为月薪
                    max_val *= 21
                elif 'k' in salary_str.lower():
                    min_val *= 1000
                    max_val *= 1000

                return min_val, max_val

        return None, None

    def check_excluded_keywords(self, text: str) -> bool:
        """检查是否包含排除关键词"""
        exclude_words = ["中介", "代理", "押金", "培训费", "贷款", "传销", "先交钱"]
        text_lower = text.lower()
        return any(word in text for word in exclude_words)


# ---------------------- 具体 Parser 实现 ----------------------

class ShiXiShengParser(BaseParser):
    """实习僧解析器 - 使用Playwright动态渲染"""

    def __init__(self):
        super().__init__("shixiseng")

    def parse(self, page) -> List[JobListing]:
        """实习僧是SPA，需要Playwright渲染后提取"""
        jobs = []

        # 从页面提取结构化数据
        job_data = page.evaluate("""
            () => {
                const results = [];
                const items = document.querySelectorAll('.intern-wrap.interns-point.intern-item');

                items.forEach((item) => {
                    // 从DOM元素中提取数据
                    const titleEl = item.querySelector('.intern-detail__job .title');
                    const companyEl = item.querySelector('.intern-detail__company .title');
                    const cityEl = item.querySelector('.city');
                    const salaryEl = item.querySelector('.day');
                    const linkEl = item.querySelector('a.title');

                    const title = titleEl?.getAttribute('title') || titleEl?.innerText?.trim() || '';
                    const company = companyEl?.getAttribute('title') || companyEl?.innerText?.trim() || '';
                    const city = cityEl?.getAttribute('title') || cityEl?.innerText?.trim() || '';
                    const salary = salaryEl?.getAttribute('title') || salaryEl?.innerText?.trim() || '';
                    const link = linkEl?.href || '';

                    if (title) {
                        results.push({ title, company, city, salary, link });
                    }
                });

                return results;
            }
        """)

        for item in job_data:
            # 清理 icon font 产生的乱码
            title = self.clean_text(item.get('title', ''))
            company = self.clean_text(item.get('company', ''))
            city = self.clean_text(item.get('city', ''))
            salary = self.clean_text(item.get('salary', ''))

            if title:
                job = JobListing(
                    source=self.name,
                    company=company,
                    title=title,
                    city=city,
                    salary=salary if salary and '面议' not in salary else None,
                    url=item.get('link', '')
                )
                job.salary_min, job.salary_max = self.normalize_salary(salary)
                jobs.append(job)

        return jobs

    def clean_text(self, text: str) -> str:
        """清理 icon font 产生的乱码"""
        if not text:
            return ''
        import html
        # 先解码 HTML 实体
        text = html.unescape(text)
        # 移除 Private Use Area (icon fonts)
        text = re.sub(r'[\ue000-\uf8ff]', '', text)
        # 移除残留的 HTML 实体
        text = re.sub(r'&#[xX][0-9a-fA-F]+;', '', text)
        text = re.sub(r'&#[0-9]+;', '', text)
        # 移除多余空白
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    def validate(self, job: JobListing) -> bool:
        if self.check_excluded_keywords(job.title + job.company):
            return False
        if job.salary_min and job.salary_min < 50:
            return False
        if len(job.title) < 3:
            return False
        return True


class NiuKeWangParser(BaseParser):
    """牛客网解析器"""

    def __init__(self):
        super().__init__("niukewang")

    def parse(self, page) -> List[JobListing]:
        """牛客网职位列表页"""
        jobs = []

        job_data = page.evaluate("""
            () => {
                const results = [];

                // 尝试多种选择器
                const selectors = [
                    '.job-list .job-item',
                    '.job-item',
                    '[class*="job-item"]',
                    '[class*="job-card"]'
                ];

                let items = [];
                selectors.forEach(sel => {
                    items = items.concat(Array.from(document.querySelectorAll(sel)));
                });

                // 去重
                const seen = new Set();
                items = items.filter(item => {
                    if (seen.has(item)) return false;
                    seen.add(item);
                    return true;
                });

                items.forEach(item => {
                    const title = item.querySelector('h3, h4, .title, [class*="title"]')?.innerText?.trim() || '';
                    const company = item.querySelector('[class*="company"]')?.innerText?.trim() || '';
                    const city = item.querySelector('[class*="city"], [class*="location"]')?.innerText?.trim() || '';
                    const salary = item.querySelector('[class*="salary"]')?.innerText?.trim() || '';

                    if (title || company) {
                        results.push({ title, company, city, salary });
                    }
                });

                return results;
            }
        """)

        for item in job_data:
            if item.get('title'):
                job = JobListing(
                    source=self.name,
                    company=item.get('company', ''),
                    title=item.get('title', ''),
                    city=item.get('city', ''),
                    salary=item.get('salary') or None
                )
                job.salary_min, job.salary_max = self.normalize_salary(item.get('salary', ''))
                jobs.append(job)

        return jobs

    def validate(self, job: JobListing) -> bool:
        if self.check_excluded_keywords(job.title + job.company):
            return False
        return True


class XiaohongshuParser(BaseParser):
    """小红书解析器 - 从帖子提取招聘相关信息并通过WebSearch验证"""

    def __init__(self):
        super().__init__("xiaohongshu")

    def parse(self, page) -> List[JobListing]:
        """小红书是SPA，需要Playwright渲染"""
        jobs = []

        # 小红书页面结构
        job_data = page.evaluate("""
            () => {
                const results = [];

                // 查找笔记内容区域
                const content = document.querySelector('#detailPage') ||
                               document.querySelector('.note-detail') ||
                               document.querySelector('[class*="content"]');

                if (content) {
                    const text = content.innerText;
                    results.push({ content: text.substring(0, 5000) });
                }

                return results;
            }
        """)

        for item in job_data:
            content = item.get('content', '')
            # 从内容中提取可能的职位信息
            # 这需要后续的 web search 验证

        return jobs

    def validate(self, job: JobListing) -> bool:
        return True


class OfferShowParser(BaseParser):
    """OfferShow解析器 - 使用Playwright动态渲染"""

    def __init__(self):
        super().__init__("offershow")

    def parse(self, page) -> List[JobListing]:
        """OfferShow 是 SPA，需要 Playwright 渲染后提取"""
        jobs = []

        # 从页面提取文本内容并解析
        data = page.evaluate("""
            () => {
                const results = [];
                const body = document.body;
                const allText = body.innerText;

                // 按段落分割提取职位信息
                const paragraphs = allText.split('\\n\\n');

                paragraphs.forEach(p => {
                    const lines = p.split('\\n').filter(l => l.trim());
                    if (lines.length >= 2) {
                        const firstLine = lines[0].trim();

                        // 跳过导航、登录等无关内容
                        const skipWords = ['导航', '登录', '会员', 'OfferShow', '找名企', 'offer', '小程序', '加入', '求职'];
                        if (skipWords.some(w => firstLine.includes(w))) return;

                        // 匹配模式1: 公司名 + 职位描述 (中间有 | 分隔)
                        if (firstLine.includes('|')) {
                            const parts = firstLine.split('|').map(s => s.trim());
                            if (parts.length >= 2 && parts[0].length > 1) {
                                results.push({
                                    company: parts[0],
                                    title: parts[1],
                                    posted: lines.find(l => /\\d{4}\\.\\d{2}\\.\\d{2}/.test(l)) || ''
                                });
                            }
                        }
                        // 匹配模式2: 公司名 + 职位 (如 "华为云软件研发27届实习生招聘")
                        else if (firstLine.length > 6 && firstLine.length < 80) {
                            // 检查是否包含职位关键词
                            const jobKeywords = ['招聘', '实习', '校招', '春招', '秋招', '管培生', '培训生', '内推', '直聘'];
                            if (jobKeywords.some(k => firstLine.includes(k))) {
                                results.push({
                                    company: '',
                                    title: firstLine,
                                    posted: lines.find(l => /\\d{4}\\.\\d{2}\\.\\d{2}/.test(l)) || ''
                                });
                            }
                        }
                    }
                });

                return results;
            }
        """)

        for item in data:
            company = item.get('company', '').strip()
            title = item.get('title', '').strip()

            # 从职位标题中提取公司名（如果没有单独的公司名）
            if not company and title:
                # 尝试从标题中提取公司名 (通常在前面)
                company_match = re.match(r'^([A-Za-z\u4e00-\u9fa5]{2,10})', title)
                if company_match:
                    company = company_match.group(1)

            if title and len(title) > 4:
                job = JobListing(
                    source=self.name,
                    company=company,
                    title=title,
                    city="",
                    posted_time=item.get('posted', '').replace('.', '-') if item.get('posted') else None
                )
                jobs.append(job)

        return jobs

    def validate(self, job: JobListing) -> bool:
        if self.check_excluded_keywords(job.title + job.company):
            return False
        if len(job.title) < 6:
            return False
        # 排除明显不是招聘的内容
        if job.title in ['OfferShow小程序', '加入OfferShow求职精英交流群']:
            return False
        return True


# ---------------------- Scraper 主逻辑 ----------------------

class JobScraper:
    """多源爬虫调度器"""

    def __init__(self, config_path: str = "skill.json"):
        self.parsers = {
            "shixiseng": ShiXiShengParser(),
            "niukewang": NiuKeWangParser(),
            "offershow": OfferShowParser()
        }
        self.load_config(config_path)
        self.results: List[JobListing] = []

    def load_config(self, path: str):
        """加载配置文件"""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
        except FileNotFoundError:
            self.config = {"filters": {}}

    def fetch_url(self, url: str, headers: dict = None) -> Optional[str]:
        """HTTP 获取页面内容"""
        try:
            import urllib.request

            default_headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            }

            if headers:
                default_headers.update(headers)

            req = urllib.request.Request(url, headers=default_headers)
            with urllib.request.urlopen(req, timeout=30) as response:
                return response.read().decode('utf-8')
        except Exception as e:
            print(f"[{self}] Failed to fetch {url}: {e}")
            return None

    def scrape_source(self, source_config: dict, use_playwright: bool = False) -> List[JobListing]:
        """抓取单个来源"""
        source_name = source_config["name"]
        url = source_config["url"]

        print(f"\n📦 正在抓取: {source_config['display']} ({source_name})")

        html = None
        jobs = []

        parser = self.parsers.get(source_name)
        if not parser:
            print(f"❌ 未知来源: {source_name}")
            return []

        # SPA sources need Playwright
        spa_sources = ("offershow", "shixiseng", "niukewang")

        if use_playwright or source_name in spa_sources:
            try:
                from playwright.sync_api import sync_playwright

                with sync_playwright() as p:
                    browser = p.chromium.launch(headless=True)
                    page = browser.new_page(viewport={"width": 1280, "height": 900})

                    # Use domcontentloaded for sites that might timeout with networkidle
                    page.goto(url, wait_until="domcontentloaded", timeout=60000)
                    page.wait_for_timeout(8000)  # Wait for JS rendering

                    # SPA sources need page object, others use HTML
                    if source_name in spa_sources:
                        jobs = parser.parse(page)
                    else:
                        html = page.content()

                    browser.close()
            except ImportError as e:
                print(f"⚠️ Playwright 未安装: {e}")
                html = self.fetch_url(url)
            except Exception as e:
                print(f"⚠️ Playwright 错误: {e}")
                html = self.fetch_url(url)
        else:
            html = self.fetch_url(url)

        # Parse HTML-based sources
        if html and not jobs:
            jobs = parser.parse(html)

        if not jobs and not html:
            print(f"❌ 获取页面失败: {source_name}")
            return []

        print(f"   解析到 {len(jobs)} 条职位")

        # 过滤
        valid_jobs = [j for j in jobs if parser.validate(j)]
        print(f"   通过验证 {len(valid_jobs)} 条")

        return valid_jobs

    def run(self, sources: List[str] = None) -> List[JobListing]:
        """运行爬虫"""
        print("=" * 60)
        print("🚀 多源招聘信息爬虫启动")
        print("=" * 60)

        all_jobs = []

        for source in self.config.get("sources", []):
            if sources and source["name"] not in sources:
                continue

            use_playwright = source["name"] in ("offershow", "shixiseng", "niukewang")
            jobs = self.scrape_source(source, use_playwright=use_playwright)
            all_jobs.extend(jobs)

        # 去重
        seen = set()
        unique_jobs = []
        for job in all_jobs:
            if job.hash_id not in seen:
                seen.add(job.hash_id)
                unique_jobs.append(job)

        print(f"\n✅ 总计获取 {len(unique_jobs)} 条去重后职位")

        self.results = unique_jobs
        return unique_jobs

    def export(self, format: str = "json", filepath: str = None):
        """导出结果"""
        if not self.results:
            print("⚠️ 没有结果可导出")
            return

        if format == "json":
            output = json.dumps([j.to_dict() for j in self.results], ensure_ascii=False, indent=2)
        elif format == "csv":
            import csv
            import io
            output = io.StringIO()
            fieldnames = ["source", "company", "title", "city", "salary", "job_type", "posted_time"]
            writer = csv.DictWriter(output, fieldnames=fieldnames)
            writer.writeheader()
            for j in self.results:
                writer.writerow({k: getattr(j, k, "") for k in fieldnames})
            output = output.getvalue()
        else:
            output = str(self.results)

        if filepath:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(output)
            print(f"💾 已保存到: {filepath}")
        else:
            print(output)

        return output


# ---------------------- CLI 入口 ----------------------

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="多源招聘信息爬虫")
    parser.add_argument("--sources", nargs="+", help="指定来源 (shixiseng, niukewang, offershow)")
    parser.add_argument("--config", default="skill.json", help="配置文件路径")
    parser.add_argument("--output", default="jobs.json", help="输出文件")
    parser.add_argument("--format", default="json", choices=["json", "csv"], help="输出格式")

    args = parser.parse_args()

    scraper = JobScraper(config_path=args.config)
    scraper.run(sources=args.sources)
    scraper.export(format=args.format, filepath=args.output)
