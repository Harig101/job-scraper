#!/bin/bash
# 常用命令示例

# === 基础抓取 ===

# 抓取所有来源（默认）
python3 scraper.py

# 抓取单个来源
python3 scraper.py --sources shixiseng
python3 scraper.py --sources offershow
python3 scraper.py --sources niukewang

# === 城市过滤（支持多城市） ===

# 单城市
python3 scraper.py --cities 深圳

# 多城市
python3 scraper.py --cities 深圳 上海 北京

# === 职位类型过滤 ===

python3 scraper.py --job-type 实习
python3 scraper.py --job-type 校招
python3 scraper.py --job-type 社招

# === 薪资过滤 ===

python3 scraper.py --salary-min 200
python3 scraper.py --cities 深圳 --salary-min 150

# === 时间范围过滤 ===

python3 scraper.py --posted-within-days 7    # 最近7天
python3 scraper.py --posted-within-days 30   # 最近30天

# === 组合使用 ===

python3 scraper.py --cities 深圳 上海 --job-type 实习 --salary-min 200 --posted-within-days 7

# === 输出格式 ===

python3 scraper.py --format json --output jobs.json
python3 scraper.py --format csv --output jobs.csv

# === 跳过公司规模验证 ===

python3 scraper.py --no-verify-size
python3 scraper.py --cities 深圳 --no-verify-size

# === OpenClaw 调用 ===

# claw run job_scraper --sources shixiseng --format json
# claw run job_scraper --cities 深圳 上海
# claw run job_scraper --cities 北京 --job-type 实习 --salary-min 200
