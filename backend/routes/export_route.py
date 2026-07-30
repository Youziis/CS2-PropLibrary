"""
导出路由
"""
import sys
import json
import shutil
from pathlib import Path
from flask import Blueprint, request, jsonify
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.database import Database

bp = Blueprint('export', __name__)
db = Database()


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
            
            for i, util in enumerate(utilities, 1):
                util_type = util['type']
                utility_id = f"{map_name}_{util_type}_{i:03d}"
                
                # 复制截图
                screenshot_base = util.get('screenshot_filename_base') or f"{map_name}_unknown_{util.get('screenshot_id', 'util000')}"
                
                for shot_type in ['position', 'crosshair', 'landing']:
                    src_file = screenshots_dir / f"{screenshot_base}_{shot_type}.jpg"
                    
                    if src_file.exists():
                        dest_dir = public_dir / 'images' / map_name / util_type
                        dest_dir.mkdir(parents=True, exist_ok=True)
                        dest_file = dest_dir / f"{utility_id}_{shot_type}.jpg"
                        
                        shutil.copy2(src_file, dest_file)
                
                # 生成道具数据
                map_utilities.append({
                    'id': utility_id,
                    'type': util_type,
                    'team': util.get('team', 'Unknown'),
                    'name': util.get('display_name', f'{util_type}_{i}'),
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
        
        # 生成索引文件
        index_file = public_dir / 'data' / 'utilities.json'
        with open(index_file, 'w', encoding='utf-8') as f:
            json.dump({
                'version': '1.0.0',
                'last_updated': datetime.now().isoformat(),
                'maps': exported_maps,
                'statistics': {
                    'total_utilities': total_exported,
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
