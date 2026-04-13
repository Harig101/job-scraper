#!/usr/bin/env python3
"""
数据校验脚本
检查 jobs.json 的数据质量和完整性
"""

import json
import sys
from pathlib import Path


def validate_jobs(filepath="jobs.json"):
    """校验 jobs.json"""

    if not Path(filepath).exists():
        print(f"❌ 文件不存在: {filepath}")
        return False

    with open(filepath, encoding="utf-8") as f:
        jobs = json.load(f)

    print(f"📊 共 {len(jobs)} 条职位")

    # 检查必需字段
    required_fields = ["source", "company", "title", "city"]
    missing_fields = []
    for job in jobs:
        for field in required_fields:
            if not job.get(field):
                missing_fields.append(f"{job.get('title', '?')} 缺少 {field}")

    if missing_fields:
        print(f"⚠️  {len(missing_fields)} 条记录缺少必填字段")
        for m in missing_fields[:5]:
            print(f"   - {m}")
    else:
        print("✅ 必填字段完整")

    # 检查薪资
    no_salary = [j for j in jobs if not j.get("salary")]
    print(f"💰 无薪资信息: {len(no_salary)} 条")

    # 检查城市分布
    cities = {}
    for job in jobs:
        city = job.get("city", "未知")
        cities[city] = cities.get(city, 0) + 1

    print("\n🏙️ 城市分布:")
    for city, count in sorted(cities.items(), key=lambda x: -x[1])[:10]:
        print(f"   {city}: {count}")

    # 检查来源分布
    sources = {}
    for job in jobs:
        src = job.get("source", "未知")
        sources[src] = sources.get(src, 0) + 1

    print("\n📡 来源分布:")
    for src, count in sorted(sources.items(), key=lambda x: -x[1]):
        print(f"   {src}: {count}")

    return True


if __name__ == "__main__":
    filepath = sys.argv[1] if len(sys.argv) > 1 else "jobs.json"
    validate_jobs(filepath)
