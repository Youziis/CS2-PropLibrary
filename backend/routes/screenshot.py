"""
截图管理路由
"""
import sys
import json
from pathlib import Path
from flask import Blueprint, request, jsonify

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.database import Database

bp = Blueprint('screenshot', __name__)
db = Database()


@bp.route('/api/screenshot/selected', methods=['GET'])
def get_selected():
    """获取已选择的道具（待截图）"""
    utilities = db.get_utilities(status='selected')
    
    # 按地图分组
    by_map = {}
    for util in utilities:
        map_name = util['map']
        if map_name not in by_map:
            by_map[map_name] = []
        by_map[map_name].append(util)
    
    return jsonify({
        'utilities': utilities,
        'by_map': by_map,
        'total': len(utilities)
    })


@bp.route('/api/screenshot/export_for_script', methods=['GET'])
def export_for_script():
    """
    导出选中道具为 JSON 格式供截图脚本使用
    兼容旧的截图脚本
    """
    utilities = db.get_utilities(status='selected')
    
    # 保存到文件
    output_path = Path(__file__).parent.parent.parent / 'output' / 'commands' / 'selected_for_screenshot.json'
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(utilities, f, ensure_ascii=False, indent=2)
    
    return jsonify({
        'success': True,
        'message': f'已导出 {len(utilities)} 个道具到 {output_path}',
        'count': len(utilities),
        'file': str(output_path)
    })


@bp.route('/api/screenshot/update_from_script', methods=['POST'])
def update_from_script():
    """
    从截图脚本更新道具状态
    截图脚本完成后调用此API更新数据库
    Body: { "utilities": [...] }  # 包含 screenshot_id 的道具列表
    """
    data = request.json
    utilities = data.get('utilities', [])
    
    updated = 0
    for util in utilities:
        if util.get('screenshot_id'):
            success = db.update_status(
                util['hash'],
                'screenshotted',
                screenshot_id=util['screenshot_id'],
                screenshot_filename_base=util.get('screenshot_filename_base')
            )
            if success:
                updated += 1
    
    return jsonify({
        'success': True,
        'message': f'已更新 {updated} 个道具状态',
        'updated': updated
    })


@bp.route('/api/screenshot/clear_selected', methods=['POST'])
def clear_selected():
    """清空已选择的道具列表"""
    utilities = db.get_utilities(status='selected')
    
    count = 0
    for util in utilities:
        if db.update_status(util['hash'], 'parsed'):
            count += 1
    
    return jsonify({
        'success': True,
        'message': f'已清空 {count} 个选中道具',
        'count': count
    })
