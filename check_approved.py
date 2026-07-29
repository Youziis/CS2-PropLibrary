#!/usr/bin/env python3
"""检查已批准道具的数据"""
import json
from pathlib import Path

base_path = Path(__file__).parent

# 读取approved.json
approved_file = base_path / 'output/data/approved.json'
exported_file = base_path / 'output/data/exported.json'

print("=" * 80)
print("🔍 检查已批准和已导出的道具")
print("=" * 80)

# 检查approved.json
if approved_file.exists():
    with open(approved_file, encoding='utf-8') as f:
        approved = json.load(f)
    
    print(f"\n📋 approved.json:")
    print(f"   道具数量: {len(approved)}")
    
    if approved:
        first = approved[0]
        print(f"\n   第一个道具的字段:")
        for key in ['hash', 'screenshot_id', 'type', 'display_name', 'thrower']:
            value = first.get(key, '❌ 不存在')
            print(f"     {key}: {value}")
else:
    print(f"\n❌ approved.json 不存在")

# 检查exported.json
if exported_file.exists():
    with open(exported_file, encoding='utf-8') as f:
        exported = json.load(f)
    
    print(f"\n📋 exported.json:")
    print(f"   道具数量: {len(exported)}")
    
    if exported:
        first = exported[0]
        print(f"\n   第一个道具的字段:")
        for key in ['hash', 'screenshot_id', 'type', 'display_name', 'thrower']:
            value = first.get(key, '❌ 不存在')
            print(f"     {key}: {value}")
else:
    print(f"\n❌ exported.json 不存在")

print("\n" + "=" * 80)
