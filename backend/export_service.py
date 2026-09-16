"""
导出服务

把已批准 / 已导出的道具写入 public/：
- 图片处理（准星图裁剪中心区域，站位图与落点图压缩）
- 合并写 public/data/<map>.json
- 刷新 public/data/utilities.json 索引

后台的 /api/export、单地图自动导出（trigger_export_for_map）以及命令行
client/export.py 都调用这里的实现，避免多份导出逻辑各自漂移。
"""
import json
from datetime import datetime
from pathlib import Path

from PIL import Image

PROJECT_ROOT = Path(__file__).parent.parent
DEFAULT_PUBLIC_DIR = PROJECT_ROOT / 'public'
DEFAULT_SCREENSHOTS_DIR = PROJECT_ROOT / 'output' / 'screenshots'

SHOT_TYPES = ('position', 'crosshair', 'landing')
INDEX_FILE_NAME = 'utilities.json'


def process_and_save_image(src_path, dest_path, shot_type, max_size=(1200, 900), quality=75):
    """
    处理并保存图片
    - crosshair（准星图）: 裁剪中心区域，保留准星周围
    - position/landing（站位图/落点图）: 压缩质量以减小文件大小
    """
    try:
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        img = Image.open(src_path)

        if shot_type == 'crosshair':
            width, height = img.size
            crop_width = int(width * 0.4)
            crop_height = int(height * 0.5)
            left = (width - crop_width) // 2
            top = (height - crop_height) // 2
            img = img.crop((left, top, left + crop_width, top + crop_height))
            img.save(dest_path, 'JPEG', quality=85, optimize=True)
        else:
            if img.width > max_size[0] or img.height > max_size[1]:
                img.thumbnail(max_size, Image.Resampling.LANCZOS)
            img.save(dest_path, 'JPEG', quality=quality, optimize=True)

        return True

    except Exception as e:
        print(f"[错误] 处理图片失败 ({shot_type}): {e}")
        import traceback
        traceback.print_exc()
        return False


def build_utility_entry(util, map_name, combo_group=None):
    """生成 public/data/<map>.json 里的一条道具数据"""
    util_type = util['type']
    util_hash = util['hash'][:8]
    utility_id = f"{map_name}_{util_type}_{util_hash}"

    return {
        'id': utility_id,
        'sort_id': util.get('sort_id'),
        'hash': util['hash'],
        'type': util_type,
        'team': util.get('team', 'Unknown'),
        'name': util.get('display_name', f'{util_type}_{util_hash}'),
        'position': util.get('throw_position', {}),
        'angles': util.get('throw_angles', {}),
        'land_position': util.get('land_position', {}),
        'throw_type': util.get('throw_type', 'unknown'),
        'flight_time': round(util.get('flight_time', 0), 2),
        'distance': round(util.get('distance', 0), 1),
        'command': f"setpos {util['throw_position']['x']:.2f} {util['throw_position']['y']:.2f} {util['throw_position']['z']:.2f}; setang {util['throw_angles']['pitch']:.2f} {util['throw_angles']['yaw']:.2f} 0",
        'tags': util.get('tags', []),
        'combo_group': combo_group,
        'notes': util.get('notes', ''),
        'screenshots': {
            'position': f"images/{map_name}/{util_type}/{utility_id}_position.jpg",
            'crosshair': f"images/{map_name}/{util_type}/{utility_id}_crosshair.jpg",
            'landing': f"images/{map_name}/{util_type}/{utility_id}_landing.jpg"
        },
        'thrower': util.get('thrower'),
        'demo_source': util.get('source_demo')
    }


def _read_json(path, default=None):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return default


