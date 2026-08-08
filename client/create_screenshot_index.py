#!/usr/bin/env python3
"""
创建截图索引映射
扫描截图文件，将实际存在截图的道具映射到截图ID
优先使用 selected_for_screenshot.json（截图时实际使用的列表）
"""
import json
from pathlib import Path
import re

def create_screenshot_index():
    """创建道具ID到截图序号的映射"""
    
    base_path = Path(__file__).resolve().parent.parent
    
    # 数据文件 - 优先使用截图时选择的文件
    selected_file = base_path / "output" / "commands" / "selected_for_screenshot.json"
    pending_file = base_path / "output" / "data" / "pending_review.json"
    screenshots_dir = base_path / "output" / "screenshots"
    index_file = base_path / "output" / "data" / "screenshot_index.json"
    
    print(f"📂 扫描目录: {screenshots_dir}")
    
    if not screenshots_dir.exists():
        print(f"❌ 未找到截图目录: {screenshots_dir}")
        return
    
    # 优先加载选中的道具列表（截图时实际使用的）
    if selected_file.exists():
        data_file = selected_file
        print(f"✅ 使用截图选择文件: selected_for_screenshot.json")
    elif pending_file.exists():
        data_file = pending_file
        print(f"⚠️  使用待审核文件: pending_review.json")
    else:
        print(f"❌ 未找到道具数据文件")
        return
    
    with open(data_file, 'r', encoding='utf-8') as f:
        all_utilities = json.load(f)
    
    print(f"📚 加载了 {len(all_utilities)} 个道具")
    
    # 扫描截图文件，提取地图和util编号
    screenshot_files = list(screenshots_dir.glob('*.jpg'))
    print(f"📸 找到 {len(screenshot_files)} 个截图文件")
    
    # 只支持新格式：de_dust2_unknown_util001_position.jpg
    util_pattern = re.compile(r'(de_\w+)_unknown_util(\d+)_')
    
    screenshot_map = {}  # {(map_name, util_num): True}
    
    for file in screenshot_files:
        match = util_pattern.search(file.name)
        if match:
            map_name = match.group(1)
            util_num = int(match.group(2))
            screenshot_map[(map_name, util_num)] = True
    
    # 按地图分组统计
    maps_utils = {}
    for (map_name, util_num) in screenshot_map.keys():
        if map_name not in maps_utils:
            maps_utils[map_name] = []
        if util_num not in maps_utils[map_name]:
            maps_utils[map_name].append(util_num)
    
    for map_name in maps_utils:
        maps_utils[map_name].sort()
    
    print(f"🎯 找到截图的地图:")
    for map_name, util_nums in sorted(maps_utils.items()):
        print(f"   {map_name}: {len(util_nums)} 个道具 (util{min(util_nums):03d}-util{max(util_nums):03d})")
    
    # 加载现有索引（如果存在）
    existing_index = {}
    if index_file.exists():
        try:
            with open(index_file, 'r', encoding='utf-8') as f:
                existing_index = json.load(f)
            print(f"📋 加载了现有索引: {len(existing_index)} 条记录")
        except:
            pass
    
    # 按地图分组道具
    utilities_by_map = {}
    for util in all_utilities:
        map_name = util.get('map') or util.get('map_name', 'unknown')
        if map_name not in utilities_by_map:
            utilities_by_map[map_name] = []
        utilities_by_map[map_name].append(util)
    
    # 为每个地图创建映射（保留现有索引）
    screenshot_index = existing_index.copy() if existing_index else {}
    matched_count = 0
    updated_maps = set()
    
    for map_name, util_nums in sorted(maps_utils.items()):
        if map_name not in utilities_by_map:
            print(f"⚠️  {map_name} 没有找到对应的待审核道具")
            continue
        
        map_utilities = utilities_by_map[map_name]
        print(f"\n🔗 匹配 {map_name}:")
        print(f"   截图: {len(util_nums)} 个")
        print(f"   道具: {len(map_utilities)} 个")
        
        # 按解析时间排序道具（保持顺序一致）
        map_utilities.sort(key=lambda u: u.get('parse_time', ''))
        
        # 记录这个地图被更新了
        updated_maps.add(map_name)
        
        # 为每个截图编号匹配道具
        for util_num in util_nums:
            # util编号从1开始，对应列表索引0
            index = util_num - 1
            if 0 <= index < len(map_utilities):
                util = map_utilities[index]
                util_hash = util.get('hash', '')
                if util_hash:
                    screenshot_id = f"util{str(util_num).zfill(3)}"
                    screenshot_index[util_hash] = screenshot_id
                    matched_count += 1
    
    print(f"\n✅ 创建截图索引成功！")
    print(f"   本次匹配: {matched_count} 个道具")
    print(f"   总索引数: {len(screenshot_index)} 条")
    
    # 保存映射文件
    with open(index_file, 'w', encoding='utf-8') as f:
        json.dump(screenshot_index, f, ensure_ascii=False, indent=2)
    
    print(f"   保存到: {index_file}")
    
    # 显示更新的地图
    if updated_maps:
        print(f"\n📋 本次更新的地图: {', '.join(sorted(updated_maps))}")
    
    # 显示每个地图的映射示例
    if screenshot_index:
        print(f"\n📋 映射示例:")
        for map_name in sorted(maps_utils.keys()):
            map_examples = [(h, sid) for h, sid in screenshot_index.items() 
                          if any(u.get('hash') == h and u.get('map') == map_name 
                                for u in all_utilities)][:3]
            if map_examples:
                print(f"\n   {map_name}:")
                for hash_val, util_id in map_examples:
                    util = next((u for u in all_utilities if u.get('hash') == hash_val), None)
                    if util:
                        print(f"     {util.get('type', 'unknown'):10s} - {util.get('thrower', 'unknown'):15s} -> {util_id}")

if __name__ == "__main__":
    create_screenshot_index()
