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
    "Keep", "薄荷健康", "平安好医生", "丁香园", "微医",
    "顺丰", "中通", "韵达", "圆通", "申通", "极兔",
    "爱奇艺", "B站", "UC", "优酷", "土豆", "搜狐", "新浪", "凤凰网",
    "汽车之家", "易车", "懂车帝", "瓜子二手车", "人人车", "优信",
    "猎聘", "BOSS直聘", "拉勾网", "前程无忧", "智联招聘",
    "饿了么", "美团外卖", "大众点评", "口碑", "淘票票", "猫眼",
    "58同城", "赶集网", "百姓网", "安居客", "贝壳找房",
    "蜜芽", "孩子王", "宝宝树", "妈妈网",
    "大麦网", "永辉超市", "盒马", "叮咚买菜", "每日优鲜",
    # 金融
    "中国银行", "工商银行", "建设银行", "农业银行", "交通银行", "招商银行", "民生银行",
    "平安银行", "浦发银行", "广发银行", "兴业银行", "中信银行", "光大银行", "华夏银行",
    "中国人寿", "中国平安", "太平洋保险", "新华保险", "泰康保险", "人保财险", "大地保险",
    "蚂蚁基金", "天天基金", "雪球", "富途", "老虎证券", "同花顺", "东方财富",
    "中金公司", "中信建投", "国泰君安", "华泰证券", "招商证券", "海通证券", "广发证券",
    "中国石化", "中国石油", "中国建筑", "中国中铁", "中国铁建", "中国中车",
    # 外资
    "Google", "Meta", "Apple", "Amazon", "Microsoft", "Netflix", "Tesla",
    "Goldman Sachs", "Morgan Stanley", "JP Morgan", "Citi", "UBS", "Deutsche Bank", "HSBC",
    "Boeing", "Airbnb", "Uber", "Lyft", "Stripe", "Square", "Shopify", "PayPal",
    "Intel", "AMD", "Nvidia", "Qualcomm", "Broadcom", "Texas Instruments",
    "Samsung", "Sony", "LG", "Panasonic", "Hitachi",
    "Shell", "BP", "ExxonMobil", "Chevron",
    "Coca-Cola", "PepsiCo", "Nestle", "Unilever", "P&G", "L'Oréal", "Estée Lauder",
    "BMW", "Mercedes-Benz", "Audi", "Volkswagen", "Toyota", "Honda", "Ford", "GM",
    "McDonald's", "KFC", "Pizza Hut", "Starbucks", "Costa Coffee",
    "IKEA", "H&M", "Zara", "Gap", "Nike", "Adidas", "Uniqlo",
    "Pfizer", "Johnson & Johnson", "Merck", "Roche", "Novartis", "Sanofi", "Bayer",
    # 快消/零售
    "宝洁", "联合利华", "欧莱雅", "雅诗兰黛", "兰蔻", "资生堂", "SK-II", "Olay",
    "可口可乐", "百事可乐", "农夫山泉", "怡口", "娃哈哈", "蒙牛", "伊利", "光明", "飞鹤",
    "雀巢", "玛氏", "亿滋", "卡夫", "达能", "养元", "王老吉", "加多宝",
    "茅台", "五粮液", "洋河", "泸州老窖", "汾酒", "古井贡酒",
    "华润", "中粮", "中化", "中储粮", "中糖",
    "永辉超市", "大润发", "华润万家", "家乐福", "沃尔玛", "麦德龙", "山姆会员店",
    "京东", "天猫", "淘宝", "拼多多", "唯品会", "考拉海购", "聚美优品",
    "国美", "苏宁", "五星电器", "迪信通", "顺电", "苏宁易购",
    # 汽车
    "特斯拉", "比亚迪", "吉利", "长城", "长安", "上汽", "广汽", "一汽", "东风", "北汽",
    "蔚来汽车", "小鹏汽车", "理想汽车", "哪吒汽车", "零跑汽车", "威马汽车",
    "宁德时代", "亿纬锂能", "国轩高科", "中创新航", "蜂巢能源",
    "潍柴动力", "玉柴", "锡柴", "重汽", "陕汽", "北奔重卡",
    "米其林", "固特异", "普利司通", "倍耐力", "韩泰", "佳通",
    "博世", "大陆", "采埃孚", "麦格纳", "爱信", "格特拉克",
    # 医疗健康
    "恒瑞医药", "百济神州", "信达生物", "君实生物", "再鼎医药", "荣昌生物",
    "迈瑞医疗", "联影医疗", "鱼跃医疗", "九安医疗", "乐普医疗", "微创医疗",
    "京东健康", "阿里健康", "平安好医生", "丁香园", "微医", "好大夫",
    "药明康德", "药明生物", "康龙化成", "昭衍新药", "美迪西",
    "爱尔眼科", "通策医疗", "爱康国宾", "美年健康", "瑞尔齿科",
    "云南白药", "片仔癀", "东阿阿胶", "同仁堂", "九芝堂", "马应龙",
    "修正药业", "扬子江药业", "复星医药", "上海医药", "九州药业",
    "GSK", "Pfizer", "Johnson & Johnson", "Roche", "Novartis", "Sanofi", "Bayer", "AstraZeneca", "MSD",
    # 工业/制造
    "中国商飞", "中国中车", "中航工业", "航天科技", "航天科工", "中船重工",
    "三一重工", "中联重科", "徐工机械", "柳工机械", "临工机械", "龙工控股",
    "振华重工", "华滋", "润邦股份",
    "海螺水泥", "华新水泥", "冀东水泥", "山水水泥", "天瑞水泥",
    "宝武钢铁", "河钢集团", "沙钢集团", "鞍钢集团", "首钢集团",
    "中国铝业", "中国建材", "海螺型材", "北新建材",
    "特变电工", "阳光电源", "隆基绿能", "通威股份", "天合光能", "晶澳科技",
    "宁德时代", "亿纬锂能", "国轩高科", "孚能科技", "欣旺达", "鹏辉能源",
    "国电南瑞", "许继电气", "平高电气", "思源电气", "特变电工",
    # 房地产/建筑
    "万科集团", "碧桂园", "恒大集团", "融创中国", "中国海外", "华润置地",
    "龙湖集团", "金地集团", "绿地集团", "保利发展", "招商蛇口", "华夏幸福",
    "新城控股", "中南建设", "金科股份", "阳光城", "旭辉集团",
    "中国建筑", "中国中铁", "中国铁建", "中国交建", "中国电建", "中国能建",
    "中国化学", "中国核建", "中冶集团", "上海建工", "北京建工",
    # 教育
    "好未来", "新东方", "学而思", "猿辅导", "作业帮", "高途", "一起教育",
    "VIPKID", "哒哒英语", "兰迪少儿英语", "VIPKID", "51Talk",
    "中公教育", "华图教育", "粉笔教育", "导氮教育",
    "中银集团", "中汇", "瑞思学科", "英孚教育", "华尔街英语",
    "智慧树", "学习通", "雨课堂", "classIn", "腾讯课堂", "网易云课堂",
    # 其他知名
    "万科物业", "碧桂园服务", "龙湖物业", "融创服务", "华润万象生活",
    "顺丰速运", "京东物流", "菜鸟网络", "极兔速递", "京东快递",
    "中国邮政", "EMS", "顺丰同城", "闪送", "达达",
    # 人力资源/猎头
    "科锐国际", "米高蒲志", "Michael Page", "Adecco", "Manpower", "Randstad",
    # 基金
    "国海富兰克林基金", "汇添富基金", "易方达基金", "南方基金", "华夏基金", "嘉实基金", "博时基金", "富国基金", "工银基金", "建信基金",
    "滴滴出行", "嘀嗒出行", "首汽约车", "T3出行", "曹操出行", "美团打车",
    "哈啰出行", "青桔单车", "美团单车", "摩拜单车",
    "猫眼", "淘票票", "时光网", "万达电影", "横店影视", "金逸影视",
    "Keep", "咕咚", "小米运动", "华为运动", "Fitbit",
    "小天才", "步步高", "读书郎", "优学派", "科大讯飞学习机",
}

