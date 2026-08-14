"""
数据提取模块
从解析的事件中提取和匹配道具投掷数据
"""

import hashlib
from collections import defaultdict


def extract_utilities(demo_data):
    """
    从 demo 数据中提取道具信息
    
    Args:
        demo_data: 解析后的 demo 数据
        
    Returns:
        list: 道具数据列表
    """
    events = demo_data['events']
    tick_rate = demo_data['tick_rate']
    map_name = demo_data['map_name']
    smoke_entities = demo_data.get('smoke_entities', {})
    grenade_velocities = demo_data.get('grenade_velocities', {})
    
    # 分离投掷事件和爆炸事件
    throw_events = []
    detonate_events = []
    
    for event in events:
        event_name = event.get('event_name', '')
        
        # 投掷事件
        if event_name == 'weapon_fire':
            weapon = event.get('weapon', '')
            if is_grenade_weapon(weapon):
                throw_events.append(event)
        
        # 爆炸/激活事件
        elif 'detonate' in event_name or 'startburn' in event_name or 'started' in event_name:
            detonate_events.append(event)
    
    # 匹配投掷和爆炸事件
    utilities = match_throw_detonate(
        throw_events, 
        detonate_events, 
        tick_rate, 
        map_name,
        smoke_entities,
        grenade_velocities
    )
    
    # 过滤重复道具
    utilities = filter_duplicate_utilities(utilities)
    
    return utilities


def match_throw_detonate(throw_events, detonate_events, tick_rate, map_name, smoke_entities=None, grenade_velocities=None):
    """匹配投掷和爆炸事件"""
    utilities = []
    used_detonations = set()
    
    # 辅助函数：获取字段值（支持 user_ 前缀）
    def get_field(event, field_name):
        if field_name in event:
            return event[field_name]
        user_field = f'user_{field_name}'
        if user_field in event:
            return event[user_field]
        return None
    
    for throw_event in throw_events:
        throw_tick = throw_event.get('tick', 0)
        throw_weapon = normalize_weapon_name(throw_event.get('weapon', ''))
        throw_user_id = get_field(throw_event, 'user_id')
        throw_name = get_field(throw_event, 'name')  # 【新增】获取玩家名字
        
        # 查找匹配的爆炸事件
        best_match = None
        min_score = float('inf')
        
        for idx, det_event in enumerate(detonate_events):
            if idx in used_detonations:
                continue
            
            det_tick = det_event.get('tick', 0)
            det_weapon = get_weapon_from_event(det_event)
            det_user_id = get_field(det_event, 'user_id')
            det_name = get_field(det_event, 'name')  # 【新增】获取爆炸事件的玩家名字
            
            # 1. 武器类型匹配
            if det_weapon != throw_weapon:
                continue
            
            # 2. 爆炸在投掷之后
            tick_diff = det_tick - throw_tick
            if tick_diff < 0:
                continue
            
            # 3. 时间差在合理范围内（5秒）
            time_diff = tick_diff / tick_rate
            if time_diff > 5.0:
                continue
            
            # 4. 【新增】烟雾弹的飞行时间合理性检查
            # 烟雾弹正常飞行时间：1-3秒（跳投可能短至0.5秒，远投可能长至4秒）
            # 如果时间太短（<0.5秒），可能是匹配错误
            if throw_weapon == 'smoke' and time_diff < 0.5:
                # 时间太短，降低优先级（但不完全排除，因为可能是近距离投掷）
                time_penalty = 1000
            else:
                time_penalty = 0
            
            # 5. 检查距离是否合理（不能太远）
            throw_pos = {
                'x': get_field(throw_event, 'X'),
                'y': get_field(throw_event, 'Y'),
                'z': get_field(throw_event, 'Z')
            }
            det_pos = {
                'x': det_event.get('x', det_event.get('X', 0)),
                'y': det_event.get('y', det_event.get('Y', 0)),
                'z': det_event.get('z', det_event.get('Z', 0))
            }
            distance = calculate_distance(throw_pos, det_pos)
            
            # 距离太远（超过3000单位）的不匹配
            if distance > 3000:
                continue
            
            # 6. 综合评分
            # - 优先匹配相同玩家（通过name或user_id）
            # - 优先匹配时间较长的（更符合物理）
            # - 距离作为次要因素
            score = tick_diff * -1 + distance * 0.1 + time_penalty  # 时间越长分数越低（越优先）
            
            # 【重点修改】玩家匹配优先级最高
            if det_user_id and throw_user_id and det_user_id == throw_user_id:
                score -= 10000  # user_id匹配
            elif det_name and throw_name and det_name == throw_name:
                score -= 10000  # 名字匹配（同样重要）
            
            if score < min_score:
                best_match = (idx, det_event, tick_diff)
                min_score = score
        
        if best_match:
            idx, det_event, tick_diff = best_match
            used_detonations.add(idx)
            
            utility = create_utility_record(
                throw_event,
                det_event,
                tick_diff,
                tick_rate,
                map_name,
                smoke_entities,
                grenade_velocities
            )
            utilities.append(utility)
    
    return utilities


