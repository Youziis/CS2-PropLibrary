"""
管理后台主程序
使用 Flask + SQLite
"""
import os
import sys
import json
from pathlib import Path
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from database import Database
from routes import demo, utility, screenshot, export_route

# 创建 Flask 应用
app = Flask(__name__, 
            static_folder='../client/admin',
            static_url_path='')
CORS(app)  # 允许跨域

# 初始化数据库
db = Database()

# 注册路由
app.register_blueprint(demo.bp)
app.register_blueprint(utility.bp)
app.register_blueprint(screenshot.bp)
app.register_blueprint(export_route.bp)


@app.route('/')
def index():
    """管理后台首页"""
    return app.send_static_file('index.html')


@app.route('/api/stats')
def get_stats():
    """获取统计信息"""
    stats = db.get_statistics()
    
    return jsonify({
        'total_parsed': stats.get('total', 0),
        'pending_review': stats.get('screenshotted', 0),
        'approved': stats.get('approved', 0) + stats.get('exported', 0),
        'by_map': stats.get('by_map', {}),
        'by_type': stats.get('by_type', {}),
        'by_status': {
            'parsed': stats.get('parsed', 0),
            'selected': stats.get('selected', 0),
            'screenshotted': stats.get('screenshotted', 0),
            'approved': stats.get('approved', 0),
            'exported': stats.get('exported', 0),
            'rejected': stats.get('rejected', 0)
        }
    })


# ============ 兼容旧API的路由 ============

@app.route('/api/approve', methods=['POST'])
def approve_utility_legacy():
    """批准道具（兼容旧API）"""
    data = request.json
    hash_val = data.get('hash')
    info = data.get('info', {})
    
    # 构建要更新的字段
    update_fields = {
        'approved_time': datetime.now().isoformat()
    }
    
    # 添加可选字段
    if 'display_name' in info:
        update_fields['display_name'] = info['display_name']
    if 'notes' in info:
        update_fields['notes'] = info['notes']
    if 'type' in info:
        update_fields['type'] = info['type']
    if 'team' in info:
        update_fields['team'] = info['team']
    if 'throw_type' in info:
        update_fields['throw_type'] = info['throw_type']
    
    success = db.update_status(
        hash_val,
        'approved',
        **update_fields
    )
    
    if success:
        return jsonify({'success': True, 'message': '批准成功'})
    else:
        return jsonify({'success': False, 'message': '道具未找到'}), 404


