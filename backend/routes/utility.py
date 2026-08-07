"""
道具管理路由（CRUD）
"""
import sys
from pathlib import Path
from flask import Blueprint, request, jsonify
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.database import Database

bp = Blueprint('utility', __name__)
db = Database()


@bp.route('/api/utilities', methods=['GET'])
def get_utilities():
    """
    获取道具列表
    参数：
    - status: 状态筛选
    - map: 地图筛选
    - limit: 限制数量
    - offset: 偏移量
    """
    status = request.args.get('status')
    map_name = request.args.get('map')
    limit = request.args.get('limit', type=int)
    offset = request.args.get('offset', default=0, type=int)
    
    utilities = db.get_utilities(
        status=status,
        map_name=map_name,
        limit=limit,
        offset=offset
    )
    
    return jsonify({'utilities': utilities, 'count': len(utilities)})


@bp.route('/api/all_pending', methods=['GET'])
def get_all_pending():
    """获取所有待选择的道具（用于选择道具页面）"""
    utilities = db.get_utilities(status='parsed')
    return jsonify({'utilities': utilities})


@bp.route('/api/pending', methods=['GET'])
def get_pending():
    """获取待审核的道具（已截图）"""
    utilities = db.get_utilities(status='screenshotted')
    return jsonify({'utilities': utilities})


@bp.route('/api/utilities/select', methods=['POST'])
def select_utilities():
    """
    选择道具进行截图
    Body: { "utilities": [...] }
    """
    data = request.json
    utilities = data.get('utilities', [])
    
    if not utilities:
        return jsonify({'success': False, 'message': '未选择道具'}), 400
    
    # 更新状态为 selected
    count = 0
    for util in utilities:
        if db.update_status(util['hash'], 'selected'):
            count += 1
    
    # 统计选中的地图
    maps = set(u['map'] for u in utilities)
    map_counts = {}
    for util in utilities:
        map_name = util['map']
        map_counts[map_name] = map_counts.get(map_name, 0) + 1
    
    map_info = ', '.join([f"{m}({c}个)" for m, c in map_counts.items()])
    
    # 🆕 自动导出到JSON文件供截图脚本使用
    import json
    selected_utils = db.get_utilities(status='selected')
    output_path = Path(__file__).parent.parent.parent / 'output' / 'commands' / 'selected_for_screenshot.json'
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(selected_utils, f, ensure_ascii=False, indent=2)
    
    return jsonify({
        'success': True,
        'message': f'已选择 {count} 个道具并导出到JSON\n地图: {map_info}\n\n💡 提示: 现在可以直接运行截图脚本',
        'count': count,
        'maps': list(maps),
        'json_exported': True
    })


@bp.route('/api/utilities/<hash>/approve', methods=['POST'])
def approve_utility(hash):
    """批准道具"""
    data = request.json
    
    success = db.update_status(
        hash,
        'approved',
        display_name=data.get('display_name'),
        notes=data.get('notes'),
        approved_time=datetime.now().isoformat()
    )
    
    if success:
        return jsonify({'success': True, 'message': '批准成功'})
    else:
        return jsonify({'success': False, 'message': '道具未找到'}), 404


@bp.route('/api/utilities/<hash>/reject', methods=['POST'])
def reject_utility(hash):
    """拒绝道具"""
    success = db.update_status(hash, 'rejected')
    
    if success:
        return jsonify({'success': True, 'message': '已拒绝'})
    else:
        return jsonify({'success': False, 'message': '道具未找到'}), 404


@bp.route('/api/utilities/<hash>', methods=['DELETE'])
def delete_utility(hash):
    """删除道具"""
    success = db.delete_utility(hash)
    
    if success:
        return jsonify({'success': True, 'message': '已删除'})
    else:
        return jsonify({'success': False, 'message': '道具未找到'}), 404


@bp.route('/api/utilities/<hash>/unapprove', methods=['POST'])
def unapprove_utility(hash):
    """撤销批准（移回待审核）"""
    success = db.update_status(hash, 'screenshotted')
    
    if success:
        return jsonify({'success': True, 'message': '已撤销批准'})
    else:
        return jsonify({'success': False, 'message': '道具未找到'}), 404


@bp.route('/api/utilities/<hash>/edit', methods=['POST'])
def edit_utility(hash):
    """编辑道具信息"""
    data = request.json
    
    fields = {}
    if 'display_name' in data:
        fields['display_name'] = data['display_name']
    if 'notes' in data:
        fields['notes'] = data['notes']
    
    success = db.update_utility(hash, fields)
    
    if success:
        return jsonify({'success': True, 'message': '更新成功'})
    else:
        return jsonify({'success': False, 'message': '道具未找到'}), 404