def detect_jump_throw(position, velocity, is_airborne, in_crouch):
    """
    检测跳投并计算地面位置
    
    参数:
        position: 投掷位置 {x, y, z}
        velocity: 速度向量 {x, y, z}
        is_airborne: 是否在空中
        in_crouch: 是否蹲下
    
    返回:
        (throw_type, corrected_position)
        throw_type: "jump", "stand", "crouch", "elevated"
        corrected_position: 修正后的地面位置 {x, y, z}
    """
    # CS2 物理常量
    GRAVITY = 800.0  # 单位/秒²
    JUMP_VELOCITY = 301.993377  # 跳跃初速度
    JUMP_HEIGHT_MAX = 57.0  # 最大跳跃高度
    
    # 跳投检测阈值
    VELOCITY_Z_THRESHOLD = 150.0  # Z轴速度阈值
    AIRBORNE_Z_OFFSET = 40.0  # 空中时的平均高度偏移
    
    corrected_pos = position.copy()
    
    # 方法1: 使用 velocity_z 检测跳投（最准确）
    vz = velocity.get('z', 0)
    
    if abs(vz) > VELOCITY_Z_THRESHOLD or is_airborne:
        # 检测到跳投
        throw_type = "jump"
        
        # 方法A: 使用速度反推高度（物理计算）
        if vz < 0:
            # 玩家正在下落，计算从最高点下落的高度
            # v² = 2gh -> h = v² / (2g)
            height_from_peak = (vz ** 2) / (2 * GRAVITY)
            corrected_pos['z'] = position['z'] - height_from_peak
        elif vz > 0:
            # 玩家正在上升，计算还能上升多少 + 从最高点落回地面
            # 到最高点还需: h1 = v² / (2g)
            height_to_peak = (vz ** 2) / (2 * GRAVITY)
            # 从最高点落回当前高度再落到地面
            max_height = position['z'] + height_to_peak
            # 假设从最高点落回地面
            corrected_pos['z'] = max_height - JUMP_HEIGHT_MAX
        else:
            # vz ≈ 0，可能在跳跃最高点，使用平均偏移
            corrected_pos['z'] = position['z'] - AIRBORNE_Z_OFFSET
        
        # 方法B（备用）: 如果计算结果不合理，使用固定偏移
        z_diff = position['z'] - corrected_pos['z']
        if z_diff < 0 or z_diff > JUMP_HEIGHT_MAX:
            # 不合理的结果，使用平均偏移
            corrected_pos['z'] = position['z'] - AIRBORNE_Z_OFFSET
            
    elif in_crouch:
        # 蹲投
        throw_type = "crouch"
        # 蹲投时记录的就是准确位置，无需修正
        
    else:
        # 站投
        throw_type = "stand"
        # 站投时记录的就是准确位置，无需修正
    
    # 保证Z坐标不会变成负数（地图最低点检查）
    if corrected_pos['z'] < -500:
        corrected_pos['z'] = position['z']
        throw_type = "elevated"  # 标记为异常高度
    
    return throw_type, corrected_pos


