"""
导出路由

实际的导出动作（图片处理、地图 JSON、索引）在 backend/export_service.py，
这里只负责取数、更新状态和拼装响应。
"""
import sys
from pathlib import Path
from datetime import datetime
from flask import Blueprint, jsonify

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.database import Database
from backend.export_service import export_utilities_to_public

bp = Blueprint('export', __name__)
db = Database()


@bp.route('/api/export', methods=['POST'])
def export_utilities():
    """导出已批准的道具到用户端（没有待导出的则重新导出已导出的道具）"""
    try:
        approved = db.get_utilities(status='approved')

        if approved:
            utilities_to_export = approved
            is_reexport = False
        else:
            utilities_to_export = db.get_utilities(status='exported')

            if not utilities_to_export:
                return jsonify({'success': False, 'message': '没有可导出的道具（既没有待导出，也没有已导出的道具）'}), 400

            is_reexport = True

        counts = export_utilities_to_public(db, utilities_to_export)
        total_exported = sum(c['processed'] for c in counts.values())

        # 只有正常导出才把 approved 改成 exported；重新导出不改状态
        if not is_reexport:
            exported_time = datetime.now().isoformat()
            for util in utilities_to_export:
                db.update_status(util['hash'], 'exported', exported_time=exported_time)

        exported_maps = [
            {
                'name': map_name,
                'display_name': map_name.replace('de_', '').title(),
                'utility_count': counts[map_name]['merged'],
                'data_file': f"data/{map_name}.json"
            }
            for map_name in counts
        ]

        if is_reexport:
            message = f'重新导出成功！共重新导出 {total_exported} 个已导出道具'
        else:
            message = f'导出成功！共导出 {total_exported} 个新道具'

        return jsonify({
            'success': True,
            'message': message,
            'total': total_exported,
            'maps': exported_maps,
            'is_reexport': is_reexport
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


def trigger_export_for_map(map_name: str) -> dict:
    """
    触发单个地图的导出（编辑道具后的自动导出用）
    只导出指定地图的 approved 和 exported 道具

    Returns:
        dict: {'success': bool, 'message': str, 'count': int} 或 {'success': False, 'error': str}
    """
    try:
        approved = db.get_utilities(status='approved', map_name=map_name)
        exported = db.get_utilities(status='exported', map_name=map_name)
        utilities_to_export = approved + exported

        if not utilities_to_export:
            return {'success': False, 'error': f'地图 {map_name} 没有可导出的道具'}

        counts = export_utilities_to_public(db, utilities_to_export)
        processed = counts.get(map_name, {}).get('processed', 0)

        exported_time = datetime.now().isoformat()
        for util in approved:
            db.update_status(util['hash'], 'exported', exported_time=exported_time)

        return {
            'success': True,
            'message': f'成功导出地图 {map_name} 的 {processed} 个道具',
            'count': processed
        }

    except Exception as e:
        import traceback
        print(f"[错误] 单地图导出失败: {e}")
        traceback.print_exc()
        return {'success': False, 'error': str(e)}
