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


@bp.route('/api/relations/search', methods=['GET'])
def search_utilities():
    """搜索道具（支持hash或名称）"""
    query = request.args.get('q', '').strip()
    
    if not query:
        return jsonify({'error': '搜索关键词不能为空'}), 400
    
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            # 先尝试按hash前缀搜索
            cursor.execute("""
                SELECT * FROM utilities 
                WHERE hash LIKE ? 
                AND status = 'exported'
                LIMIT 10
            """, (query + '%',))
            
            results = cursor.fetchall()
            
            # 如果没找到，尝试按名称模糊搜索
            if not results:
                cursor.execute("""
                    SELECT * FROM utilities 
                    WHERE (display_name LIKE ? OR display_name LIKE ?)
                    AND status = 'exported'
                    LIMIT 10
                """, ('%' + query + '%', query + '%'))
                results = cursor.fetchall()
            
            if not results:
                return jsonify({'error': '未找到匹配的道具'}), 404
            
            # 解析结果
            import json
            utilities = []
            for row in results:
                utility = dict(row)
                # 解析JSON字段
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
                utilities.append(utility)
            
            return jsonify({
                'utilities': utilities,
                'count': len(utilities)
            }), 200
            
    except Exception as e:
        import traceback
        print(f"搜索出错: {e}")
        print(traceback.format_exc())
        return jsonify({'error': f'搜索失败: {str(e)}'}), 500


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


@bp.route('/api/relations/groups', methods=['GET'])
def get_all_groups():
    """获取所有关联组"""
    try:
        import json
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            groups = []
            
            # 获取所有有组名的关联组
            cursor.execute("""
                SELECT DISTINCT combo_group 
                FROM utility_relations 
                WHERE combo_group IS NOT NULL
                ORDER BY combo_group
            """)
            
            for row in cursor.fetchall():
                combo_group = row['combo_group']
                
                # 获取该组的所有道具
                cursor.execute("""
                    SELECT DISTINCT u.*, ur.combo_order
                    FROM utility_relations ur
                    JOIN utilities u ON ur.utility_hash = u.hash
                    WHERE ur.combo_group = ?
                    ORDER BY ur.combo_order, u.hash
                """, (combo_group,))
                
                utilities = []
                for u_row in cursor.fetchall():
                    utility = dict(u_row)
                    # 解析JSON字段
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
                    utilities.append(utility)
                
                groups.append({
                    'combo_group': combo_group,
                    'utilities': utilities,
                    'count': len(utilities)
                })
            
            # 获取没有组名的关联（按第一个hash分组）
            cursor.execute("""
                SELECT DISTINCT utility_hash
                FROM utility_relations
                WHERE combo_group IS NULL
            """)
            
            for row in cursor.fetchall():
                hash_value = row['utility_hash']
                
                # 获取该hash的所有关联道具（去重）
                related_hashes = set()
                cursor.execute("""
                    SELECT related_hash FROM utility_relations 
                    WHERE utility_hash = ? AND combo_group IS NULL
                """, (hash_value,))
                
                for r in cursor.fetchall():
                    related_hashes.add(r['related_hash'])
                
                # 加上自己
                related_hashes.add(hash_value)
                
                # 如果这个组已经被添加过（从反向关联），跳过
                skip = False
                for existing_group in groups:
                    if existing_group.get('combo_group') is None:
                        existing_hashes = {u['hash'] for u in existing_group['utilities']}
                        if related_hashes == existing_hashes:
                            skip = True
                            break
                
                if skip:
                    continue
                
                # 获取所有道具详情
                utilities = []
                for h in sorted(related_hashes):
                    cursor.execute("SELECT * FROM utilities WHERE hash = ?", (h,))
                    u_row = cursor.fetchone()
                    if u_row:
                        utility = dict(u_row)
                        # 解析JSON字段
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
                        utilities.append(utility)
                
                if utilities:
                    groups.append({
                        'combo_group': None,
                        'utilities': utilities,
                        'count': len(utilities)
                    })
            
            return jsonify({
                'groups': groups,
                'count': len(groups)
            }), 200
            
    except Exception as e:
        import traceback
        print(f"获取关联组出错: {e}")
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500