def create_utility_record(throw_event, det_event, tick_diff, tick_rate, map_name, smoke_entities=None, grenade_velocities=None):
    """创建道具记录"""
    # 字段名可能有 user_ 前缀
    def get_field(event, field_name):
        """尝试多种字段名获取值"""
        # 尝试直接获取
        if field_name in event:
            return event[field_name]
        # 尝试带 user_ 前缀
        user_field = f'user_{field_name}'
        if user_field in event:
            return event[user_field]
        # 尝试大写
        if field_name.upper() in event:
            return event[field_name.upper()]
        # 尝试带 user_ 且大写
        user_upper = f'user_{field_name.upper()}'
        if user_upper in event:
            return event[user_upper]
        return 0
    
    throw_pos = {
        'x': get_field(throw_event, 'X'),
        'y': get_field(throw_event, 'Y'),
        'z': get_field(throw_event, 'Z')
    }
    
    # 爆炸事件的坐标字段是小写 x, y, z
    land_pos = {
        'x': det_event.get('x', det_event.get('X', 0)),
        'y': det_event.get('y', det_event.get('Y', 0)),
        'z': det_event.get('z', det_event.get('Z', 0))
    }
    
    # 【方案2】对所有道具类型都直接使用爆炸事件位置
    # 不进行烟雾实体匹配，避免匹配错误
    # 烟雾弹可能有10-50单位的误差，但总比匹配到错误的烟雾好
    
    throw_angles = {
        'pitch': get_field(throw_event, 'pitch'),
        'yaw': get_field(throw_event, 'yaw')
    }
    
    # 获取速度数据用于跳投检测
    velocity = {
        'x': get_field(throw_event, 'velocity_X'),
        'y': get_field(throw_event, 'velocity_Y'),
        'z': get_field(throw_event, 'velocity_Z')
    }
    
    is_airborne = get_field(throw_event, 'is_airborne')
    in_crouch = get_field(throw_event, 'in_crouch')
    
    # 检测跳投并计算地面位置
    throw_type, corrected_pos = detect_jump_throw(
        throw_pos, velocity, is_airborne, in_crouch
    )
    
    weapon_type = normalize_weapon_name(throw_event.get('weapon', ''))
    flight_time = tick_diff / tick_rate
    distance = calculate_distance(throw_pos, land_pos)
    
    # 匹配道具的初始速度（从grenade实体数据）
    throw_tick = throw_event.get('tick', 0)
    grenade_throw_velocity = None
    if grenade_velocities:
        # 找到最接近投掷tick的道具实体
        best_match_id = None
        min_tick_diff = float('inf')
        thrower_name = get_field(throw_event, 'name')
        
        for entity_id, vel_data in grenade_velocities.items():
            # 检查时间和玩家名称匹配
            entity_tick = vel_data['tick']
            entity_name = vel_data.get('name', '')
            
            # 实体tick应该在投掷tick附近（允许10 tick误差）
            tick_diff_match = abs(entity_tick - throw_tick)
            if tick_diff_match > 10:
                continue
            
            # 玩家名称匹配
            if entity_name != thrower_name:
                continue
            
            if tick_diff_match < min_tick_diff:
                best_match_id = entity_id
                min_tick_diff = tick_diff_match
        
        if best_match_id:
            vel_data = grenade_velocities[best_match_id]
            grenade_throw_velocity = {
                'x': vel_data['vx'],
                'y': vel_data['vy'],
                'z': vel_data['vz'],
                'speed': vel_data['speed']
            }
    
    utility = {
        'hash': generate_id(throw_event, det_event),  # ✅ 改为 hash 字段
        'id': generate_id(throw_event, det_event),    # 保留 id 以兼容
        'type': weapon_type,
        'thrower': get_field(throw_event, 'name') or 'Unknown',
        'team': 'T' if (get_field(throw_event, 'team_name') or '').upper() == 'T' else (get_field(throw_event, 'team_name') or 'Unknown'),
        'map': map_name,
        
        # 投掷信息
        'throw_position': throw_pos,
        'throw_position_corrected': corrected_pos,  # 修正后的地面位置
        'throw_type': throw_type,  # 投掷类型: jump, stand, crouch, elevated
        'throw_angles': throw_angles,
        'throw_tick': throw_event.get('tick', 0),
        'throw_time': throw_event.get('tick', 0) / tick_rate,
        'velocity': velocity,  # 玩家身体速度
        'grenade_velocity': grenade_throw_velocity,  # 道具出手速度
        
        # 落点信息
        'land_position': land_pos,
        'land_tick': det_event.get('tick', 0),
        'land_time': det_event.get('tick', 0) / tick_rate,
        
        # 计算信息
        'flight_time': flight_time,
        'distance': distance,
        'velocity': calculate_velocity(throw_pos, land_pos, flight_time),
        'direction': calculate_direction(throw_angles),
    }
    
    return utility