@app.route('/api/reject', methods=['POST'])
def reject_utility_legacy():
    """拒绝道具（兼容旧API）- 删除截图文件但保留数据，同时保存编辑的字段"""
    try:
        data = request.json
        hash_val = data.get('hash')
        info = data.get('info', {})
        
        print(f"[拒绝道具] 开始处理: {hash_val}")
        print(f"[拒绝道具] 接收到的info: {info}")
        
        # 获取道具信息以找到截图文件
        utility = db.get_utility_by_hash(hash_val)
        
        if not utility:
            print(f"[拒绝道具] 错误: 道具未找到")
            return jsonify({'success': False, 'message': '道具未找到'}), 404
        
        print(f"[拒绝道具] 找到道具，当前状态: {utility.get('status')}")
        
        # 删除截图文件
        screenshot_base = utility.get('screenshot_filename_base')
        deleted_count = 0
        
        if screenshot_base:
            print(f"[拒绝道具] 截图文件前缀: {screenshot_base}")
            screenshots_dir = Path(__file__).parent.parent / 'output' / 'screenshots'
            screenshot_files = [
                f"{screenshot_base}_position.jpg",
                f"{screenshot_base}_crosshair.jpg",
                f"{screenshot_base}_landing.jpg"
            ]
            
            for filename in screenshot_files:
                filepath = screenshots_dir / filename
                if filepath.exists():
                    try:
                        filepath.unlink()
                        deleted_count += 1
                        print(f"[拒绝道具] 已删除: {filename}")
                    except Exception as e:
                        print(f"[拒绝道具] 删除失败 {filename}: {e}")
                else:
                    print(f"[拒绝道具] 文件不存在: {filename}")
            
            print(f"[拒绝道具] 共删除 {deleted_count} 个截图文件")
        else:
            print(f"[拒绝道具] 警告: 没有截图文件前缀")
        
        # 构建要更新的字段（包括用户编辑的信息）
        update_fields = {
            'screenshot_filename_base': None
        }
        
        # 添加可选的编辑字段
        if 'display_name' in info and info['display_name']:
            update_fields['display_name'] = info['display_name']
            print(f"[拒绝道具] 保存道具名称: {info['display_name']}")
        if 'notes' in info and info['notes']:
            update_fields['notes'] = info['notes']
            print(f"[拒绝道具] 保存备注: {info['notes']}")
        if 'type' in info and info['type']:
            update_fields['type'] = info['type']
            print(f"[拒绝道具] 保存类型: {info['type']}")
        if 'team' in info and info['team']:
            update_fields['team'] = info['team']
            print(f"[拒绝道具] 保存队伍: {info['team']}")
        if 'throw_type' in info and info['throw_type']:
            update_fields['throw_type'] = info['throw_type']
            print(f"[拒绝道具] 保存投掷方式: {info['throw_type']}")
        
        print(f"[拒绝道具] 准备更新的字段: {update_fields}")
        
        # 一次性更新状态、清空截图字段并保存编辑的信息
        print(f"[拒绝道具] 更新数据库...")
        success = db.update_status(
            hash_val, 
            'rejected',
            **update_fields
        )
        
        if success:
            print(f"[拒绝道具] 数据库更新成功")
            
            # 验证更新结果
            updated_utility = db.get_utility_by_hash(hash_val)
            print(f"[拒绝道具] 验证 - 新状态: {updated_utility.get('status')}")
            print(f"[拒绝道具] 验证 - screenshot_filename_base: {updated_utility.get('screenshot_filename_base')}")
            print(f"[拒绝道具] 验证 - display_name: {updated_utility.get('display_name')}")
            print(f"[拒绝道具] 验证 - notes: {updated_utility.get('notes')}")
            
            return jsonify({
                'success': True, 
                'message': f'已拒绝该道具并删除 {deleted_count} 个截图文件'
            })
        else:
            print(f"[拒绝道具] 数据库更新失败")
            return jsonify({'success': False, 'message': '更新数据库失败'}), 500
            
    except Exception as e:
        print(f"[拒绝道具] 异常: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'服务器错误: {str(e)}'}), 500


@app.route('/api/delete_pending', methods=['POST'])
def delete_pending_legacy():
    """删除待审核道具（永久删除，包括截图文件、public文件）"""
    try:
        data = request.json
        hash_val = data.get('hash')
        
        print(f"[删除待审核道具] 开始处理: {hash_val}")
        
        # 获取道具信息以找到截图文件
        utility = db.get_utility_by_hash(hash_val)
        
        if not utility:
            print(f"[删除待审核道具] 错误: 道具未找到")
            return jsonify({'success': False, 'message': '道具未找到'}), 404
        
        print(f"[删除待审核道具] 找到道具，当前状态: {utility.get('status')}")
        
        # 1. 删除 output/screenshots 中的截图文件
        screenshot_base = utility.get('screenshot_filename_base')
        deleted_count = 0
        
        if screenshot_base:
            print(f"[删除待审核道具] 截图文件前缀: {screenshot_base}")
            screenshots_dir = Path(__file__).parent.parent / 'output' / 'screenshots'
            screenshot_files = [
                f"{screenshot_base}_position.jpg",
                f"{screenshot_base}_crosshair.jpg",
                f"{screenshot_base}_landing.jpg"
            ]
            
            for filename in screenshot_files:
                filepath = screenshots_dir / filename
                if filepath.exists():
                    try:
                        filepath.unlink()
                        deleted_count += 1
                        print(f"[删除待审核道具] 已删除output截图: {filename}")
                    except Exception as e:
                        print(f"[删除待审核道具] 删除失败 {filename}: {e}")
        
        # 2. 删除 public/images 中的导出图片（如果已导出）
        map_name = utility.get('map')
        util_type = utility.get('type')
        
        if map_name and util_type:
            # 生成导出的文件名格式：{map}_{type}_{hash[:8]}_*.jpg
            util_hash = hash_val[:8]
            utility_id = f"{map_name}_{util_type}_{util_hash}"
            
            print(f"[删除待审核道具] 道具ID: {utility_id}")
            
            # 删除 public/images/{map}/{type}/ 目录中的文件
            public_images_dir = Path(__file__).parent.parent / 'public' / 'images' / map_name / util_type
            public_screenshot_files = [
                f"{utility_id}_position.jpg",
                f"{utility_id}_crosshair.jpg",
                f"{utility_id}_landing.jpg"
            ]
            
            for filename in public_screenshot_files:
                filepath = public_images_dir / filename
                if filepath.exists():
                    try:
                        filepath.unlink()
                        deleted_count += 1
                        print(f"[删除待审核道具] 已删除public图片: {filename}")
                    except Exception as e:
                        print(f"[删除待审核道具] 删除public图片失败 {filename}: {e}")
        
        # 3. 从 public/data/{map}.json 中删除道具数据（如果已导出）
        if map_name:
            public_data_dir = Path(__file__).parent.parent / 'public' / 'data'
            map_data_file = public_data_dir / f"{map_name}.json"
            
            if map_data_file.exists():
                try:
                    # 读取现有数据
                    with open(map_data_file, 'r', encoding='utf-8') as f:
                        data_content = json.load(f)
                    
                    utilities_list = data_content.get('utilities', [])
                    
                    # 过滤掉要删除的道具（通过hash匹配）
                    original_count = len(utilities_list)
                    utilities_list = [u for u in utilities_list if u.get('hash') != hash_val]
                    removed_count = original_count - len(utilities_list)
                    
                    if removed_count > 0:
                        # 更新数据
                        data_content['utilities'] = utilities_list
                        
                        # 保存更新后的JSON文件
                        with open(map_data_file, 'w', encoding='utf-8') as f:
                            json.dump(data_content, f, ensure_ascii=False, indent=2)
                        
                        print(f"[删除待审核道具] 从{map_name}.json中删除了{removed_count}条数据")
                    else:
                        print(f"[删除待审核道具] {map_name}.json中未找到该道具数据")
                        
                except Exception as e:
                    print(f"[删除待审核道具] 更新public/data失败: {e}")
                    import traceback
                    traceback.print_exc()
        
        # 4. 更新索引文件 utilities.json
        try:
            index_file = Path(__file__).parent.parent / 'public' / 'data' / 'utilities.json'
            if index_file.exists() and map_name:
                with open(index_file, 'r', encoding='utf-8') as f:
                    index_data = json.load(f)
                
                # 更新对应地图的道具数量
                for map_info in index_data.get('maps', []):
                    if map_info['name'] == map_name:
                        # 重新读取地图数据文件获取最新数量
                        map_data_file = Path(__file__).parent.parent / 'public' / 'data' / f"{map_name}.json"
                        if map_data_file.exists():
                            with open(map_data_file, 'r', encoding='utf-8') as f:
                                map_data = json.load(f)
                                map_info['utility_count'] = len(map_data.get('utilities', []))
                        break
                
                # 重新计算总数
                total_count = sum(m.get('utility_count', 0) for m in index_data.get('maps', []))
                if 'statistics' not in index_data:
                    index_data['statistics'] = {}
                index_data['statistics']['total_utilities'] = total_count
                index_data['last_updated'] = datetime.now().isoformat()
                
                # 保存更新后的索引
                with open(index_file, 'w', encoding='utf-8') as f:
                    json.dump(index_data, f, ensure_ascii=False, indent=2)
                
                print(f"[删除待审核道具] 已更新索引文件")
        except Exception as e:
            print(f"[删除待审核道具] 更新索引文件失败: {e}")
        
        # 5. 从数据库中永久删除
        success = db.delete_utility(hash_val)
        
        if success:
            print(f"[删除待审核道具] 数据库删除成功")
            return jsonify({
                'success': True, 
                'message': f'已永久删除该道具（含 {deleted_count} 个文件）'
            })
        else:
            print(f"[删除待审核道具] 数据库删除失败")
            return jsonify({'success': False, 'message': '删除失败'}), 500
            
    except Exception as e:
        print(f"[删除待审核道具] 异常: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'服务器错误: {str(e)}'}), 500


@app.route('/api/delete_approved', methods=['POST'])
def delete_approved_legacy():
    """删除已批准道具（兼容旧API）"""
    data = request.json
    hash_val = data.get('hash')
    
    # 移回待审核状态
    success = db.update_status(hash_val, 'screenshotted')
    
    if success:
        return jsonify({'success': True, 'message': '已移回待审核列表'})
    else:
        return jsonify({'success': False, 'message': '道具未找到'}), 404


@app.route('/api/unexport', methods=['POST'])
def unexport_utility():
    """撤销导出（兼容旧API）"""
    data = request.json
    hash_val = data.get('hash')
    
    # 移回已批准状态
    success = db.update_status(hash_val, 'approved')
    
    if success:
        return jsonify({'success': True, 'message': '已撤销导出'})
    else:
        return jsonify({'success': False, 'message': '道具未找到'}), 404


@app.route('/api/delete_exported', methods=['POST'])
def delete_exported_utility():
    """删除已导出道具（永久删除，包括截图文件、数据库记录和已导出的public文件）"""
    try:
        data = request.json
        hash_val = data.get('hash')
        
        print(f"[删除已导出道具] 开始处理: {hash_val}")
        
        # 获取道具信息以找到截图文件
        utility = db.get_utility_by_hash(hash_val)
        
        if not utility:
            print(f"[删除已导出道具] 错误: 道具未找到")
            return jsonify({'success': False, 'message': '道具未找到'}), 404
        
        print(f"[删除已导出道具] 找到道具，当前状态: {utility.get('status')}")
        
        # 1. 删除 output/screenshots 中的截图文件
        screenshot_base = utility.get('screenshot_filename_base')
        deleted_count = 0
        
        if screenshot_base:
            print(f"[删除已导出道具] 截图文件前缀: {screenshot_base}")
            screenshots_dir = Path(__file__).parent.parent / 'output' / 'screenshots'
            screenshot_files = [
                f"{screenshot_base}_position.jpg",
                f"{screenshot_base}_crosshair.jpg",
                f"{screenshot_base}_landing.jpg"
            ]
            
            for filename in screenshot_files:
                filepath = screenshots_dir / filename
                if filepath.exists():
                    try:
                        filepath.unlink()
                        deleted_count += 1
                        print(f"[删除已导出道具] 已删除output截图: {filename}")
                    except Exception as e:
                        print(f"[删除已导出道具] 删除失败 {filename}: {e}")
        
        # 2. 删除 public/images 中的导出图片
        map_name = utility.get('map')
        util_type = utility.get('type')
        
        if map_name and util_type:
            # 生成导出的文件名格式：{map}_{type}_{hash[:8]}_*.jpg
            util_hash = hash_val[:8]
            utility_id = f"{map_name}_{util_type}_{util_hash}"
            
            print(f"[删除已导出道具] 道具ID: {utility_id}")
            
            # 删除 public/images/{map}/{type}/ 目录中的文件
            public_images_dir = Path(__file__).parent.parent / 'public' / 'images' / map_name / util_type
            public_screenshot_files = [
                f"{utility_id}_position.jpg",
                f"{utility_id}_crosshair.jpg",
                f"{utility_id}_landing.jpg"
            ]
            
            for filename in public_screenshot_files:
                filepath = public_images_dir / filename
                if filepath.exists():
                    try:
                        filepath.unlink()
                        deleted_count += 1
                        print(f"[删除已导出道具] 已删除public图片: {filename}")
                    except Exception as e:
                        print(f"[删除已导出道具] 删除public图片失败 {filename}: {e}")
                else:
                    print(f"[删除已导出道具] 图片不存在: {filepath}")
        
        # 3. 从 public/data/{map}.json 中删除道具数据
        if map_name:
            public_data_dir = Path(__file__).parent.parent / 'public' / 'data'
            map_data_file = public_data_dir / f"{map_name}.json"
            
            if map_data_file.exists():
                try:
                    # 读取现有数据
                    with open(map_data_file, 'r', encoding='utf-8') as f:
                        data_content = json.load(f)
                    
                    utilities_list = data_content.get('utilities', [])
                    
                    # 过滤掉要删除的道具（通过hash匹配）
                    original_count = len(utilities_list)
                    utilities_list = [u for u in utilities_list if u.get('hash') != hash_val]
                    removed_count = original_count - len(utilities_list)
                    
                    if removed_count > 0:
                        # 更新数据
                        data_content['utilities'] = utilities_list
                        
                        # 保存更新后的JSON文件
                        with open(map_data_file, 'w', encoding='utf-8') as f:
                            json.dump(data_content, f, ensure_ascii=False, indent=2)
                        
                        print(f"[删除已导出道具] 从{map_name}.json中删除了{removed_count}条数据")
                    else:
                        print(f"[删除已导出道具] {map_name}.json中未找到该道具数据")
                        
                except Exception as e:
                    print(f"[删除已导出道具] 更新public/data失败: {e}")
                    import traceback
                    traceback.print_exc()
            else:
                print(f"[删除已导出道具] 数据文件不存在: {map_data_file}")
        
        # 4. 更新索引文件 utilities.json
        try:
            index_file = Path(__file__).parent.parent / 'public' / 'data' / 'utilities.json'
            if index_file.exists() and map_name:
                with open(index_file, 'r', encoding='utf-8') as f:
                    index_data = json.load(f)
                
                # 更新对应地图的道具数量
                for map_info in index_data.get('maps', []):
                    if map_info['name'] == map_name:
                        # 重新读取地图数据文件获取最新数量
                        map_data_file = Path(__file__).parent.parent / 'public' / 'data' / f"{map_name}.json"
                        if map_data_file.exists():
                            with open(map_data_file, 'r', encoding='utf-8') as f:
                                map_data = json.load(f)
                                map_info['utility_count'] = len(map_data.get('utilities', []))
                        break
                
                # 重新计算总数
                total_count = sum(m.get('utility_count', 0) for m in index_data.get('maps', []))
                if 'statistics' not in index_data:
                    index_data['statistics'] = {}
                index_data['statistics']['total_utilities'] = total_count
                index_data['last_updated'] = datetime.now().isoformat()
                
                # 保存更新后的索引
                with open(index_file, 'w', encoding='utf-8') as f:
                    json.dump(index_data, f, ensure_ascii=False, indent=2)
                
                print(f"[删除已导出道具] 已更新索引文件")
        except Exception as e:
            print(f"[删除已导出道具] 更新索引文件失败: {e}")
        
        # 5. 从数据库中永久删除
        success = db.delete_utility(hash_val)
        
        if success:
            print(f"[删除已导出道具] 数据库删除成功")
            return jsonify({
                'success': True, 
                'message': f'已永久删除该道具（含 {deleted_count} 个文件）'
            })
        else:
            print(f"[删除已导出道具] 数据库删除失败")
            return jsonify({'success': False, 'message': '删除失败'}), 500
            
    except Exception as e:
        print(f"[删除已导出道具] 异常: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'服务器错误: {str(e)}'}), 500


@app.route('/api/exported')
def get_exported_utilities():
    """获取所有已导出的道具"""
    try:
        # 从数据库获取已导出的道具
        utilities = db.get_utilities(status='exported')
        
        return jsonify({
            'success': True,
            'utilities': utilities,
            'count': len(utilities)
        })
    except Exception as e:
        print(f"[获取已导出道具] 错误: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/edit_exported', methods=['POST'])
def edit_exported():
    """编辑已导出道具（兼容旧API - 仅更新文本字段）"""
    data = request.json
    hash_val = data.get('hash')
    info = data.get('info', {})
    
    fields = {}
    if 'display_name' in info:
        fields['display_name'] = info['display_name']
    if 'notes' in info:
        fields['notes'] = info['notes']
    if 'type' in info:
        fields['type'] = info['type']
    if 'team' in info:
        fields['team'] = info['team']
    if 'throw_type' in info:
        fields['throw_type'] = info['throw_type']
    
    success = db.update_utility(hash_val, fields)
    
    if success:
        return jsonify({'success': True, 'message': '更新成功'})
    else:
        return jsonify({'success': False, 'message': '道具未找到'}), 404


@app.route('/api/update_utility', methods=['POST'])
def update_utility():
    """完整更新道具（包括图片、坐标等所有信息）"""
    try:
        import hashlib
        from PIL import Image
        
        # 获取表单数据
        hash_val = request.form.get('hash')
        
        if not hash_val:
            return jsonify({'success': False, 'error': '缺少道具hash'}), 400
        
        # 获取原道具信息
        utility = db.get_utility_by_hash(hash_val)
        if not utility:
            return jsonify({'success': False, 'error': '道具未找到'}), 404
        
        print(f"[更新道具] 开始处理: {hash_val}")
        
        # 获取更新的字段
        name = request.form.get('name')
        map_name = request.form.get('map')
        utility_type = request.form.get('type')
        team = request.form.get('team')
        throw_type = request.form.get('throw_type', '未知')
        notes = request.form.get('notes', '')
        tags_str = request.form.get('tags', '')  # 获取标签字符串
        
        # 获取坐标数据
        import json
        throw_position = json.loads(request.form.get('throw_position', '{}'))
        throw_angles = json.loads(request.form.get('throw_angles', '{}'))
        land_position = json.loads(request.form.get('land_position', '{}'))
        
        # 处理标签：将逗号分隔的字符串转换为数组
        tags = []
        if tags_str:
            tags = [tag.strip() for tag in tags_str.split(',') if tag.strip()]
            print(f"[更新道具] 标签: {tags}")
        
        # 构建更新字段
        import json
        update_fields = {
            'display_name': name,
            'map': map_name,
            'type': utility_type,
            'team': team,
            'throw_type': throw_type,
            'notes': notes,
            'tags': json.dumps(tags),  # 添加tags字段
            'throw_position': json.dumps(throw_position),  # 转换为JSON字符串
            'throw_angles': json.dumps(throw_angles),      # 转换为JSON字符串
            'land_position': json.dumps(land_position)     # 转换为JSON字符串
        }
        
        # 处理图片更新
        screenshot_base = utility.get('screenshot_filename_base')
        if not screenshot_base:
            screenshot_base = f"{map_name}_{hash_val}"
        
        screenshots_dir = Path(__file__).parent.parent / 'output' / 'screenshots'
        screenshots_dir.mkdir(parents=True, exist_ok=True)
        
        # 检查是否有新上传的图片
        img_position = request.files.get('img_position')
        img_crosshair = request.files.get('img_crosshair')
        img_landing = request.files.get('img_landing')
        
        updated_images = []
        
        # 更新站位图
        if img_position:
            try:
                img_position.save(screenshots_dir / f"{screenshot_base}_position.jpg")
                updated_images.append('position')
                print(f"[更新道具] 已更新站位图")
            except Exception as e:
                print(f"[更新道具] 保存站位图失败: {e}")
        
        # 更新准星图
        if img_crosshair:
            try:
                img_crosshair.save(screenshots_dir / f"{screenshot_base}_crosshair.jpg")
                updated_images.append('crosshair')
                print(f"[更新道具] 已更新准星图")
            except Exception as e:
                print(f"[更新道具] 保存准星图失败: {e}")
        
        # 更新落点图
        if img_landing:
            try:
                img_landing.save(screenshots_dir / f"{screenshot_base}_landing.jpg")
                updated_images.append('landing')
                print(f"[更新道具] 已更新落点图")
            except Exception as e:
                print(f"[更新道具] 保存落点图失败: {e}")
        
        # 更新数据库
        success = db.update_utility(hash_val, update_fields)
        
        if not success:
            return jsonify({'success': False, 'error': '数据库更新失败'}), 500
        
        print(f"[更新道具] 数据库更新成功")
        
        # 如果状态是 exported，需要重新导出到 public
        if utility.get('status') == 'exported':
            print(f"[更新道具] 道具已导出，开始重新导出...")
            
            # 获取更新后的道具数据
            updated_utility = db.get_utility_by_hash(hash_val)
            
            # 重新导出
            export_success, export_message = export_single_utility(updated_utility, db)
            
            if export_success:
                print(f"[更新道具] 重新导出成功")
                message = f'道具更新成功'
                if updated_images:
                    message += f'（已更新图片: {", ".join(updated_images)}）'
                message += '，已重新导出到前端'
                return jsonify({'success': True, 'message': message})
            else:
                print(f"[更新道具] 重新导出失败: {export_message}")
                return jsonify({
                    'success': False,
                    'error': f'道具更新成功但重新导出失败: {export_message}'
                }), 500
        else:
            # 未导出的道具，只更新数据库
            message = f'道具更新成功'
            if updated_images:
                message += f'（已更新图片: {", ".join(updated_images)}）'
            return jsonify({'success': True, 'message': message})
        
    except Exception as e:
        print(f"[更新道具] 异常: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': f'服务器错误: {str(e)}'}), 500


def export_single_utility(utility, db_instance):
    """
    导出单个道具到 public 目录
    返回: (success, message)
    """
    try:
        from PIL import Image
        import json
        
        root_dir = Path(__file__).parent.parent
        public_dir = root_dir / 'public'
        screenshots_dir = root_dir / 'output' / 'screenshots'
        
        map_name = utility['map']
        util_type = utility['type']
        util_hash = utility['hash'][:8]
        utility_id = f"{map_name}_{util_type}_{util_hash}"
        
        # 1. 处理并复制截图到 public/images
        screenshot_base = utility.get('screenshot_filename_base') or f"{map_name}_{utility['hash']}"
        
        for shot_type in ['position', 'crosshair', 'landing']:
            src_file = screenshots_dir / f"{screenshot_base}_{shot_type}.jpg"
            
            if not src_file.exists():
                print(f"[警告] 截图文件不存在: {src_file}")
                continue
            
            dest_dir = public_dir / 'images' / map_name / util_type
            dest_dir.mkdir(parents=True, exist_ok=True)
            dest_file = dest_dir / f"{utility_id}_{shot_type}.jpg"
            
            # 处理图片（裁剪准星图，压缩其他图）
            try:
                img = Image.open(src_file)
                
                if shot_type == 'crosshair':
                    # 准星图：裁剪中心区域
                    width, height = img.size
                    crop_width = int(width * 0.4)
                    crop_height = int(height * 0.5)
                    left = (width - crop_width) // 2
                    top = (height - crop_height) // 2
                    right = left + crop_width
                    bottom = top + crop_height
                    img = img.crop((left, top, right, bottom))
                    img.save(dest_file, 'JPEG', quality=85, optimize=True)
                else:
                    # 站位图和落点图：压缩
                    if img.width > 1200 or img.height > 900:
                        img.thumbnail((1200, 900), Image.Resampling.LANCZOS)
                    img.save(dest_file, 'JPEG', quality=75, optimize=True)
                
                print(f"[导出] 已处理图片: {dest_file}")
                
            except Exception as e:
                print(f"[错误] 处理图片失败 ({shot_type}): {e}")
                return False, f"处理图片失败: {str(e)}"
        
        # 2. 生成道具数据
        utility_data = {
            'id': utility_id,
            'type': util_type,
            'team': utility.get('team', 'Unknown'),
            'name': utility.get('display_name', f'{util_type}_{util_hash}'),
            'description': f"{utility.get('throw_type', '投掷')}，飞行时间 {utility.get('flight_time', 0):.1f} 秒",
            'position': utility.get('throw_position', {}),
            'angles': utility.get('throw_angles', {}),
            'land_position': utility.get('land_position', {}),
            'throw_type': utility.get('throw_type', 'unknown'),
            'flight_time': round(utility.get('flight_time', 0), 2),
            'distance': round(utility.get('distance', 0), 1),
            'command': f"setpos {utility['throw_position']['x']:.2f} {utility['throw_position']['y']:.2f} {utility['throw_position']['z']:.2f}; setang {utility['throw_angles']['pitch']:.2f} {utility['throw_angles']['yaw']:.2f} 0",
            'quality': 3,
            'tags': utility.get('tags', []),  # 导出标签数据
            'notes': utility.get('notes', ''),
            'screenshots': {
                'position': f"images/{map_name}/{util_type}/{utility_id}_position.jpg",
                'crosshair': f"images/{map_name}/{util_type}/{utility_id}_crosshair.jpg",
                'landing': f"images/{map_name}/{util_type}/{utility_id}_landing.jpg"
            },
            'thrower': utility.get('thrower'),
            'demo_source': utility.get('source_demo'),
            'hash': utility['hash']
        }
        
        # 3. 更新地图数据文件
        map_data_file = public_dir / 'data' / f"{map_name}.json"
        map_data_file.parent.mkdir(parents=True, exist_ok=True)
        
        # 读取已有数据
        existing_utilities = []
        if map_data_file.exists():
            try:
                with open(map_data_file, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
                    existing_utilities = existing_data.get('utilities', [])
            except Exception as e:
                print(f"[警告] 读取已有地图数据失败: {e}")
        
        # 移除旧的同ID道具（如果存在）
        existing_utilities = [u for u in existing_utilities if u.get('id') != utility_id]
        
        # 添加新道具
        existing_utilities.append(utility_data)
        
        # 按ID排序
        existing_utilities.sort(key=lambda u: u['id'])
        
        # 保存更新后的数据
        with open(map_data_file, 'w', encoding='utf-8') as f:
            json.dump({
                'map': map_name,
                'utilities': existing_utilities
            }, f, ensure_ascii=False, indent=2)
        
        print(f"[导出] 已更新地图数据: {map_data_file}")
        
        # 4. 更新索引文件
        index_file = public_dir / 'data' / 'utilities.json'
        existing_maps = {}
        
        if index_file.exists():
            try:
                with open(index_file, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
                    for map_info in existing_data.get('maps', []):
                        existing_maps[map_info['name']] = map_info
            except:
                pass
        
        # 更新当前地图信息
        existing_maps[map_name] = {
            'name': map_name,
            'display_name': map_name.replace('de_', '').title(),
            'utility_count': len(existing_utilities),
            'data_file': f"data/{map_name}.json"
        }
        
        all_maps = sorted(existing_maps.values(), key=lambda x: x['name'])
        total_in_index = sum(m['utility_count'] for m in all_maps)
        
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
        
        print(f"[导出] 已更新索引文件")
        
        # 5. 更新数据库状态为 exported
        db_instance.update_status(
            utility['hash'],
            'exported',
            exported_time=datetime.now().isoformat()
        )
        
        return True, "导出成功"
        
    except Exception as e:
        print(f"[错误] 导出单个道具失败: {e}")
        import traceback
        traceback.print_exc()
        return False, f"导出失败: {str(e)}"


@app.route('/api/add_manual_utility', methods=['POST'])
def add_manual_utility():
    """手动添加道具（用户上传）- 直接导出到前端"""
    try:
        import hashlib
        from werkzeug.utils import secure_filename
        import json
        
        # 获取表单数据
        name = request.form.get('name')
        map_name = request.form.get('map')
        utility_type = request.form.get('type')
        team = request.form.get('team')
        throw_type = request.form.get('throw_type', '未知')
        source = request.form.get('source', '手动添加')
        notes = request.form.get('notes', '')
        tags_str = request.form.get('tags', '')  # 获取标签字符串
        
        # 获取坐标数据
        throw_position = json.loads(request.form.get('throw_position', '{}'))
        throw_angles = json.loads(request.form.get('throw_angles', '{}'))
        land_position = json.loads(request.form.get('land_position', '{}'))
        
        # 处理标签：将逗号分隔的字符串转换为数组
        tags = []
        if tags_str:
            tags = [tag.strip() for tag in tags_str.split(',') if tag.strip()]
            print(f"[手动添加道具] 标签: {tags}")
        
        # 验证必填字段
        if not all([name, map_name, utility_type, team]):
            return jsonify({'success': False, 'error': '缺少必填字段'}), 400
        
        if not all([throw_position, throw_angles, land_position]):
            return jsonify({'success': False, 'error': '缺少坐标信息'}), 400
        
        # 获取上传的图片
        img_position = request.files.get('img_position')
        img_crosshair = request.files.get('img_crosshair')
        img_landing = request.files.get('img_landing')
        
        if not all([img_position, img_crosshair, img_landing]):
            return jsonify({'success': False, 'error': '请上传所有三张截图'}), 400
        
        # 使用与Demo解析相同的hash生成规则
        # 将坐标四舍五入到1位小数
        throw_pos = (
            round(throw_position.get('x', 0), 1),
            round(throw_position.get('y', 0), 1),
            round(throw_position.get('z', 0), 1)
        )
        throw_ang = (
            round(throw_angles.get('pitch', 0), 1),
            round(throw_angles.get('yaw', 0), 1)
        )
        land_pos = (
            round(land_position.get('x', 0), 1),
            round(land_position.get('y', 0), 1),
            round(land_position.get('z', 0), 1)
        )
        
        # 生成weapon字符串（根据类型）
        weapon_map = {
            'smoke': 'weapon_smokegrenade',
            'flashbang': 'weapon_flashbang',
            'hegrenade': 'weapon_hegrenade',
            'incendiary': 'weapon_incgrenade',
            'molotov': 'weapon_molotov'
        }
        weapon = weapon_map.get(utility_type, 'unknown')
        
        # 组合成字符串（与extractor.py中的逻辑一致）
        hash_string = f"{throw_pos}_{throw_ang}_{land_pos}_{weapon}"
        hash_val = hashlib.md5(hash_string.encode()).hexdigest()[:16]
        
        print(f"[手动添加道具] Hash生成字符串: {hash_string}")
        print(f"[手动添加道具] 生成的Hash: {hash_val}")
        
        # 保存图片文件到 output/screenshots
        screenshots_dir = Path(__file__).parent.parent / 'output' / 'screenshots'
        screenshots_dir.mkdir(parents=True, exist_ok=True)
        
        screenshot_base = f"{map_name}_{hash_val}"
        
        try:
            # 保存三张图片
            img_position.save(screenshots_dir / f"{screenshot_base}_position.jpg")
            img_crosshair.save(screenshots_dir / f"{screenshot_base}_crosshair.jpg")
            img_landing.save(screenshots_dir / f"{screenshot_base}_landing.jpg")
            print(f"[手动添加道具] 已保存截图到 output/screenshots")
        except Exception as e:
            print(f"[手动添加道具] 保存图片失败: {e}")
            return jsonify({'success': False, 'error': f'保存图片失败: {str(e)}'}), 500
        
        # 插入数据库（初始状态为 approved，稍后会更新为 exported）
        timestamp = datetime.now().isoformat()
        utility_data = {
            'hash': hash_val,
            'map': map_name,
            'type': utility_type,
            'team': team,
            'throw_type': throw_type,
            'throw_position': throw_position,
            'throw_angles': throw_angles,
            'land_position': land_position,
            'display_name': name,
            'notes': notes,
            'tags': tags,  # 添加标签
            'demo_source': source,
            'screenshot_filename_base': screenshot_base,
            'status': 'approved',  # 临时状态，导出后会变为 exported
            'created_time': timestamp,
            'approved_time': timestamp
        }
        
        success = db.insert_utility(utility_data)
        
        if not success:
            # 如果数据库插入失败（可能是hash冲突），删除已保存的图片
            for suffix in ['position', 'crosshair', 'landing']:
                filepath = screenshots_dir / f"{screenshot_base}_{suffix}.jpg"
                if filepath.exists():
                    filepath.unlink()
            
            return jsonify({'success': False, 'error': '该道具已存在（相同坐标和角度）'}), 400
        
        print(f"[手动添加道具] 成功添加到数据库: {name} ({hash_val})")
        
        # 立即导出到 public 目录
        utility = db.get_utility_by_hash(hash_val)
        if utility:
            export_success, export_message = export_single_utility(utility, db)
            
            if export_success:
                print(f"[手动添加道具] 成功导出到前端")
                return jsonify({
                    'success': True, 
                    'message': '道具添加成功并已导出到前端',
                    'hash': hash_val
                })
            else:
                print(f"[手动添加道具] 导出失败: {export_message}")
                return jsonify({
                    'success': False, 
                    'error': f'道具已添加但导出失败: {export_message}'
                }), 500
        else:
            return jsonify({
                'success': False, 
                'error': '道具添加成功但无法读取数据'
            }), 500
            
    except Exception as e:
        print(f"[手动添加道具] 异常: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': f'服务器错误: {str(e)}'}), 500



@app.route('/screenshots/<path:filename>')
def serve_screenshot(filename):
    """提供截图文件"""
    screenshots_dir = Path(__file__).parent.parent / 'output' / 'screenshots'
    return send_from_directory(screenshots_dir, filename)


@app.errorhandler(404)
def not_found(e):
    return jsonify({'error': 'Not found'}), 404


@app.errorhandler(500)
def internal_error(e):
    return jsonify({'error': 'Internal server error', 'message': str(e)}), 500


if __name__ == '__main__':
    import logging
    
    # 禁用 Flask 的访问日志，只保留错误日志
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)
    
    print("=" * 70)
    print("🍊 CS2 道具管理后台")
    print("=" * 70)
    print(f"\n🌐 服务器启动成功！")
    print(f"📍 管理后台: http://localhost:5000")
    print(f"⏹️  按 Ctrl+C 停止服务器")
    print(f"ℹ️  HTTP 访问日志已关闭，只显示错误和操作日志\n")
    print("=" * 70)
    
    app.run(host='0.0.0.0', port=5000, debug=True)