def _combo_group_of(db, utility_hash):
    """查询道具所属的组合组名（没有则返回 None）"""
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT DISTINCT combo_group
                FROM utility_relations
                WHERE utility_hash = ? AND combo_group IS NOT NULL
                LIMIT 1
            """, (utility_hash,))
            row = cursor.fetchone()
            return row['combo_group'] if row and row['combo_group'] else None
    except Exception as e:
        print(f"[警告] 查询组合信息失败: {e}")
        return None


def export_map(db, map_name, utilities, public_dir=None, screenshots_dir=None,
               assign_sort_id=True):
    """
    导出单个地图的道具
    返回: (处理条数, 合并后该地图的总条数)
    """
    public_dir = Path(public_dir) if public_dir else DEFAULT_PUBLIC_DIR
    screenshots_dir = Path(screenshots_dir) if screenshots_dir else DEFAULT_SCREENSHOTS_DIR

    # 没有 sort_id 的道具在导出时分配（保证前端展示顺序稳定）
    if assign_sort_id:
        for util in utilities:
            if not util.get('sort_id'):
                sort_id = db._get_next_sort_id(map_name)
                db.update_utility(util['hash'], {'sort_id': sort_id})
                util['sort_id'] = sort_id

    entries = []
    for util in utilities:
        util_type = util['type']
        utility_id = f"{map_name}_{util_type}_{util['hash'][:8]}"
        screenshot_base = util.get('screenshot_filename_base') or f"{map_name}_{util['hash']}"

        for shot_type in SHOT_TYPES:
            src_file = screenshots_dir / f"{screenshot_base}_{shot_type}.jpg"
            if not src_file.exists():
                continue

            dest_dir = public_dir / 'images' / map_name / util_type
            dest_dir.mkdir(parents=True, exist_ok=True)
            process_and_save_image(src_file, dest_dir / f"{utility_id}_{shot_type}.jpg", shot_type)

        entries.append(build_utility_entry(util, map_name, _combo_group_of(db, util['hash'])))

    # 合并已有数据：同 hash 覆盖，其余保留
    map_data_file = public_dir / 'data' / f"{map_name}.json"
    map_data_file.parent.mkdir(parents=True, exist_ok=True)

    existing_data = _read_json(map_data_file, {}) or {}
    existing_utilities = existing_data.get('utilities', []) or []

    new_hashes = {entry['hash'] for entry in entries}
    merged = [u for u in existing_utilities if u.get('hash') not in new_hashes]
    merged.extend(entries)
    merged.sort(key=lambda u: u.get('sort_id', 999999))

    with open(map_data_file, 'w', encoding='utf-8') as f:
        json.dump({
            'map': map_name,
            'utilities': merged
        }, f, ensure_ascii=False, indent=2)

    return len(entries), len(merged)


def update_index(public_dir, map_counts):
    """
    刷新 public/data/utilities.json
    只更新本次涉及的地图，其余地图的索引信息保持不变
    """
    public_dir = Path(public_dir) if public_dir else DEFAULT_PUBLIC_DIR
    index_file = public_dir / 'data' / INDEX_FILE_NAME
    index_file.parent.mkdir(parents=True, exist_ok=True)

    existing_data = _read_json(index_file, {}) or {}
    existing_maps = {m['name']: m for m in existing_data.get('maps', []) if m.get('name')}

    for map_name, count in map_counts.items():
        existing_maps[map_name] = {
            'name': map_name,
            'display_name': map_name.replace('de_', '').title(),
            'utility_count': count,
            'data_file': f"data/{map_name}.json"
        }

    all_maps = sorted(existing_maps.values(), key=lambda x: x['name'])
    total_in_index = sum(m.get('utility_count', 0) for m in all_maps)

    with open(index_file, 'w', encoding='utf-8') as f:
        json.dump({
            'version': '1.0.0',
            'last_updated': datetime.now().isoformat(),
            'maps': all_maps,
            'statistics': {
                'total_utilities': total_in_index,
                'by_type': {}
            }
        }, f, ensure_ascii=False, indent=2)


def export_utilities_to_public(db, utilities, public_dir=None, screenshots_dir=None,
                               assign_sort_id=True):
    """
    把一批道具导出到 public/（按地图分组）
    返回: {map_name: {'processed': 处理条数, 'merged': 合并后总数}}
    """
    by_map = {}
    for util in utilities:
        by_map.setdefault(util['map'], []).append(util)

    result = {}
    for map_name, map_utilities in by_map.items():
        processed, merged = export_map(
            db, map_name, map_utilities,
            public_dir=public_dir,
            screenshots_dir=screenshots_dir,
            assign_sort_id=assign_sort_id
        )
        result[map_name] = {'processed': processed, 'merged': merged}

    update_index(public_dir, {m: r['merged'] for m, r in result.items()})
    return result