def is_grenade_weapon(weapon):
    """判断是否为投掷物"""
    if not weapon:
        return False
    weapon_lower = str(weapon).lower()
    return any(g in weapon_lower for g in [
        'hegrenade', 'flashbang', 'smokegrenade', 
        'molotov', 'incgrenade', 'decoy'
    ])


def normalize_weapon_name(weapon):
    """规范化武器名称"""
    if not weapon:
        return 'unknown'
    
    weapon_lower = str(weapon).lower()
    mapping = {
        'hegrenade': 'hegrenade',
        'flashbang': 'flashbang',
        'smokegrenade': 'smoke',
        'molotov': 'molotov',
        'incgrenade': 'incendiary',
        'decoy': 'decoy'
    }
    
    for key, value in mapping.items():
        if key in weapon_lower:
            return value
    return weapon


def get_weapon_from_event(event):
    """从事件中获取武器类型"""
    event_name = event.get('event_name', '')
    
    if 'hegrenade' in event_name:
        return 'hegrenade'
    elif 'flashbang' in event_name:
        return 'flashbang'
    elif 'smoke' in event_name:
        return 'smoke'
    elif 'molotov' in event_name:
        return 'molotov'
    elif 'inferno' in event_name or 'incendiary' in event_name:
        return 'incendiary'
    elif 'decoy' in event_name:
        return 'decoy'
    
    return 'unknown'


def calculate_distance(pos1, pos2):
    """计算两点距离"""
    dx = pos2['x'] - pos1['x']
    dy = pos2['y'] - pos1['y']
    dz = pos2['z'] - pos1['z']
    return (dx**2 + dy**2 + dz**2) ** 0.5


def calculate_velocity(start_pos, end_pos, time):
    """计算速度向量"""
    if time == 0:
        return {'x': 0, 'y': 0, 'z': 0}
    
    return {
        'x': (end_pos['x'] - start_pos['x']) / time,
        'y': (end_pos['y'] - start_pos['y']) / time,
        'z': (end_pos['z'] - start_pos['z']) / time
    }


def calculate_direction(angles):
    """计算投掷方向描述"""
    yaw = angles['yaw']
    pitch = angles['pitch']
    
    # 方位判断
    if -22.5 <= yaw < 22.5:
        cardinal = '北'
    elif 22.5 <= yaw < 67.5:
        cardinal = '东北'
    elif 67.5 <= yaw < 112.5:
        cardinal = '东'
    elif 112.5 <= yaw < 157.5:
        cardinal = '东南'
    elif yaw >= 157.5 or yaw < -157.5:
        cardinal = '南'
    elif -157.5 <= yaw < -112.5:
        cardinal = '西南'
    elif -112.5 <= yaw < -67.5:
        cardinal = '西'
    else:
        cardinal = '西北'
    
    # 俯仰角判断
    if pitch < -45:
        pitch_type = '平视'
    elif pitch < -20:
        pitch_type = '略微俯视'
    elif pitch < 0:
        pitch_type = '俯视'
    elif pitch < 20:
        pitch_type = '低角度'
    else:
        pitch_type = '高抛'
    
    return {
        'yaw': yaw,
        'pitch': pitch,
        'cardinal': cardinal,
        'pitch_type': pitch_type
    }


