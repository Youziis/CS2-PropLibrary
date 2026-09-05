"""
道具关联管理路由
"""
from flask import Blueprint, request, jsonify
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / 'backend'))

from database import Database

bp = Blueprint('relation', __name__)
db = Database()


@bp.route('/api/relations/add', methods=['POST'])
def add_relation():
    """添加单个关联关系"""
    data = request.get_json()
    
    utility_hash = data.get('utility_hash')
    related_hash = data.get('related_hash')
    bidirectional = data.get('bidirectional', True)
    combo_group = data.get('combo_group')
    combo_order = data.get('combo_order')
    
    if not utility_hash or not related_hash:
        return jsonify({'error': '缺少必需参数'}), 400
    
    success = db.add_utility_relation(
        utility_hash, 
        related_hash, 
        bidirectional, 
        combo_group, 
        combo_order
    )
    
    if success:
        return jsonify({'message': '关联添加成功'}), 200
    else:
        return jsonify({'error': '关联添加失败'}), 500


@bp.route('/api/relations/remove', methods=['POST'])
def remove_relation():
    """移除关联关系"""
    data = request.get_json()
    
    utility_hash = data.get('utility_hash')
    related_hash = data.get('related_hash')
    bidirectional = data.get('bidirectional', True)
    
    if not utility_hash or not related_hash:
        return jsonify({'error': '缺少必需参数'}), 400
    
    success = db.remove_utility_relation(utility_hash, related_hash, bidirectional)
    
    if success:
        return jsonify({'message': '关联移除成功'}), 200
    else:
        return jsonify({'error': '关联移除失败'}), 500


@bp.route('/api/relations/get/<hash>', methods=['GET'])
def get_relations(hash):
    """获取道具的所有关联（支持完整hash或前8位hash）"""
    try:
        utility = None
        
        # 先尝试完整hash查询
        try:
            utility = db.get_utility_by_hash(hash)
        except:
            pass
        
        # 如果没找到，尝试模糊查询（支持前缀匹配）
        if not utility:
            with db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM utilities 
                    WHERE hash LIKE ? 
                    AND status = 'exported'
                    ORDER BY hash
                    LIMIT 1
                """, (hash + '%',))
                row = cursor.fetchone()
                if row:
                    # 手动解析行数据
                    utility = dict(row)
                    # 解析JSON字段
                    import json
                    for field in ['throw_position', 'throw_angles', 'land_position']:
                        if utility.get(field):
                            try:
                                utility[field] = json.loads(utility[field])
                            except:
                                pass
                    if utility.get('tags'):
                        try:
                            utility['tags'] = json.loads(utility['tags'])
                        except:
                            utility['tags'] = []
                    else:
                        utility['tags'] = []
        
        if not utility:
            return jsonify({'error': '未找到道具'}), 404
        
        # 使用找到的完整hash获取关联信息
        actual_hash = utility['hash']
        
        # 获取关联道具列表
        related = db.get_related_utilities(actual_hash)
        
        # 获取关联数量
        count = db.get_relation_count(actual_hash)
        
        return jsonify({
            'utility': utility,
            'related_utilities': related,
            'count': count
        }), 200
    except Exception as e:
        import traceback
        print(f"查询出错: {e}")
        print(traceback.format_exc())
        return jsonify({'error': f'查询失败: {str(e)}'}), 500


@bp.route('/api/relations/batch-link', methods=['POST'])
def batch_link():
    """批量关联多个道具"""
    data = request.get_json()
    
    utility_hashes = data.get('utility_hashes', [])
    combo_group = data.get('combo_group')
    
    if not utility_hashes or len(utility_hashes) < 2:
        return jsonify({'error': '至少需要2个道具进行关联'}), 400
    
    count = db.batch_link_utilities(utility_hashes, combo_group)
    
    return jsonify({
        'message': f'成功创建 {count} 个关联',
        'count': count
    }), 200


@bp.route('/api/relations/combo/<group_id>', methods=['GET'])
def get_combo(group_id):
    """获取组合道具"""
    try:
        utilities = db.get_combo_utilities(group_id)
        
        return jsonify({
            'combo_group': group_id,
            'utilities': utilities,
            'count': len(utilities)
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/api/relations/clear/<hash>', methods=['POST'])
def clear_relations(hash):
    """清空道具的所有关联"""
    try:
        success = db.clear_all_relations(hash)
        
        if success:
            return jsonify({'message': '关联已清空'}), 200
        else:
            return jsonify({'error': '清空失败'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/api/relations/stats', methods=['GET'])
def get_relation_stats():
    """获取关联统计信息"""
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            # 总关联数
            cursor.execute("SELECT COUNT(*) as count FROM utility_relations")
            total = cursor.fetchone()['count']
            
            # 有关联的道具数量
            cursor.execute("""
                SELECT COUNT(DISTINCT utility_hash) as count 
                FROM utility_relations
            """)
            linked_utilities = cursor.fetchone()['count']
            
            # 组合数量
            cursor.execute("""
                SELECT COUNT(DISTINCT combo_group) as count 
                FROM utility_relations 
                WHERE combo_group IS NOT NULL
            """)
            combo_groups = cursor.fetchone()['count']
            
            return jsonify({
                'total_relations': total,
                'linked_utilities': linked_utilities,
                'combo_groups': combo_groups
            }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
