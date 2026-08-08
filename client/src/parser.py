"""
Demo 解析模块
使用 demoparser2 解析 CS2 demo 文件
"""

import pandas as pd

try:
    from demoparser2 import DemoParser
except ImportError:
    print("❌ 错误: 未安装 demoparser2")
    print("请运行: pip install -r requirements.txt")
    raise


def parse_demo(demo_path):
    """
    解析 CS2 demo 文件
    
    Args:
        demo_path: demo 文件路径
        
    Returns:
        dict: 包含地图信息和所有事件的字典
    """
    parser = DemoParser(demo_path)
    
    # 解析 header 获取基本信息
    header = parser.parse_header()
    
    # 需要解析的事件类型
    events_to_parse = [
        "weapon_fire",           # 武器发射（包括投掷物）
        "hegrenade_detonate",    # 高爆手雷爆炸
        "flashbang_detonate",    # 闪光弹爆炸
        "smokegrenade_detonate", # 烟雾弹爆炸
        "molotov_detonate",      # 燃烧瓶爆炸
        "inferno_startburn",     # 燃烧弹开始燃烧
        "decoy_started",         # 诱饵弹启动
    ]
    
    # 需要的玩家属性
    player_props = [
        "X", "Y", "Z", "pitch", "yaw", "name", "team_name",
        "velocity_X", "velocity_Y", "velocity_Z",  # 速度数据用于跳投检测
        "is_airborne",  # 是否在空中
        "in_crouch"     # 是否蹲下
    ]
    
    # 需要的其他属性
    other_props = ["weapon", "x", "y", "z"]
    
    # 解析事件
    results = parser.parse_events(
        events_to_parse,
        player=player_props,
        other=other_props
    )
    
    # 解析烟雾实体以获取准确落点
    print("  ⏳ 解析烟雾实体位置...")
    try:
        # 解析所有 tick 的烟雾实体
        df = parser.parse_grenades()
        smoke_entities = {}
        grenade_velocities = {}  # 存储道具的初始速度
        
        if df is not None and not df.empty:
            # 只处理投射物类型（飞行中的道具），排除手持状态
            projectile_types = [
                'CSmokeGrenadeProjectile',
                'CFlashbangProjectile', 
                'CHEGrenadeProjectile',
                'CMolotovProjectile',
                'CIncendiaryProjectile'
            ]
            projectile_df = df[df['grenade_type'].isin(projectile_types)].copy()
            
            # 处理所有道具类型
            for entity_id, group in projectile_df.groupby('grenade_entity_id'):
                group = group.sort_values('tick').copy()
                
                # 获取初始速度（前几帧的平均速度）
                if len(group) >= 2:
                    # 取前2帧计算初始速度
                    first_frames = group.head(2)
                    dx = first_frames['x'].iloc[1] - first_frames['x'].iloc[0]
                    dy = first_frames['y'].iloc[1] - first_frames['y'].iloc[0]
                    dz = first_frames['z'].iloc[1] - first_frames['z'].iloc[0]
                    dt = first_frames['tick'].iloc[1] - first_frames['tick'].iloc[0]
                    
                    if dt > 0 and not (pd.isna(dx) or pd.isna(dy) or pd.isna(dz)):
                        # 速度 = 位移 / 时间（tick数）
                        vx = dx / dt
                        vy = dy / dt
                        vz = dz / dt
                        speed = (vx**2 + vy**2 + vz**2) ** 0.5
                        
                        grenade_velocities[entity_id] = {
                            'vx': vx,
                            'vy': vy,
                            'vz': vz,
                            'speed': speed,
                            'tick': int(first_frames['tick'].iloc[0]),
                            'name': first_frames['name'].iloc[0] if 'name' in first_frames.columns else 'Unknown',
                            'grenade_type': first_frames['grenade_type'].iloc[0]
                        }
            
            # 只保留烟雾弹投射物（CSmokeGrenadeProjectile = 飞行中和落地后的烟雾）
            smoke_df = df[df['grenade_type'] == 'CSmokeGrenadeProjectile'].copy()
            
            if not smoke_df.empty:
                # 按 grenade_entity_id 分组，获取每个烟雾的最终静止位置
                for entity_id, group in smoke_df.groupby('grenade_entity_id'):
                    # 计算每帧的移动速度
                    group = group.sort_values('tick').copy()
                    
                    # 计算相邻帧之间的位置变化（速度）
                    group['dx'] = group['x'].diff().fillna(0)
                    group['dy'] = group['y'].diff().fillna(0)
                    group['dz'] = group['z'].diff().fillna(0)
                    group['speed'] = ((group['dx']**2 + group['dy']**2 + group['dz']**2) ** 0.5).fillna(0)
                    
                    # 找到速度低于阈值的帧（认为已经静止）
                    # 烟雾弹完全静止时speed应该接近0
                    SPEED_THRESHOLD = 1.0  # 速度阈值（单位/tick）
                    still_frames = group[group['speed'] < SPEED_THRESHOLD]
                    
                    if not still_frames.empty:
                        # 取最后一个静止帧作为最终位置
                        final_pos = still_frames.iloc[-1]
                    else:
                        # 如果没有静止帧，取最后一帧
                        final_pos = group.iloc[-1]
                    
                    smoke_entities[entity_id] = {
                        'x': final_pos['x'],
                        'y': final_pos['y'],
                        'z': final_pos['z'],
                        'tick': int(final_pos['tick']),
                        'name': final_pos.get('name', 'Unknown')  # 投掷者名字
                    }
                
                print(f"  ✅ 找到 {len(smoke_entities)} 个烟雾实体的最终位置")
                print(f"  ✅ 找到 {len(grenade_velocities)} 个道具的初始速度")
    except Exception as e:
        print(f"  ⚠️  烟雾实体解析失败: {e}")
        import traceback
        traceback.print_exc()
        smoke_entities = {}
        grenade_velocities = {}
    
    # demoparser2 返回 list of (event_name, dataframe)
    events = []
    
    if isinstance(results, list):
        for item in results:
            if isinstance(item, tuple) and len(item) == 2:
                event_name, df = item
                if hasattr(df, 'to_dict'):
                    # 将 DataFrame 转换为字典列表，并添加事件名
                    event_records = df.to_dict('records')
                    for record in event_records:
                        record['event_name'] = event_name
                        events.append(record)
    
    print(f"  ✅ 解析到 {len(events)} 个事件")
    
    result = {
        'map_name': header.get('map_name', 'unknown'),
        'duration': header.get('playback_time', 0),
        'playback_ticks': header.get('playback_ticks', 0),
        'tick_rate': calculate_tick_rate(header),
        'events': events,
        'smoke_entities': smoke_entities,
        'grenade_velocities': grenade_velocities,  # 添加道具初始速度
        'total_events': len(events)
    }
    
    return result


def calculate_tick_rate(header):
    """计算 tick rate"""
    playback_time = header.get('playback_time', 0)
    playback_ticks = header.get('playback_ticks', 0)
    
    if playback_time > 0:
        return playback_ticks / playback_time
    return 64.0  # CS2 默认 tick rate


def is_grenade_weapon(weapon):
    """判断是否为投掷物武器"""
    if not weapon:
        return False
    
    weapon_lower = str(weapon).lower()
    grenade_keywords = [
        'hegrenade', 'flashbang', 'smokegrenade', 
        'molotov', 'incgrenade', 'decoy'
    ]
    
    return any(keyword in weapon_lower for keyword in grenade_keywords)


def normalize_weapon_name(weapon):
    """规范化武器名称"""
    if not weapon:
        return 'unknown'
    
    weapon_lower = str(weapon).lower()
    
    mapping = {
        'hegrenade': 'hegrenade',
        'flashbang': 'flashbang',
        'smokegrenade': 'smoke',
        'smoke': 'smoke',
        'molotov': 'molotov',
        'incgrenade': 'incendiary',
        'incendiary': 'incendiary',
        'decoy': 'decoy'
    }
    
    for key, value in mapping.items():
        if key in weapon_lower:
            return value
    
    return weapon