def generate_id(throw_event, det_event):
    """
    生成唯一 ID (hash值)
    基于道具的关键属性，确保相同的道具产生相同的hash
    """
    # 获取字段
    def get_field(event, field_name):
        if field_name in event:
            return event[field_name]
        user_field = f'user_{field_name}'
        if user_field in event:
            return event[user_field]
        return 0
    
    # 使用关键属性生成hash
    throw_pos = (
        round(get_field(throw_event, 'X'), 1),
        round(get_field(throw_event, 'Y'), 1),
        round(get_field(throw_event, 'Z'), 1)
    )
    throw_angles = (
        round(get_field(throw_event, 'pitch'), 1),
        round(get_field(throw_event, 'yaw'), 1)
    )
    land_pos = (
        round(det_event.get('x', 0), 1),
        round(det_event.get('y', 0), 1),
        round(det_event.get('z', 0), 1)
    )
    weapon = throw_event.get('weapon', 'unknown')
    
    # 组合成字符串
    data = f"{throw_pos}_{throw_angles}_{land_pos}_{weapon}"
    
    # 生成16位hash
    return hashlib.md5(data.encode()).hexdigest()[:16]


def analyze_utilities(utilities):
    """分析道具使用统计"""
    stats = {
        'total': len(utilities),
        'by_type': defaultdict(int),
        'by_map': defaultdict(int),
        'by_player': defaultdict(int)
    }
    
    for util in utilities:
        stats['by_type'][util['type']] += 1
        stats['by_map'][util['map']] += 1
        stats['by_player'][util['thrower']] += 1
    
    return dict(stats)


def filter_duplicate_utilities(utilities):
    """
    过滤重复的道具
    
    判断标准：
    - 相同的道具类型
    - 投掷位置接近（50单位内）
    - 投掷角度接近（5度内）
    - 落点位置接近（100单位内）
    
    只保留第一个匹配的道具
    
    Args:
        utilities: 原始道具列表
        
    Returns:
        list: 去重后的道具列表
    """
    if not utilities:
        return []
    
    # 相似度阈值
    POSITION_THRESHOLD = 50.0  # 投掷位置差异阈值（单位）
    ANGLE_THRESHOLD = 5.0      # 角度差异阈值（度）
    LANDING_THRESHOLD = 100.0  # 落点差异阈值（单位）
    
    filtered = []
    
    for util in utilities:
        is_duplicate = False
        
        # 与已保留的道具比较
        for existing in filtered:
            # 1. 必须是相同类型
            if util['type'] != existing['type']:
                continue
            
            # 2. 投掷位置接近
            throw_dist = calculate_distance(
                util['throw_position'],
                existing['throw_position']
            )
            if throw_dist > POSITION_THRESHOLD:
                continue
            
            # 3. 投掷角度接近
            pitch_diff = abs(util['throw_angles']['pitch'] - existing['throw_angles']['pitch'])
            yaw_diff = abs(util['throw_angles']['yaw'] - existing['throw_angles']['yaw'])
            
            # 处理yaw角度的周期性（-180到180）
            if yaw_diff > 180:
                yaw_diff = 360 - yaw_diff
            
            if pitch_diff > ANGLE_THRESHOLD or yaw_diff > ANGLE_THRESHOLD:
                continue
            
            # 4. 落点位置接近
            land_dist = calculate_distance(
                util['land_position'],
                existing['land_position']
            )
            if land_dist > LANDING_THRESHOLD:
                continue
            
            # 所有条件都满足，判定为重复
            is_duplicate = True
            break
        
        if not is_duplicate:
            filtered.append(util)
    
    return filtered