# 常见城市
SUPPORTED_CITIES = {
    "北京", "上海", "深圳", "广州", "杭州", "成都", "武汉", "南京", "苏州",
    "西安", "重庆", "天津", "长沙", "郑州", "东莞", "佛山", "厦门", "福州",
    "济南", "青岛", "大连", "沈阳", "哈尔滨", "长春", "昆明", "贵阳", "南宁",
    "石家庄", "太原", "合肥", "南昌", "宁波", "无锡", "珠海", "中山", "惠州",
    "常州", "徐州", "温州", "嘉兴", "金华", "泉州", "烟台", "潍坊", "临沂",
    "洛阳", "唐山", "保定", "邯郸", "海口", "三亚", "兰州", "银川",
    "西宁", "乌鲁木齐", "拉萨", "呼和浩特", "昆山", "江门", "肇庆", "汕头",
    "漳州", "柳州", "遵义", "绵阳", "泸州"
}

# ---------------------- 时间过滤配置 ----------------------
# 发布于这些时间之后的招聘信息才会被保留
# 格式：datetime(年, 月, 日, 时, 分, 秒)

POST_AFTER = datetime(2026, 3, 1, 0, 0, 0)  # 2026年3月1日起


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
    posted_timestamp: Optional[int] = None  # Unix timestamp，用于时间过滤
    hash_id: str = ""  # 用于去重

    def __post_init__(self):
        if not self.hash_id:
            self.hash_id = hashlib.md5(
                f"{self.source}{self.company}{self.title}{self.city}".encode()
            ).hexdigest()[:12]

    def to_dict(self) -> dict:
        return asdict(self)


