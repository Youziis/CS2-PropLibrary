#!/usr/bin/env python3
"""检查道具是否有screenshot_id"""
import json
from pathlib import Path

base_path = Path(__file__).parent

files_to_check = [
    'output/commands/selected_for_screenshot.json',
    'output/data/pending_review.json'
]

for filepath in files_to_check:
    full_path = base_path / filepath
    
    print(f"\n📁 {filepath}:")
    
    if not full_path.exists():
        print("   ❌ 文件不存在")
        continue
    
    with open(full_path, encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"   道具数量: {len(data)}")
    
    if data:
        first = data[0]
        has_id = 'screenshot_id' in first
        id_value = first.get('screenshot_id', '不存在')
        
        print(f"   第一个道具:")
        print(f"     有screenshot_id: {has_id}")
        print(f"     值: {id_value}")
        print(f"     类型: {first.get('type', 'unknown')}")
        print(f"     玩家: {first.get('thrower', 'unknown')}")
        
        # 统计有screenshot_id的数量
        with_id = sum(1 for u in data if u.get('screenshot_id') and u.get('screenshot_id') != 'unknown')
        print(f"   有截图ID的道具: {with_id}/{len(data)}")
