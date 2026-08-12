"""
导出路由
"""
import sys
import json
import shutil
import os
from pathlib import Path
from flask import Blueprint, request, jsonify
from datetime import datetime
from PIL import Image

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.database import Database

bp = Blueprint('export', __name__)
db = Database()


def process_and_save_image(src_path, dest_path, shot_type, max_size=(1200, 900), quality=75):
    """
    处理并保存图片
    - crosshair（准星图）: 裁剪中心区域，保留准星周围
    - position/landing（站位图/落点图）: 压缩质量以减小文件大小
    """
    try:
        # 创建目标目录
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 打开图片
        img = Image.open(src_path)
        
        if shot_type == 'crosshair':
            # 准星图：裁剪中心区域
            width, height = img.size
            
            # 裁剪尺寸：宽度的40%，高度的50%
            crop_width = int(width * 0.4)
            crop_height = int(height * 0.5)
            
            # 计算裁剪区域（中心区域）
            left = (width - crop_width) // 2
            top = (height - crop_height) // 2
            right = left + crop_width
            bottom = top + crop_height
            
            # 裁剪图片
            img = img.crop((left, top, right, bottom))
            
            # 保存裁剪后的图片，使用较高质量
            img.save(dest_path, 'JPEG', quality=85, optimize=True)
            
        else:
            # 站位图和落点图：压缩质量
            # 如果图片太大，先缩小尺寸
            if img.width > max_size[0] or img.height > max_size[1]:
                img.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            # 保存压缩后的图片
            img.save(dest_path, 'JPEG', quality=quality, optimize=True)
        
        return True
        
    except Exception as e:
        print(f"[错误] 处理图片失败 ({shot_type}): {e}")
        import traceback
        traceback.print_exc()
        return False


@bp.route('/api/export', methods=['POST'])
def export_utilities():
    """导出已批准的道具到用户端"""
    try:
        # 获取已批准的道具
        approved = db.get_utilities(status='approved')
        
        if not approved:
            return jsonify({'success': False, 'message': '没有待导出的道具'}), 400
        
        # 项目根目录
        root_dir = Path(__file__).parent.parent.parent
        public_dir = root_dir / 'public'
        screenshots_dir = root_dir / 'output' / 'screenshots'
        
        # 按地图分组
        by_map = {}
        for util in approved:
            map_name = util['map']
            if map_name not in by_map:
                by_map[map_name] = []
            by_map[map_name].append(util)
        
        # 导出每个地图
        exported_maps = []
        total_exported = 0
        
        for map_name, utilities in by_map.items():
            # 生成地图数据
            map_utilities = []
            
            for util in utilities:
                util_type = util['type']
                util_hash = util['hash'][:8]  # 使用hash的前8位作为唯一标识
                utility_id = f"{map_name}_{util_type}_{util_hash}"
                
                # 复制并处理截图
                screenshot_base = util.get('screenshot_filename_base') or f"{map_name}_{util['hash']}"
                
                for shot_type in ['position', 'crosshair', 'landing']:
                    src_file = screenshots_dir / f"{screenshot_base}_{shot_type}.jpg"
                    
                    if src_file.exists():
                        dest_dir = public_dir / 'images' / map_name / util_type
                        dest_dir.mkdir(parents=True, exist_ok=True)
                        dest_file = dest_dir / f"{utility_id}_{shot_type}.jpg"
                        
                        # 使用图片处理函数（压缩和裁剪）
                        process_and_save_image(src_file, dest_file, shot_type)
                
                # 生成道具数据
                map_utilities.append({
                    'id': utility_id,
                    'type': util_type,
                    'team': util.get('team', 'Unknown'),
                    'name': util.get('display_name', f'{util_type}_{util_hash}'),
                    'description': f"{util.get('throw_type', '投掷')}，飞行时间 {util.get('flight_time', 0):.1f} 秒",
                    'position': util.get('throw_position', {}),
                    'angles': util.get('throw_angles', {}),
                    'land_position': util.get('land_position', {}),
                    'throw_type': util.get('throw_type', 'unknown'),
                    'flight_time': round(util.get('flight_time', 0), 2),
                    'distance': round(util.get('distance', 0), 1),
                    'command': f"setpos {util['throw_position']['x']:.2f} {util['throw_position']['y']:.2f} {util['throw_position']['z']:.2f}; setang {util['throw_angles']['pitch']:.2f} {util['throw_angles']['yaw']:.2f} 0",
                    'quality': 3,
                    'tags': [],
                    'notes': util.get('notes', ''),
                    'screenshots': {
                        'position': f"images/{map_name}/{util_type}/{utility_id}_position.jpg",
                        'crosshair': f"images/{map_name}/{util_type}/{utility_id}_crosshair.jpg",
                        'landing': f"images/{map_name}/{util_type}/{utility_id}_landing.jpg"
                    },
                    'thrower': util.get('thrower'),
                    'demo_source': util.get('source_demo')
                })
            
            # 保存地图数据
            map_data_file = public_dir / 'data' / f"{map_name}.json"
            map_data_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(map_data_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'map': map_name,
                    'utilities': map_utilities
                }, f, ensure_ascii=False, indent=2)
            
            exported_maps.append({
                'name': map_name,
                'display_name': map_name.replace('de_', '').title(),
                'utility_count': len(map_utilities),
                'data_file': f"data/{map_name}.json"
            })
            
            total_exported += len(map_utilities)
        
        # 生成索引文件（合并已有数据）
        index_file = public_dir / 'data' / 'utilities.json'
        
        # 读取现有索引（如果存在）
        existing_maps = {}
        if index_file.exists():
            try:
                with open(index_file, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
                    # 将现有地图转换为字典，便于更新
                    for map_info in existing_data.get('maps', []):
                        existing_maps[map_info['name']] = map_info
            except:
                pass
        
        # 更新或添加本次导出的地图
        for map_info in exported_maps:
            existing_maps[map_info['name']] = map_info
        
        # 转换回列表并排序
        all_maps = sorted(existing_maps.values(), key=lambda x: x['name'])
        
        # 计算总数
        total_in_index = sum(m['utility_count'] for m in all_maps)
        
        # 保存合并后的索引
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
        
        # 更新数据库状态为 exported
        for util in approved:
            db.update_status(
                util['hash'],
                'exported',
                exported_time=datetime.now().isoformat()
            )
        
        return jsonify({
            'success': True,
            'message': f'导出成功！共导出 {total_exported} 个道具',
            'total': total_exported,
            'maps': exported_maps
        })
        
    except Exception as e:
        print(f"[错误] 导出失败: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'导出失败: {str(e)}'}), 500


@bp.route('/api/export/approved', methods=['GET'])
def get_approved():
    """获取已批准待导出的道具"""
    utilities = db.get_utilities(status='approved')
    return jsonify({'utilities': utilities, 'count': len(utilities)})


@bp.route('/api/export/exported', methods=['GET'])
def get_exported():
    """获取已导出的道具"""
    utilities = db.get_utilities(status='exported')
    return jsonify({'utilities': utilities, 'count': len(utilities)})
