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

from backend.database import Database
from backend.routes import demo, utility, screenshot, export_route

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
    
    success = db.update_status(
        hash_val,
        'approved',
        display_name=info.get('display_name'),
        notes=info.get('notes'),
        approved_time=datetime.now().isoformat()
    )
    
    if success:
        return jsonify({'success': True, 'message': '批准成功'})
    else:
        return jsonify({'success': False, 'message': '道具未找到'}), 404


@app.route('/api/reject', methods=['POST'])
def reject_utility_legacy():
    """拒绝道具（兼容旧API）"""
    data = request.json
    hash_val = data.get('hash')
    
    success = db.update_status(hash_val, 'rejected')
    
    if success:
        return jsonify({'success': True, 'message': '已拒绝'})
    else:
        return jsonify({'success': False, 'message': '道具未找到'}), 404


@app.route('/api/delete_pending', methods=['POST'])
def delete_pending_legacy():
    """删除待审核道具（兼容旧API）"""
    data = request.json
    hash_val = data.get('hash')
    
    success = db.delete_utility(hash_val)
    
    if success:
        return jsonify({'success': True, 'message': '已删除'})
    else:
        return jsonify({'success': False, 'message': '道具未找到'}), 404


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