def parse_posted_time(time_str: str) -> Optional[int]:
    """解析发布时间字符串，返回 Unix timestamp

    支持格式：
    - "2026-03-19"
    - "2026.03.19"
    - "2026-03-19 发布"
    - "3天前"
    - "1周前"
    """
    if not time_str:
        return None

    # 清理字符串
    time_str = time_str.strip()
    time_str = re.sub(r'发布|前$', '', time_str).strip()

    # 尝试解析日期格式
    for fmt in ["%Y.%m.%d", "%Y-%m-%d", "%Y/%m/%d"]:
        try:
            dt = datetime.strptime(time_str[:10], fmt)
            return int(dt.timestamp())
        except ValueError:
            continue

    # ✅ 新增：支持中文日期格式 "2026年03月09日"
    try:
        m = re.match(r'(\d{4})年(\d{2})月(\d{2})日', time_str)
        if m:
            dt = datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)))
            return int(dt.timestamp())
    except:
        pass

    # 解析相对时间
    if "天" in time_str:
        try:
            days = int(re.search(r'(\d+)', time_str).group(1))
            return int((datetime.now() - timedelta(days=days)).timestamp())
        except:
            pass

    if "周" in time_str:
        try:
            weeks = int(re.search(r'(\d+)', time_str).group(1))
            return int((datetime.now() - timedelta(weeks=weeks)).timestamp())
        except:
            pass

    return None


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
                if match.lastindex and match.lastindex >= 2:
                    max_val = int(match.group(2))
                else:
                    max_val = min_val  # 单值薪资

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
                    const linkEl = item.querySelector('a.title');

                    // 优先使用 title 属性（正常文本），其次 innerText
                    let title = titleEl?.getAttribute('title') || '';
                    // 如果 title 属性是乱码，用 innerText
                    if (!title || /[\ue000-\uf8ff]/.test(title)) {
                        const href = linkEl?.href || '';
                        title = titleEl?.innerText?.replace(/[\ue000-\uf8ff]/g, '')?.trim() || '';
                    }
                    const company = companyEl?.getAttribute('title') || companyEl?.innerText?.trim() || '';
                    const link = linkEl?.href || '';

                    // 从完整文本中提取城市（格式：城市 | 天/周 | X个月）
                    const fullText = item.innerText || '';
                    const lines = fullText.split('\\n').filter(l => l.trim());
                    let city = '';

                    // 查找包含 "城市 |" 格式的行
                    const cityPattern = /^([^\|]+)\s*\|/;
                    for (const line of lines) {
                        const match = line.match(cityPattern);
                        if (match && match[1]) {
                            const potentialCity = match[1].trim();
                            // 验证是否是已知的城市名
                            const knownCities = ['北京', '上海', '深圳', '广州', '杭州', '成都', '武汉', '南京', '苏州', '西安', '重庆', '天津', '长沙', '郑州', '东莞', '佛山', '厦门', '福州', '济南', '青岛', '大连', '沈阳', '哈尔滨', '长春', '昆明', '贵阳', '南宁', '石家庄', '太原', '合肥', '南昌'];
                            if (knownCities.some(c => potentialCity.includes(c))) {
                                city = potentialCity;
                                break;
                            }
                        }
                    }

                    // 提取薪资（格式：数字-数字/天 或 面议）
                    let salary = '';
                    for (const line of lines) {
                        if (line.includes('/天') || line.includes('面议')) {
                            // 清理 icon font
                            salary = line.replace(/[\ue000-\uf8ff]/g, '').trim();
                            break;
                        }
                    }

                    if (title || company) {
                        results.push({ title, company, city, salary, link });
                    }
                });

                return results;
            }
        """)

        for item in job_data:
            # 清理 icon font 和 HTML 实体
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

                // 牛客网校园招聘页面选择器
                const selectors = [
                    '.job-list .job-item',
                    '.job-item',
                    '[class*="job-item"]',
                    '[class*="job-card"]',
                    '.recruit-list .recruit-item',
                    '[class*="recruit-item"]'
                ];

                let items = [];
                selectors.forEach(sel => {
                    const found = document.querySelectorAll(sel);
                    if (found.length > 0) {
                        items = items.concat(Array.from(found));
                    }
                });

                // 去重
                const seen = new Set();
                items = items.filter(item => {
                    if (seen.has(item)) return false;
                    seen.add(item);
                    return true;
                });

                items.forEach(item => {
                    const text = item.innerText || '';
                    const lines = text.split('\\n').map(l => l.trim()).filter(l => l);

                    let title = '', company = '', city = '', salary = '';
                    const knownCities = ['北京', '上海', '深圳', '广州', '杭州', '成都', '武汉', '南京', '西安', '苏州', '天津', '重庆', '长沙', '郑州', '东莞', '佛山', '宁波', '青岛', '济南', '大连', '哈尔滨', '长春', '沈阳', '石家庄', '福州', '厦门', '南昌', '合肥', '昆明', '贵阳'];
                    const companyKeywords = ['有限', '集团', '科技', '公司', '银行', '基金', '保险', '证券', '投资', '资本', '控股', '股份'];
                    const statusKeywords = ['毕业', 'HR', '薪资', '面议', '投', '反馈', '收藏', '在线', '处理', '稳定', '不错', '很好', '高薪', '直达', '专属', '内推', '类职', '同专', '指数', '榜', '今日', '刚', '日', '周', '收藏', '处理', '反馈', '稳定', '氛围', '体验', '超过', '同类'];

                    // 标题：第一行，去掉城市后缀（-城市）
                    const firstLine = lines[0] || '';
                    const titleParts = firstLine.split('-');
                    if (titleParts.length >= 2 && knownCities.includes(titleParts[titleParts.length - 1].trim())) {
                        title = titleParts.slice(0, -1).join('-').trim();
                    } else {
                        title = firstLine;
                    }

                    // 遍历所有行提取：公司、薪资、城市
                    for (let i = 1; i < lines.length; i++) {
                        const line = lines[i];

                        // 薪资：包含K或面议
                        if (!salary && (line.includes('K') || line.includes('面议'))) {
                            salary = line;
                        }

                        // 城市：单个已知城市
                        if (!city && knownCities.some(c => line === c)) {
                            city = line;
                        }

                        // 公司名：包含公司关键词的直接是公司
                        if (!company && companyKeywords.some(k => line.includes(k))) {
                            company = line;
                        }
                    }

                    // 如果还没找到公司，尝试用位置推断
                    // 公司通常在教育要求行之后，industry行之前
                    if (!company) {
                        for (let i = 1; i < lines.length; i++) {
                            const line = lines[i];
                            // 如果这一行不包含状态关键词，且后面有行业/规模信息
                            if (!statusKeywords.some(k => line.includes(k)) && line.length >= 2 && line.length <= 15) {
                                // 检查后面是否有规模信息（包含"人"）
                                const hasSizeAfter = lines.slice(i + 1, i + 3).some(l => l.includes('人') && l.match(/^\d+/));
                                if (hasSizeAfter) {
                                    company = line;
                                    break;
                                }
                            }
                        }
                    }

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

        # OfferShow 城市列表（用于从公司名中提取城市）
        KNOWN_CITIES = ['北京', '上海', '深圳', '广州', '杭州', '成都', '武汉', '南京', '西安', '苏州', '天津', '重庆', '长沙', '郑州', '东莞', '佛山', '宁波', '青岛', '济南', '大连', '哈尔滨', '长春', '沈阳', '石家庄', '福州', '厦门', '南昌', '合肥', '昆明', '贵阳', '乌鲁木齐', '兰州', '太原', '海口', '呼和浩特', '拉萨', '银川', '西宁', '无锡', '常州', '徐州', '南通', '温州', '泉州', '珠海', '中山', '惠州', '江门', '湛江', '汕头', '莆田', '漳州', '龙岩', '三明', '南平', '宁德', '茂名', '肇庆', '韶关', '桂林', '柳州', '梧州', '北海', '钦州', '贵港', '玉林', '百色', '贺州', '河池', '来宾', '崇左']

        for item in data:
            company = item.get('company', '').strip()
            title = item.get('title', '').strip()
            posted_str = item.get('posted', '')

            # 从职位标题中提取公司名（如果没有单独的公司名）
            if not company and title:
                company_match = re.match(r'^([A-Za-z\u4e00-\u9fa5]{2,10})', title)
                if company_match:
                    company = company_match.group(1)

            # 尝试从公司名中提取城市（如"深圳市xxx" -> "深圳"）
            city = ""
            if company:
                for c in KNOWN_CITIES:
                    if company.startswith(c) or company[:4].endswith(c):
                        city = c
                        break

            if title and len(title) > 4:
                posted_formatted = posted_str.replace('.', '-') if posted_str else None
                job = JobListing(
                    source=self.name,
                    company=company,
                    title=title,
                    city=city,
                    posted_time=posted_formatted,
                    posted_timestamp=parse_posted_time(posted_str)
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

    def run(self, sources: List[str] = None, cities: List[str] = None, job_type: str = None,
            salary_min: int = None, posted_within_days: int = None, verify_size: bool = True) -> List[JobListing]:
        """运行爬虫

        Args:
            sources: 指定来源列表
            cities: 城市过滤列表（如 ["深圳", "上海"]），支持多城市
            job_type: 职位类型过滤（实习/校招/社招）
            salary_min: 最低日薪过滤
            posted_within_days: 只保留最近 N 天内发布的职位
            verify_size: 是否验证公司规模
        """
        print("=" * 60)
        print("🚀 多源招聘信息爬虫启动")
        if cities:
            print(f"📍 城市过滤: {', '.join(cities)}")
        if job_type:
            print(f"💼 职位类型过滤: {job_type}")
        if salary_min:
            print(f"💰 最低日薪: {salary_min}元/天")
        if posted_within_days:
            print(f"⏰ 只保留最近 {posted_within_days} 天发布的职位")
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

        # 城市过滤：区分平台是否提供 city
        # - 平台提供 city：空 city 按不匹配处理（应被过滤）
        # - 平台不提供 city（如 OfferShow）：空 city 保留（未知数据）
        SOURCES_WITHOUT_CITY = {"offershow", "xiaohongshu"}
        if cities:
            before = len(unique_jobs)
            city_filters = [c.strip() for c in cities]
            matched = [j for j in unique_jobs if j.city and any(cf in j.city for cf in city_filters)]
            unknown_city = [j for j in unique_jobs if not j.city and j.source in SOURCES_WITHOUT_CITY]
            unique_jobs = matched + unknown_city
            filtered = before - len(unique_jobs)
            unknown_count = len(unknown_city)
            print(f"\n🏙️ 城市过滤后: {len(unique_jobs)} 条 (匹配 {len(matched)} 条，未知城市保留 {unknown_count} 条)")

        # 职位类型过滤
        if job_type:
            type_before = len(unique_jobs)
            # job_type 支持模糊匹配：实习->实习, 校招->校招/春秋招, 社招->社招
            type_keyword_map = {
                "实习": ["实习"],
                "校招": ["校招", "春招", "秋招", "应届", "校园招聘"],
                "社招": ["社招", "社会招聘", "全职"]
            }
            keywords = type_keyword_map.get(job_type, [job_type])
            unique_jobs = [j for j in unique_jobs if j.job_type and any(kw in j.job_type for kw in keywords)]
            filtered_type = type_before - len(unique_jobs)
            if filtered_type > 0:
                print(f"💼 职位类型过滤后: {len(unique_jobs)} 条 (过滤 {filtered_type} 条)")

        # 薪资过滤：日薪 >= salary_min
        if salary_min is not None and salary_min > 0:
            sal_before = len(unique_jobs)
            unique_jobs = [j for j in unique_jobs if j.salary_min and j.salary_min >= salary_min]
            filtered_sal = sal_before - len(unique_jobs)
            if filtered_sal > 0:
                print(f"💰 薪资过滤后: {len(unique_jobs)} 条 (过滤 {filtered_sal} 条，日薪<{salary_min}元)")

        # 时间范围过滤：只保留最近 N 天内发布的职位
        if posted_within_days is not None and posted_within_days > 0:
            range_before = len(unique_jobs)
            cutoff_ts = int((datetime.now() - timedelta(days=posted_within_days)).timestamp())
            # 有时间戳的按时间戳过滤，无时间戳的假设为最新保留
            unique_jobs = [j for j in unique_jobs if j.posted_timestamp is None or j.posted_timestamp >= cutoff_ts]
            filtered_range = range_before - len(unique_jobs)
            if filtered_range > 0:
                print(f"⏰ 时间范围过滤后: {len(unique_jobs)} 条 (过滤 {filtered_range} 条，保留最近{posted_within_days}天)")

        # 公司规模过滤
        if verify_size:
            size_before = len(unique_jobs)
            unique_jobs = [j for j in unique_jobs if self.is_large_company(j.company)]
            print(f"🏢 大厂过滤后: {len(unique_jobs)} 条 (过滤 {size_before - len(unique_jobs)} 条)")

        # 时间过滤：只保留 POST_AFTER 之后发布的职位
        # 没有时间戳的职位保留（假设是最近的）
        time_before = len(unique_jobs)
        post_after_ts = int(POST_AFTER.timestamp())
        unique_jobs = [j for j in unique_jobs if j.posted_timestamp is None or j.posted_timestamp >= post_after_ts]
        filtered_count = time_before - len(unique_jobs)
        if filtered_count > 0:
            print(f"⏰ 时间过滤后: {len(unique_jobs)} 条 (过滤 {filtered_count} 条，保留 {POST_AFTER.strftime('%Y.%m.%d')} 之后)")
        else:
            print(f"⏰ 时间过滤后: {len(unique_jobs)} 条 (无时间戳假设为最新)")

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
    parser.add_argument("--cities", nargs="+", help="城市过滤，支持多城市（如：深圳 上海 北京）")
    parser.add_argument("--job-type", type=str, choices=["实习", "校招", "社招"], help="职位类型过滤")
    parser.add_argument("--salary-min", type=int, help="最低日薪过滤（如：200）")
    parser.add_argument("--posted-within-days", type=int, help="只保留最近 N 天内发布的职位（如：7）")
    parser.add_argument("--no-verify-size", action="store_true", help="跳过公司规模验证")

    args = parser.parse_args()

    scraper = JobScraper(config_path=args.config)
    scraper.run(
        sources=args.sources,
        cities=args.cities,
        job_type=args.job_type,
        salary_min=args.salary_min,
        posted_within_days=args.posted_within_days,
        verify_size=not args.no_verify_size
    )
    scraper.export(format=args.format, filepath=args.output)
