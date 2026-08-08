"""
数据库模块
保存和管理道具数据
"""

import json
import csv
from collections import defaultdict


def save_database(utilities):
    """
    保存道具数据库
    
    Args:
        utilities: 所有道具数据列表
    """
    # 1. 保存完整数据（JSON）
    save_json(utilities, 'output/data/utilities_full.json')
    print(f"  ✅ 完整数据: output/data/utilities_full.json")
    
    # 2. 按地图分组保存
    by_map = group_by_map(utilities)
    for map_name, items in by_map.items():
        filename = f'output/data/{map_name}_utilities.json'
        save_json(items, filename)
        print(f"  ✅ 地图数据: {filename}")
    
    # 3. 生成游戏内指令
    save_commands(utilities)
    print(f"  ✅ 游戏指令: output/commands/utilities_commands.json")
    
    # 4. 生成统计报告
    stats = generate_statistics(utilities)
    save_json(stats, 'output/data/statistics.json')
    print(f"  ✅ 统计报告: output/data/statistics.json")
    
    # 5. 生成 CSV
    save_csv(utilities, 'output/data/utilities.csv')
    print(f"  ✅ CSV 文件: output/data/utilities.csv")


def save_json(data, filepath):
    """保存 JSON 文件"""
    import numpy as np
    
    # 递归转换 numpy 类型为 Python 原生类型
    def convert_to_native(obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, dict):
            return {key: convert_to_native(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [convert_to_native(item) for item in obj]
        else:
            return obj
    
    data = convert_to_native(data)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def save_commands(utilities):
    """
    生成游戏内可直接使用的指令
    每个道具一条 setpos + setang 指令
    """
    # 按地图和类型分组
    commands = defaultdict(lambda: defaultdict(lambda: {'type_name': '', 'count': 0, 'utilities': []}))
    
    for util in utilities:
        map_name = util['map']
        util_type = util['type']
        
        # 使用修正后的位置（对跳投更准确）
        pos = util.get('throw_position_corrected', util['throw_position'])
        angles = util['throw_angles']
        command = f"setpos {pos['x']:.2f} {pos['y']:.2f} {pos['z']:.2f}; setang {angles['pitch']:.2f} {angles['yaw']:.2f} 0"
        
        # 获取投掷方式的中文名称
        throw_type_names = {
            'jump': '跳投',
            'stand': '站投',
            'crouch': '蹲投',
            'elevated': '高位'
        }
        throw_type_cn = throw_type_names.get(util.get('throw_type', 'stand'), '未知')
        
        # 构建数据
        util_data = {
            'id': util['id'],
            'index': len(commands[map_name][util_type]['utilities']) + 1,
            'command': command,
            'thrower': util['thrower'],
            'team': util['team'],
            'throw_type': util.get('throw_type', 'stand'),  # 投掷方式（英文）
            'throw_type_name': throw_type_cn,  # 投掷方式（中文）
            'velocity_z': util.get('velocity', {}).get('z', 0),  # 玩家垂直速度
            'grenade_velocity': util.get('grenade_velocity'),  # 道具出手速度
            'direction': util['direction']['cardinal'],
            'pitch_type': util['direction']['pitch_type'],
            'position': pos,
            'position_original': util['throw_position'],  # 保留原始位置
            'angles': angles,
            'land_position': util['land_position'],
            'distance': util['distance'],
            'flight_time': util['flight_time']
        }
        
        commands[map_name][util_type]['utilities'].append(util_data)
        commands[map_name][util_type]['type_name'] = get_type_name(util_type)
        commands[map_name][util_type]['count'] = len(commands[map_name][util_type]['utilities'])
    
    # 转换为普通字典并保存
    result = {map_name: dict(types) for map_name, types in commands.items()}
    save_json(result, 'output/commands/utilities_commands.json')


def save_csv(utilities, filepath):
    """保存 CSV 文件"""
    if not utilities:
        return
    
    headers = [
        'ID', '类型', '投掷者', '队伍', '地图',
        '投掷位置X', '投掷位置Y', '投掷位置Z',
        '落点X', '落点Y', '落点Z',
        '俯仰角', '偏航角', '飞行时间', '距离',
        '方向', '投掷方式'
    ]
    
    with open(filepath, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        
        for util in utilities:
            row = [
                util['id'],
                util['type'],
                util['thrower'],
                util['team'],
                util['map'],
                round(util['throw_position']['x'], 2),
                round(util['throw_position']['y'], 2),
                round(util['throw_position']['z'], 2),
                round(util['land_position']['x'], 2),
                round(util['land_position']['y'], 2),
                round(util['land_position']['z'], 2),
                round(util['throw_angles']['pitch'], 2),
                round(util['throw_angles']['yaw'], 2),
                round(util['flight_time'], 2),
                round(util['distance'], 2),
                util['direction']['cardinal'],
                util['direction']['pitch_type']
            ]
            writer.writerow(row)


def group_by_map(utilities):
    """按地图分组"""
    grouped = defaultdict(list)
    for util in utilities:
        grouped[util['map']].append(util)
    return dict(grouped)


def generate_statistics(utilities):
    """生成统计信息"""
    stats = {
        'total': len(utilities),
        'by_type': {},
        'by_map': {},
        'by_player': {},
        'average_flight_time': 0,
        'average_distance': 0
    }
    
    if not utilities:
        return stats
    
    by_type = defaultdict(int)
    by_map = defaultdict(int)
    by_player = defaultdict(int)
    
    total_flight_time = 0
    total_distance = 0
    
    for util in utilities:
        by_type[util['type']] += 1
        by_map[util['map']] += 1
        by_player[util['thrower']] += 1
        total_flight_time += util['flight_time']
        total_distance += util['distance']
    
    stats['by_type'] = dict(by_type)
    stats['by_map'] = dict(by_map)
    stats['by_player'] = dict(by_player)
    stats['average_flight_time'] = total_flight_time / len(utilities)
    stats['average_distance'] = total_distance / len(utilities)
    
    return stats


def print_statistics(utilities):
    """打印统计信息"""
    stats = generate_statistics(utilities)
    
    print("\n📊 统计信息:")
    print(f"  总道具数: {stats['total']}")
    
    print("  按类型分类:")
    for util_type, count in stats['by_type'].items():
        type_name = get_type_name(util_type)
        print(f"    {type_name}: {count}")
    
    print("  按地图分类:")
    for map_name, count in stats['by_map'].items():
        print(f"    {map_name}: {count}")
    
    print(f"  平均飞行时间: {stats['average_flight_time']:.2f}秒")
    print(f"  平均投掷距离: {stats['average_distance']:.2f}单位")


def get_type_name(util_type):
    """获取类型中文名"""
    names = {
        'smoke': '烟雾弹',
        'flashbang': '闪光弹',
        'hegrenade': '手雷',
        'molotov': '燃烧瓶',
        'incendiary': '燃烧弹',
        'decoy': '诱饵弹'
    }
    return names.get(util_type, util_type)
