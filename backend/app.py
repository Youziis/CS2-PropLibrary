"""
管理后台主程序
使用 Flask + SQLite
"""
import os
import sys
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
    """删除待审核道具（永久删除，包括截图文件）"""
    try:
        data = request.json
        hash_val = data.get('hash')
        
        # 获取道具信息以找到截图文件
        utility = db.get_utility_by_hash(hash_val)
        
        if not utility:
            return jsonify({'success': False, 'message': '道具未找到'}), 404
        
        # 删除截图文件
        screenshot_base = utility.get('screenshot_filename_base')
        if screenshot_base:
            screenshots_dir = Path(__file__).parent.parent / 'output' / 'screenshots'
            screenshot_files = [
                f"{screenshot_base}_position.jpg",
                f"{screenshot_base}_crosshair.jpg",
                f"{screenshot_base}_landing.jpg"
            ]
            
            deleted_count = 0
            for filename in screenshot_files:
                filepath = screenshots_dir / filename
                if filepath.exists():
                    try:
                        filepath.unlink()
                        deleted_count += 1
                    except Exception as e:
                        print(f"删除截图失败 {filename}: {e}")
            
            print(f"已删除 {deleted_count} 个截图文件")
        
        # 从数据库中永久删除
        success = db.delete_utility(hash_val)
        
        if success:
            return jsonify({'success': True, 'message': '已永久删除该道具'})
        else:
            return jsonify({'success': False, 'message': '删除失败'}), 500
            
    except Exception as e:
        print(f"删除道具异常: {e}")
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


@app.route('/api/edit_exported', methods=['POST'])
def edit_exported():
    """编辑已导出道具（兼容旧API）"""
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
    print("=" * 70)
    print("🎮 CS2 道具管理后台")
    print("=" * 70)
    print(f"\n🌐 服务器启动成功！")
    print(f"📍 管理后台: http://localhost:5000")
    print(f"⏹️  按 Ctrl+C 停止服务器\n")
    print("=" * 70)
    
    app.run(host='0.0.0.0', port=5000, debug=True)
