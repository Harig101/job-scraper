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
    """实习僧解析器"""

    def __init__(self):
        super().__init__("shixiseng")

    def parse(self, html: str) -> List[JobListing]:
        jobs = []

        # 实习僧的职位数据在页面 JSON 中或通过 API 加载
        # 这里用正则匹配关键信息
        job_blocks = re.findall(
            r'<div[^>]*class="[^"]*job[^"]*"[^>]*>(.*?)</div>',
            html, re.DOTALL | re.IGNORECASE
        )

        for block in job_blocks:
            try:
                company = re.search(r'company[^>]*>([^<]+)', block)
                title = re.search(r'<h3[^>]*>([^<]+)', block)
                city = re.search(r'city[^>]*>([^<]+)', block)
                salary = re.search(r'salary[^>]*>([^<]+)', block)
                time_elem = re.search(r'time[^>]*>([^<]+)', block)

                if company and title:
                    job = JobListing(
                        source=self.name,
                        company=company.group(1).strip(),
                        title=title.group(1).strip(),
                        city=city.group(1).strip() if city else "",
                        salary=salary.group(1).strip() if salary else None,
                        posted_time=time_elem.group(1).strip() if time_elem else None
                    )
                    job.salary_min, job.salary_max = self.normalize_salary(job.salary or "")
                    jobs.append(job)
            except Exception:
                continue

        return jobs

    def validate(self, job: JobListing) -> bool:
        if self.check_excluded_keywords(job.title + job.company):
            return False
        if job.salary_min and job.salary_min < 50:  # 日薪低于50可能不真实
            return False
        return True


class NiuKeWangParser(BaseParser):
    """牛客网解析器"""

    def __init__(self):
        super().__init__("niukewang")

    def parse(self, html: str) -> List[JobListing]:
        jobs = []

        # 牛客网职位列表结构
        job_items = re.findall(
            r'<a[^>]*class="[^"]*job[^"]*"[^>]*>(.*?)</a>',
            html, re.DOTALL | re.IGNORECASE
        )

        for item in job_items:
            try:
                company = re.search(r'company[^>]*>([^<]+)', item)
                title = re.search(r'<h[34][^>]*>([^<]+)', item)
                city = re.search(r'location[^>]*>([^<]+)', item)
                salary = re.search(r'salary[^>]*>([^<]+)', item)

                if company and title:
                    job = JobListing(
                        source=self.name,
                        company=company.group(1).strip(),
                        title=title.group(1).strip(),
                        city=city.group(1).strip() if city else "",
                        salary=salary.group(1).strip() if salary else None
                    )
                    job.salary_min, job.salary_max = self.normalize_salary(job.salary or "")
                    jobs.append(job)
            except Exception:
                continue

        return jobs

    def validate(self, job: JobListing) -> bool:
        if self.check_excluded_keywords(job.title + job.company):
            return False
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

        if use_playwright or source_name == "offershow":
            try:
                from playwright.sync_api import sync_playwright

                with sync_playwright() as p:
                    browser = p.chromium.launch(headless=True)
                    page = browser.new_page(viewport={"width": 1280, "height": 900})
                    page.goto(url, wait_until="networkidle", timeout=90000)
                    page.wait_for_timeout(5000)

                    # For OfferShow, pass page to parser while browser is still open
                    if source_name == "offershow":
                        jobs = parser.parse(page)
                    else:
                        html = page.content()

                    browser.close()
            except ImportError:
                print("⚠️ Playwright 未安装，使用 HTTP 请求")
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

            use_playwright = source["name"] == "offershow"
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
