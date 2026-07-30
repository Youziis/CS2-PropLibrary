#!/usr/bin/env python3
"""从截图文件重建完整索引"""
import json
import re
from pathlib import Path

base_path = Path(__file__).parent

print("=" * 80)
print("🔧 从截图文件重建完整索引")
print("=" * 80)

# 扫描所有截图文件
screenshots_dir = base_path / 'output/screenshots'
screenshot_files = list(screenshots_dir.glob('*.jpg'))

util_pattern = re.compile(r'(de_\w+)_unknown_util(\d+)_')

screenshot_map = {}  # {(map_name, util_num): True}

for file in screenshot_files:
    match = util_pattern.search(file.name)
    if match:
        map_name = match.group(1)
        util_num = int(match.group(2))
        screenshot_map[(map_name, util_num)] = True

# 按地图分组
maps_utils = {}
for (map_name, util_num) in screenshot_map.keys():
    if map_name not in maps_utils:
        maps_utils[map_name] = []
    if util_num not in maps_utils[map_name]:
        maps_utils[map_name].append(util_num)

for map_name in maps_utils:
    maps_utils[map_name].sort()

print(f"\n📸 找到的截图:")
for map_name, util_nums in sorted(maps_utils.items()):
    print(f"   {map_name}: {len(util_nums)} 个 (util{min(util_nums):03d}-util{max(util_nums):03d})")

# 加载待审核道具
pending_file = base_path / 'output/data/pending_review.json'
with open(pending_file, encoding='utf-8') as f:
    all_utilities = json.load(f)

print(f"\n📚 待审核道具总数: {len(all_utilities)}")

# 按地图分组道具
utilities_by_map = {}
for util in all_utilities:
    map_name = util.get('map', 'unknown')
    if map_name not in utilities_by_map:
        utilities_by_map[map_name] = []
    utilities_by_map[map_name].append(util)

# 创建索引
screenshot_index = {}
total_matched = 0

for map_name, util_nums in sorted(maps_utils.items()):
    if map_name not in utilities_by_map:
        print(f"\n⚠️  {map_name}: 没有找到待审核道具")
        continue
    
    map_utilities = utilities_by_map[map_name]
    
    # 按解析时间排序
    map_utilities.sort(key=lambda u: u.get('parse_time', ''))
    
    print(f"\n🔗 {map_name}:")
    print(f"   截图: {len(util_nums)} 个")
    print(f"   道具: {len(map_utilities)} 个")
    
    matched = 0
    for util_num in util_nums:
        index = util_num - 1
        if 0 <= index < len(map_utilities):
            util = map_utilities[index]
            util_hash = util.get('hash', '')
            if util_hash:
                screenshot_id = f"util{util_num:03d}"
                screenshot_index[util_hash] = screenshot_id
                matched += 1
    
    print(f"   匹配: {matched} 个")
    total_matched += matched

# 保存索引
index_file = base_path / 'output/data/screenshot_index.json'
with open(index_file, 'w', encoding='utf-8') as f:
    json.dump(screenshot_index, f, ensure_ascii=False, indent=2)

print(f"\n✅ 重建完成！")
print(f"   总匹配: {total_matched} 个道具")
print(f"   总索引: {len(screenshot_index)} 条")
print(f"   保存到: {index_file}")
print("\n💡 现在可以刷新管理后台查看所有待审核道具")
print("=" * 80)
