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

# ---------------------- 大厂名单（500+ 人公司） ----------------------

KNOWN_LARGE_COMPANIES = {
    # 互联网/科技
    "字节跳动", "腾讯", "阿里巴巴", "百度", "美团", "京东", "拼多多", "网易", "快手", "哔哩哔哩",
    "滴滴", "小米", "华为", "OPPO", "vivo", "中兴", "联想", "海尔", "美的", "格力",
    "京东科技", "蚂蚁集团", "阿里云", "腾讯云", "字节云",
    "商汤科技", "旷视科技", "依图科技", "云从科技",
    "大疆", "海康威视", "科大讯飞", "寒武纪", "地平线", "Momenta",
    "蔚来", "小鹏", "理想", "比亚迪", "宁德时代",
    "蚂蚁金服", "网商银行", "众安保险",
    "携程", "去哪儿", "飞猪", "马蜂窝",
    "小红书", "知乎", "豆瓣", "陌陌", "探探",
    "SHEIN", "安克创新", "致欧科技", "泽宝", "帕拓逊",
    "米哈游", "莉莉丝", "叠纸", "鹰角网络", "完美世界", "西山居", "37互娱",
    "腾讯音乐", "网易云音乐", "喜马拉雅", "荔枝", "蜻蜓FM",
    " Keep", "薄荷健康", "平安好医生", "丁香园", "微医",
    "顺丰", "中通", "韵达", "圆通", "申通", "极兔",
    # 金融
    "中国银行", "工商银行", "建设银行", "农业银行", "交通银行", "招商银行", "民生银行",
    "平安银行", "浦发银行", "广发银行", "兴业银行", "中信银行",
    "中国人寿", "中国平安", "太平洋保险", "新华保险", "泰康保险",
    "蚂蚁基金", "天天基金", "雪球", "富途", "老虎证券",
    # 外资
    "Google", "Meta", "Apple", "Amazon", "Microsoft", "Netflix", "Tesla",
    "Goldman Sachs", "Morgan Stanley", "JP Morgan", "Citi", "UBS", "Deutsche Bank",
    "Boeing", "Airbnb", "Uber", "Lyft", "Stripe", "Square", "Shopify",
    # 快消/零售
    "宝洁", "联合利华", "欧莱雅", "雅诗兰黛", "兰蔻", "资生堂", "可口可乐", "百事可乐",
    "雀巢", "玛氏", "亿滋", "卡夫", "达能", "蒙牛", "伊利", "光明",
    "优衣库", "Zara", "H&M", "Gap", "Nike", "Adidas", "Puma",
    "华润", "中粮", "中化", "中国石化", "中国石油",
    # 汽车
    "特斯拉", "蔚来汽车", "小鹏汽车", "理想汽车", "比亚迪", "吉利", "长城", "长安",
    "上汽", "广汽", "一汽", "东风", "北汽",
    # 医疗健康
    "恒瑞医药", "百济神州", "信达生物", "君实生物", "再鼎医药",
    "迈瑞医疗", "联影医疗", "鱼跃医疗", "九安医疗",
    "京东健康", "阿里健康", "平安好医生",
}

# 常见城市
SUPPORTED_CITIES = {"北京", "上海", "深圳", "广州", "杭州", "成都", "武汉", "南京", "苏州", "西安", "重庆", "天津", "长沙", "郑州", "东莞", "佛山", "厦门", "福州", "济南", "青岛", "大连", "沈阳", "哈尔滨", "长春", "昆明", "贵阳", "南宁", "石家庄", "太原", "合肥", "南昌"}


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
    """小红书解析器 - 通过 WebSearch 验证招聘线索

    小红书有 IP 风控无法直接爬取，此解析器用于从 WebSearch 结果中
    提取并验证小红书上提到的招聘线索。
    """

    def __init__(self):
        super().__init__("xiaohongshu")

    def parse(self, content: str) -> List[JobListing]:
        """从文本内容（WebSearch结果）中提取招聘线索"""
        jobs = []

        if not content:
            return jobs

        # 匹配模式：公司名 + 职位关键词
        # 例如："字节跳动招聘实习生" "华为内推"
        patterns = [
            r'([\u4e00-\u9fa5A-Za-z]{2,15})(?:公司)?(?:招聘|内推|直聘|实习|校招|春招|秋招)([\u4e00-\u9fa5A-Za-z]{2,20}?)(?:实习|生|工)?',
            r'(?:【)([\u4e00-\u9fa5A-Za-z]{2,10})(?:】)(.*?)(?:招聘|实习)',
        ]

        for pattern in patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                company = match[0].strip()
                title = match[1].strip() if len(match) > 1 else ""

                if company and title and len(title) > 2:
                    job = JobListing(
                        source=self.name,
                        company=company,
                        title=title,
                        city=""
                    )
                    jobs.append(job)

        return jobs

    def validate(self, job: JobListing) -> bool:
        if self.check_excluded_keywords(job.title + job.company):
            return False
        if len(job.title) < 3:
            return False
        # 小红书来源需要大厂验证
        if not self._is_large_company(job.company):
            return False
        return True

    def _is_large_company(self, company_name: str) -> bool:
        """检查是否为大规模公司"""
        if not company_name:
            return False
        for large in KNOWN_LARGE_COMPANIES:
            if large in company_name or company_name in large:
                return True
        return False


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
            "offershow": OfferShowParser(),
            "xiaohongshu": XiaohongshuParser()
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

    def run(self, sources: List[str] = None, city: str = None, verify_size: bool = True) -> List[JobListing]:
        """运行爬虫

        Args:
            sources: 指定来源列表
            city: 城市过滤（如 "深圳"、"上海"）
            verify_size: 是否验证公司规模
        """
        print("=" * 60)
        print("🚀 多源招聘信息爬虫启动")
        if city:
            print(f"📍 城市过滤: {city}")
        if verify_size:
            print("🏢 公司规模过滤: 500+ 人")
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

        # 城市过滤
        if city:
            city_filter = city.strip()
            unique_jobs = [j for j in unique_jobs if city_filter in j.city]
            print(f"\n🏙️ 城市过滤后: {len(unique_jobs)} 条")

        # 公司规模过滤
        if verify_size:
            size_before = len(unique_jobs)
            unique_jobs = [j for j in unique_jobs if self.is_large_company(j.company)]
            print(f"🏢 大厂过滤后: {len(unique_jobs)} 条 (过滤 {size_before - len(unique_jobs)} 条)")

        print(f"\n✅ 最终获取 {len(unique_jobs)} 条高质量职位")

        self.results = unique_jobs
        return unique_jobs

    def is_large_company(self, company_name: str) -> bool:
        """检查是否为大规模公司（500+ 人）"""
        if not company_name:
            return False

        # 检查是否在已知大厂名单中
        for large_company in KNOWN_LARGE_COMPANIES:
            if large_company in company_name or company_name in large_company:
                return True

        return False

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
    parser.add_argument("--city", type=str, help="城市过滤（如：深圳、上海、北京）")
    parser.add_argument("--no-verify-size", action="store_true", help="跳过公司规模验证")

    args = parser.parse_args()

    scraper = JobScraper(config_path=args.config)
    scraper.run(
        sources=args.sources,
        city=args.city,
        verify_size=not args.no_verify_size
    )
    scraper.export(format=args.format, filepath=args.output)
