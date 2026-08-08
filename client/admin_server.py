"""
管理后台服务器
使用 Python 内置 http.server，无需 Flask
"""
import json
import os
import sys
from pathlib import Path
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import mimetypes

# 添加当前目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent))

from src.manager import UtilityManager
from src.parser import parse_demo
from src.extractor import extract_utilities


class AdminHandler(SimpleHTTPRequestHandler):
    """管理后台请求处理器"""
    
    def __init__(self, *args, **kwargs):
        self.root_dir = Path(__file__).resolve().parent.parent
        self.admin_dir = Path(__file__).resolve().parent / 'admin'
        self.manager = UtilityManager()
        super().__init__(*args, directory=str(self.admin_dir), **kwargs)
    
    def do_GET(self):
        """处理 GET 请求"""
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        
        # API 路由
        if path.startswith('/api/'):
            self.handle_api_get(path, parsed_path.query)
        # 截图文件路由
        elif path.startswith('/screenshots/') or 'output/screenshots/' in path:
            # 处理截图文件请求
            # 支持两种路径格式：
            # 1. /screenshots/xxx.jpg
            # 2. ../../output/screenshots/xxx.jpg
            filename = path.split('/')[-1]  # 获取文件名
            screenshot_path = self.root_dir / 'output' / 'screenshots' / filename
            
            if screenshot_path.exists() and screenshot_path.is_file():
                self.send_file(screenshot_path)
            else:
                self.send_error(404, f"Screenshot not found: {filename}")
        # 静态文件
        else:
            if path == '/':
                path = '/index.html'
            
            file_path = self.admin_dir / path.lstrip('/')
            
            if file_path.exists() and file_path.is_file():
                self.send_file(file_path)
            else:
                self.send_error(404, "File not found")
    
    def do_POST(self):
        """处理 POST 请求"""
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        
        # 读取请求体
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        
        try:
            data = json.loads(post_data.decode('utf-8'))
        except:
            data = {}
        
        # API 路由
        if path.startswith('/api/'):
            self.handle_api_post(path, data)
        else:
            self.send_error(404, "Not found")
    
    def handle_api_get(self, path, query):
        """处理 API GET 请求"""
        try:
            if path == '/api/stats':
                # 获取统计信息
                stats = self.manager.get_statistics()
                self.send_json(stats)
            
            elif path == '/api/pending':
                # 获取待审核道具：返回已截图的道具
                # 从 selected_for_screenshot.json 读取（包含 screenshot_id）
                screenshot_file = self.root_dir / 'output' / 'commands' / 'selected_for_screenshot.json'
                
                if screenshot_file.exists():
                    with open(screenshot_file, 'r', encoding='utf-8') as f:
                        utilities = json.load(f)
                    
                    # 只返回状态为 pending 的道具（未批准的）
                    utilities = [u for u in utilities if u.get('status') == 'pending']
                    
                    # 按 screenshot_id 排序，确保顺序与截图编号一致
                    utilities.sort(key=lambda u: u.get('screenshot_id', 'util999'))
                else:
                    utilities = []
                
                self.send_json({'utilities': utilities})
            
            elif path == '/api/all_pending':
                # 获取所有待审核道具（包括未截图的）- 用于选择道具页面
                utilities = self.manager.get_pending_utilities()
                
                # 加载 selected_for_screenshot.json 中的 screenshot_id
                screenshot_file = self.root_dir / 'output' / 'commands' / 'selected_for_screenshot.json'
                screenshot_map = {}
                
                if screenshot_file.exists():
                    with open(screenshot_file, 'r', encoding='utf-8') as f:
                        screenshot_utilities = json.load(f)
                        for u in screenshot_utilities:
                            if 'hash' in u and 'screenshot_id' in u:
                                screenshot_map[u['hash']] = u['screenshot_id']
                
                # 将 screenshot_id 添加到道具数据中
                for u in utilities:
                    if u.get('hash') in screenshot_map:
                        u['screenshot_id'] = screenshot_map[u['hash']]
                
                # 按parse_time排序
                utilities.sort(key=lambda u: u.get('parse_time', ''))
                
                self.send_json({'utilities': utilities})
            
            elif path == '/api/approved':
                # 获取已批准道具
                utilities = self.manager.load_data('approved')
                self.send_json({'utilities': utilities})
            
            elif path == '/api/exported':
                # 获取已导出道具
                utilities = self.manager.load_data('exported')
                self.send_json({'utilities': utilities})
            
            elif path == '/api/demos':
                # 获取 demo 文件列表
                demos_path = self.root_dir / 'demos'
                demo_files = list(demos_path.glob('*.dem'))
                
                # 读取已解析的 demo 记录
                parsed_raw_file = self.root_dir / 'output' / 'data' / 'parsed_raw.json'
                parsed_demos = set()
                if parsed_raw_file.exists():
                    try:
                        with open(parsed_raw_file, 'r', encoding='utf-8') as f:
                            raw_data = json.load(f)
                            # 提取所有 demo 名称（字段名是 source_demo）
                            parsed_demos = set(u.get('source_demo', '') for u in raw_data)
                    except Exception as e:
                        print(f"[警告] 读取 parsed_raw.json 失败: {e}")
                
                demos = []
                for d in demo_files:
                    demos.append({
                        'name': d.name,
                        'size': d.stat().st_size,
                        'parsed': d.name in parsed_demos
                    })
                
                self.send_json({'demos': demos})
            
            else:
                self.send_error(404, "API not found")
                
        except Exception as e:
            print(f"[错误] API GET 请求失败: {path}")
            print(f"       错误信息: {e}")
            import traceback
            traceback.print_exc()
            self.send_json({'success': False, 'error': str(e)})
    
    def handle_api_post(self, path, data):
        """处理 API POST 请求"""
        if path == '/api/parse_demo':
            # 解析 demo
            demo_name = data.get('demo_name')
            if not demo_name:
                self.send_json({'success': False, 'message': '缺少参数'})
                return
            
            demo_path = self.root_dir / 'demos' / demo_name
            
            if not demo_path.exists():
                self.send_json({'success': False, 'message': 'Demo 文件不存在'})
                return
            
            try:
                # 解析
                demo_data = parse_demo(str(demo_path))
                utilities = extract_utilities(demo_data)
                
                # 添加来源信息
                import datetime
                parse_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                for util in utilities:
                    util['source_demo'] = demo_name
                    util['parse_time'] = parse_time
                
                # 保存到管理系统
                new_count, dup_count = self.manager.add_parsed_utilities(utilities)
                
                self.send_json({
                    'success': True,
                    'message': f'解析完成！新增 {new_count} 个，跳过 {dup_count} 个重复',
                    'new_count': new_count,
                    'dup_count': dup_count
                })
            except Exception as e:
                self.send_json({'success': False, 'message': f'解析失败: {str(e)}'})
        
        elif path == '/api/select_utilities':
            # 选择道具进行截图
            # 选择道具进行截图
            # 支持两种模式：
            # 1. 旧模式：按类型选择 { "type": "smoke" }
            # 2. 新模式：选择具体道具列表 { "utilities": [...], "count": 10 }
            
            if 'utilities' in data:
                # 新模式：使用前端传来的选中道具列表
                new_utilities = data.get('utilities', [])
            else:
                # 旧模式：按类型筛选
                util_type = data.get('type', 'all')
                new_utilities = self.manager.get_pending_utilities()
                
                if util_type != 'all':
                    new_utilities = [u for u in new_utilities if (u.get('type') or u.get('grenade_type')) == util_type]
            
            # 📌 智能合并模式
            output_path = self.root_dir / "output" / "commands" / "selected_for_screenshot.json"
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 读取已有的道具列表
            existing_utilities = []
            if output_path.exists():
                try:
                    with open(output_path, 'r', encoding='utf-8') as f:
                        existing_utilities = json.load(f)
                except:
                    existing_utilities = []
            
            # 检查新选择的道具来自哪张地图
            new_maps = set(u.get('map') for u in new_utilities if u.get('map'))
            existing_maps = set(u.get('map') for u in existing_utilities if u.get('map'))
            
            # 如果新道具和已有道具来自不同地图，提示用户
            if existing_utilities and new_maps and existing_maps and not new_maps.intersection(existing_maps):
                # 不同地图：清空旧数据
                self.send_json({
                    'success': False,
                    'message': f'检测到不同地图的道具！\n\n当前列表: {", ".join(existing_maps)}\n新选择: {", ".join(new_maps)}\n\n请先清空列表或审核完现有道具。',
                    'conflict': True,
                    'existing_maps': list(existing_maps),
                    'new_maps': list(new_maps),
                    'existing_count': len(existing_utilities)
                })
                return
            
            # 获取已有道具的 hash 集合
            existing_hashes = {u.get('hash') for u in existing_utilities if u.get('hash')}
            
            # 只添加不存在的道具（避免重复）
            added_count = 0
            for util in new_utilities:
                util_hash = util.get('hash')
                if util_hash and util_hash not in existing_hashes:
                    existing_utilities.append(util)
                    existing_hashes.add(util_hash)
                    added_count += 1
            
            # 保存合并后的列表
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(existing_utilities, f, ensure_ascii=False, indent=2)
            
            self.send_json({
                'success': True,
                'message': f'已添加 {added_count} 个道具到截图列表（跳过 {len(new_utilities) - added_count} 个重复）',
                'count': len(existing_utilities),
                'added': added_count
            })
        
        elif path == '/api/approve':
            # 批准道具
            util_hash = data.get('hash')
            updated_info = data.get('info', {})
            
            success, message = self.manager.approve_utility(util_hash, updated_info)
            self.send_json({'success': success, 'message': message})
        
        elif path == '/api/reject':
            # 拒绝道具
            util_hash = data.get('hash')
            
            success, message = self.manager.reject_utility(util_hash)
            self.send_json({'success': success, 'message': message})
        
        elif path == '/api/delete_approved':
            # 删除已批准的道具
            util_hash = data.get('hash')
            
            success, message = self.manager.delete_approved_utility(util_hash)
            self.send_json({'success': success, 'message': message})
        
        elif path == '/api/delete_pending':
            # 删除待审核的道具（永久删除）
            util_hash = data.get('hash')
            
            success, message = self.manager.delete_pending_utility(util_hash)
            self.send_json({'success': success, 'message': message})
        
        elif path == '/api/export':
            # 导出数据
            try:
                import subprocess
                export_script = self.root_dir / 'client' / 'export.py'
                result = subprocess.run(['python', str(export_script)], 
                                      capture_output=True, text=True, cwd=str(self.root_dir / 'client'))
                
                if result.returncode == 0:
                    # 导出成功后，将已批准道具移到已导出
                    approved = self.manager.load_data('approved')
                    if approved:
                        utility_hashes = [u['hash'] for u in approved]
                        self.manager.mark_as_exported(utility_hashes)
                    
                    # 已导出的道具保持在exported.json中（不需要移动）
                    
                    self.send_json({'success': True, 'message': f'导出成功！共导出 {len(approved)} 个新道具'})
                else:
                    self.send_json({'success': False, 'message': f'导出失败: {result.stderr}'})
            except Exception as e:
                self.send_json({'success': False, 'message': f'导出失败: {str(e)}'})
        
        elif path == '/api/unexport':
            # 撤销导出
            util_hash = data.get('hash')
            
            success, message = self.manager.unexport_utility(util_hash)
            self.send_json({'success': success, 'message': message})
        
        elif path == '/api/edit_exported':
            # 编辑已导出道具
            util_hash = data.get('hash')
            updated_info = data.get('info', {})
            
            success, message = self.manager.edit_exported_utility(util_hash, updated_info)
            self.send_json({'success': success, 'message': message})
        
        else:
            self.send_error(404, "API not found")
    
    def send_json(self, data):
        """发送 JSON 响应"""
        json_data = json.dumps(data, ensure_ascii=False).encode('utf-8')
        
        self.send_response(200)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', len(json_data))
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json_data)
    
    def send_file(self, file_path):
        """发送文件"""
        try:
            with open(file_path, 'rb') as f:
                content = f.read()
            
            self.send_response(200)
            
            # 设置 MIME 类型
            mime_type, _ = mimetypes.guess_type(str(file_path))
            if mime_type:
                self.send_header('Content-Type', mime_type)
            
            self.send_header('Content-Length', len(content))
            self.end_headers()
            self.wfile.write(content)
        except Exception as e:
            self.send_error(500, f"Error reading file: {str(e)}")
    
    def log_message(self, format, *args):
        """自定义日志"""
        print(f"[{self.log_date_time_string()}] {format % args}")


def main():
    """启动服务器"""
    # 创建 admin 目录
    admin_dir = Path(__file__).parent / 'admin'
    admin_dir.mkdir(exist_ok=True)
    
    # 启动服务器
    port = 5000
    server_address = ('', port)
    httpd = HTTPServer(server_address, AdminHandler)
    
    print("=" * 70)
    print("🎮 CS2 道具管理后台")
    print("=" * 70)
    print(f"\n🌐 服务器启动成功！")
    print(f"📍 管理后台: http://localhost:{port}")
    print(f"⏹️  按 Ctrl+C 停止服务器\n")
    print("=" * 70)
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n\n👋 服务器已停止")
        httpd.shutdown()


if __name__ == '__main__':
    main()
