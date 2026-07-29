#!/usr/bin/env python3
"""修复exported.json中缺失的screenshot_id"""
import json
from pathlib import Path

base_path = Path(__file__).parent

# 读取文件
exported_file = base_path / 'output/data/exported.json'
index_file = base_path / 'output/data/screenshot_index.json'

if not exported_file.exists():
    print("❌ exported.json 不存在")
    exit(1)

if not index_file.exists():
    print("❌ screenshot_index.json 不存在")
    exit(1)

# 加载数据
with open(exported_file, encoding='utf-8') as f:
    exported = json.load(f)

with open(index_file, encoding='utf-8') as f:
    screenshot_index = json.load(f)

print("=" * 80)
print("🔧 修复 exported.json 中的 screenshot_id")
print("=" * 80)
print(f"\n已导出道具数: {len(exported)}")
print(f"截图索引数: {len(screenshot_index)}")

# 修复每个道具
fixed_count = 0
for util in exported:
    util_hash = util.get('hash')
    if util_hash and util_hash in screenshot_index:
        old_id = util.get('screenshot_id', 'unknown')
        new_id = screenshot_index[util_hash]
        
        if old_id != new_id:
            util['screenshot_id'] = new_id
            print(f"\n✅ 修复道具: {util.get('display_name', 'unknown')}")
            print(f"   Hash: {util_hash[:16]}...")
            print(f"   旧ID: {old_id}")
            print(f"   新ID: {new_id}")
            fixed_count += 1

# 保存
if fixed_count > 0:
    with open(exported_file, 'w', encoding='utf-8') as f:
        json.dump(exported, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ 已修复 {fixed_count} 个道具")
    print(f"💾 已保存到: {exported_file}")
else:
    print("\n✅ 所有道具的 screenshot_id 都是正确的")

print("\n" + "=" * 80)
print("💡 下一步: 重新导出数据")
print("   在管理后台点击「🚀 重新导出」按钮")
print("=" * 80)
