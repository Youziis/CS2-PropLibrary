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
    """获取所有待选择的道具（用于选择道具页面）- 包含parsed、selected和rejected状态"""
    # 获取parsed状态的道具（待选择）
    parsed_utilities = db.get_utilities(status='parsed')
    
    # 获取selected状态的道具（已选择但未截图）
    selected_utilities = db.get_utilities(status='selected')
    
    # 获取rejected状态的道具（已拒绝，可重新选择）
    rejected_utilities = db.get_utilities(status='rejected')
    
    # 合并三种状态的道具
    all_utilities = parsed_utilities + selected_utilities + rejected_utilities
    
    return jsonify({
        'utilities': all_utilities,
        'success': True
    })


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


@bp.route('/api/update_utility', methods=['POST'])
def update_utility_full():
    """完整更新道具信息（用于编辑页面）"""
    try:
        # 获取表单数据
        hash_val = request.form.get('hash')
        auto_export = request.form.get('auto_export', 'true').lower() == 'true'  # 默认开启自动导出
        
        print(f"[调试] 开始更新道具: {hash_val}, 自动导出: {auto_export}")
        
        if not hash_val:
            return jsonify({'success': False, 'error': '缺少道具hash'}), 400
        
        # 获取道具信息以确定状态
        utility = db.get_utility_by_hash(hash_val)
        if not utility:
            return jsonify({'success': False, 'error': '道具未找到'}), 404
        
        # 准备更新字段
        fields = {}
        
        if request.form.get('name'):
            fields['display_name'] = request.form.get('name')
        if request.form.get('type'):
            fields['type'] = request.form.get('type')
        if request.form.get('team'):
            fields['team'] = request.form.get('team')
        if request.form.get('throw_type'):
            fields['throw_type'] = request.form.get('throw_type')
        if request.form.get('notes'):
            fields['notes'] = request.form.get('notes')
        
        # 处理标签（使用新的多表系统）
        # 即使标签为空，也要调用set_utility_tags清空旧标签
        tags_str = request.form.get('tags', '')
        print(f"[调试] 标签字符串: '{tags_str}'")
        
        if tags_str.strip():
            # 有标签内容
            tag_list = [t.strip() for t in tags_str.split(',') if t.strip()]
        else:
            # 空标签，清空所有标签
            tag_list = []
        
        print(f"[调试] 解析后的标签列表: {tag_list}")
        result = db.set_utility_tags(hash_val, tag_list)
        print(f"[调试] 标签设置结果: {result}")
        
        # 更新基本字段
        if fields:
            success = db.update_utility(hash_val, fields)
            print(f"[调试] 基本字段更新结果: {success}")
        
        # 🔄 如果道具已导出且启用自动导出，触发重新导出
        if auto_export and utility.get('status') in ['exported', 'approved']:
            try:
                from .export_route import trigger_export_for_map
                map_name = utility.get('map')
                print(f"[自动导出] 触发地图 {map_name} 的导出...")
                
                # 调用导出函数（只导出该地图）
                export_result = trigger_export_for_map(map_name)
                
                if export_result.get('success'):
                    print(f"[自动导出] 成功: {export_result.get('message')}")
                    return jsonify({
                        'success': True, 
                        'message': '更新成功并已自动导出',
                        'auto_exported': True
                    })
                else:
                    print(f"[自动导出] 失败: {export_result.get('error')}")
                    return jsonify({
                        'success': True, 
                        'message': '更新成功，但自动导出失败',
                        'auto_exported': False,
                        'export_error': export_result.get('error')
                    })
            except Exception as export_err:
                print(f"[自动导出] 异常: {export_err}")
                return jsonify({
                    'success': True, 
                    'message': '更新成功，但自动导出出错',
                    'auto_exported': False,
                    'export_error': str(export_err)
                })
        
        print(f"[调试] 更新完成")
        return jsonify({'success': True, 'message': '更新成功'})
        
    except Exception as e:
        import traceback
        error_msg = traceback.format_exc()
        print(f"[错误] 更新道具失败: {e}")
        print(error_msg)
        return jsonify({'success': False, 'error': str(e)}), 500
