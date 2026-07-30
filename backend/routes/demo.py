"""
Demo 管理路由
"""
import sys
from pathlib import Path
from flask import Blueprint, request, jsonify
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.database import Database
from client.src.parser import parse_demo
from client.src.extractor import extract_utilities

bp = Blueprint('demo', __name__)
db = Database()


@bp.route('/api/demos', methods=['GET'])
def get_demos():
    """获取 demo 文件列表"""
    demos_path = Path(__file__).parent.parent.parent / 'demos'
    demos_path.mkdir(exist_ok=True)
    
    demo_files = list(demos_path.glob('*.dem'))
    
    # 获取已解析的 demo
    all_utilities = db.get_utilities()
    parsed_demos = set(u['source_demo'] for u in all_utilities if u.get('source_demo'))
    
    demos = []
    for demo_file in demo_files:
        demos.append({
            'name': demo_file.name,
            'size': demo_file.stat().st_size,
            'parsed': demo_file.name in parsed_demos
        })
    
    return jsonify({'demos': demos})


@bp.route('/api/parse_demo', methods=['POST'])
def parse_demo_route():
    """解析 demo 文件"""
    data = request.json
    demo_name = data.get('demo_name')
    
    if not demo_name:
        return jsonify({'success': False, 'message': '缺少参数'}), 400
    
    demo_path = Path(__file__).parent.parent.parent / 'demos' / demo_name
    
    if not demo_path.exists():
        return jsonify({'success': False, 'message': 'Demo 文件不存在'}), 404
    
    try:
        # 解析 demo
        print(f"[解析] 开始解析: {demo_name}")
        demo_data = parse_demo(str(demo_path))
        utilities = extract_utilities(demo_data)
        
        # 添加来源信息
        parse_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        for util in utilities:
            util['source_demo'] = demo_name
            util['parse_time'] = parse_time
        
        # 保存到数据库
        added, duplicated = db.add_utilities(utilities)
        
        print(f"[完成] 新增 {added} 个，跳过 {duplicated} 个重复")
        
        return jsonify({
            'success': True,
            'message': f'解析完成！新增 {added} 个，跳过 {duplicated} 个重复',
            'new_count': added,
            'dup_count': duplicated
        })
        
    except Exception as e:
        print(f"[错误] 解析失败: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'解析失败: {str(e)}'}), 500
