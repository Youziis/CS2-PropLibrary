#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据导出工具
将审核通过的道具数据导出到 public/ 目录，用于静态网站部署
"""

import sys
import io
import json
import shutil
import os
from pathlib import Path
from datetime import datetime
from PIL import Image

# 设置标准输出编码为 UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 添加项目根目录到sys.path以导入backend模块
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir.resolve()))

from backend.database import Database

class UtilityExporter:
    def __init__(self, 
                 input_data_dir=None,
                 input_screenshots_dir=None,
                 output_dir=None):
        # 获取项目根目录（export.py在client目录下，所以parent.parent是根目录）
        root_dir = Path(__file__).parent.parent
        
        self.input_data_dir = Path(input_data_dir) if input_data_dir else root_dir / 'output' / 'data'
        self.input_screenshots_dir = Path(input_screenshots_dir) if input_screenshots_dir else root_dir / 'output' / 'screenshots'
        self.output_dir = Path(output_dir) if output_dir else root_dir / 'public'
        
        # 创建输出目录
        (self.output_dir / 'data').mkdir(parents=True, exist_ok=True)
        (self.output_dir / 'images').mkdir(parents=True, exist_ok=True)
    
    def load_utilities(self):
        """从数据库加载已批准和已导出的道具数据"""
        db = Database()
        utilities = []
        
        # 加载已批准的道具（待导出）
        approved = db.get_utilities(status='approved')
        if approved:
            utilities.extend(approved)
            print(f"[OK] 从数据库加载了 {len(approved)} 个待导出道具（状态=approved）")
        
        # 加载已导出的道具（用于重新导出）
        exported = db.get_utilities(status='exported')
        if exported:
            utilities.extend(exported)
            print(f"[OK] 从数据库加载了 {len(exported)} 个已导出道具（状态=exported，将重新导出）")
        
        if not utilities:
            print(f"[错误] 没有需要导出的道具")
            print(f"[提示] 请先在审核页面批准道具，或使用后端导出API")
            return []
        
        print(f"[OK] 共加载了 {len(utilities)} 个道具")
        return utilities
    
    def generate_utility_id(self, utility):
        """生成道具ID（使用hash值前8位）"""
        map_name = utility.get('map', 'unknown')
        util_type = utility.get('type', 'unknown')
        util_hash = utility.get('hash', 'unknown')[:8]
        return f"{map_name}_{util_type}_{util_hash}"
    
    def compress_and_copy_image(self, src_path, dest_path, shot_type, max_size=(1200, 900), quality=75):
        """
        处理并保存图片
        - crosshair（准星图）: 裁剪中心区域，保留准星周围
        - position/landing（站位图/落点图）: 压缩质量以减小文件大小
        """
        try:
            # 创建目标目录
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 打开图片
            img = Image.open(src_path)
            original_size = os.path.getsize(src_path) / 1024  # KB
            
            if shot_type == 'crosshair':
                # 准星图：裁剪中心区域
                # CS2截图通常是1920x1080，准星在中心
                width, height = img.size
                
                # 裁剪中心区域（保留准星周围）
                # 裁剪尺寸：宽度的40%，高度的50%左右
                crop_width = int(width * 0.4)
                crop_height = int(height * 0.5)
                
                # 计算裁剪区域（中心区域）
                left = (width - crop_width) // 2
                top = (height - crop_height) // 2
                right = left + crop_width
                bottom = top + crop_height
                
                # 裁剪图片
                img = img.crop((left, top, right, bottom))
                
                # 保存裁剪后的图片，使用较高质量
                img.save(dest_path, 'JPEG', quality=85, optimize=True)
                
                new_size = os.path.getsize(dest_path) / 1024
                print(f"      裁剪准星图: {original_size:.1f}KB -> {new_size:.1f}KB (尺寸: {crop_width}x{crop_height})")
                
            else:
                # 站位图和落点图：压缩质量
                # 如果图片太大，先缩小尺寸
                if img.width > max_size[0] or img.height > max_size[1]:
                    img.thumbnail(max_size, Image.Resampling.LANCZOS)
                
                # 保存压缩后的图片
                img.save(dest_path, 'JPEG', quality=quality, optimize=True)
                
                new_size = os.path.getsize(dest_path) / 1024
                compression_ratio = (1 - new_size / original_size) * 100 if original_size > 0 else 0
                print(f"      压缩: {original_size:.1f}KB -> {new_size:.1f}KB (压缩率: {compression_ratio:.1f}%)")
            
            return True
            
        except Exception as e:
            print(f"      [错误] 处理图片失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def export_screenshots(self, utility, utility_id, map_name, util_type):
        """
        导出道具的3张截图
        使用 screenshot_filename_base 来定位正确的截图文件
        返回截图的相对路径
        """
        screenshots = {}
        shot_types = ['position', 'crosshair', 'landing']
        
        # 获取截图文件名前缀（使用screenshot_filename_base字段）
        screenshot_base = utility.get('screenshot_filename_base', '')
        
        if not screenshot_base:
            print(f"   [警告] 道具没有screenshot_filename_base，跳过截图导出")
            return screenshots
        
        for shot_type in shot_types:
            # 使用screenshot_filename_base直接构造文件名
            src_filename = f"{screenshot_base}_{shot_type}.jpg"
            src_path = self.input_screenshots_dir / src_filename
            
            if src_path.exists():
                # 目标文件路径
                dest_subdir = self.output_dir / 'images' / map_name / util_type
                dest_filename = f"{utility_id}_{shot_type}.jpg"
                dest_path = dest_subdir / dest_filename
                
                print(f"   [导出] {shot_type} 图: {src_filename} -> {dest_filename}")
                # 传入shot_type参数，用于区分处理方式
                if self.compress_and_copy_image(src_path, dest_path, shot_type):
                    # 保存相对路径（供前端使用）
                    screenshots[shot_type] = f"images/{map_name}/{util_type}/{dest_filename}"
            else:
                print(f"   [警告] 未找到截图文件: {src_filename}")
        
        return screenshots
    
    def transform_utility_data(self, utility, utility_id, screenshots):
        """
        转换道具数据格式为前端友好的格式
        """
        return {
            'id': utility_id,
            'type': utility.get('type', 'unknown'),
            'team': utility.get('team', 'Unknown'),
            'name': utility.get('display_name') or self.generate_utility_name(utility),  # 使用审核时填写的名称
            'description': self.generate_description(utility),
            
            # 位置和角度（兼容两种字段名）
            'position': utility.get('throw_position_corrected') or utility.get('position', {}),
            'angles': utility.get('throw_angles') or utility.get('angles', {}),
            'land_position': utility.get('land_position', {}),
            
            # 投掷信息（使用审核时可能修改的值）
            'throw_type': utility.get('throw_type', 'unknown'),
            'flight_time': round(utility.get('flight_time', 0), 2),
            'distance': round(utility.get('distance', 0), 1),
            
            # 控制台命令
            'command': self.generate_command(utility),
            
            # 审核信息
            'quality': 3,  # 默认3星，后续可添加审核系统
            'tags': self.generate_tags(utility),
            'notes': utility.get('notes', ''),  # 备注信息
            
            # 截图
            'screenshots': screenshots,
            
            # 来源信息
            'thrower': utility.get('thrower', 'Unknown'),
            'demo_source': utility.get('source_demo', '')
        }
    
    def generate_utility_name(self, utility):
        """生成道具名称"""
        util_type_names = {
            'smoke': '烟雾弹',
            'flashbang': '闪光弹',
            'hegrenade': '手雷',
            'molotov': '燃烧弹',
            'incendiary': '燃烧弹'
        }
        type_name = util_type_names.get(utility.get('type'), '道具')
        return f"{type_name}"  # 后续可以添加位置名称
    
    def generate_description(self, utility):
        """生成道具描述"""
        throw_type_names = {
            'jump': '跳投',
            'stand': '站投',
            'crouch': '蹲投'
        }
        throw_type = throw_type_names.get(utility.get('throw_type'), '投掷')
        flight_time = utility.get('flight_time', 0)
        return f"{throw_type}，飞行时间 {flight_time:.1f} 秒"
    
    def generate_command(self, utility):
        """生成控制台命令"""
        if 'command' in utility:
            return utility['command']
        
        # 兼容两种字段名
        pos = utility.get('throw_position_corrected') or utility.get('position', {})
        angles = utility.get('throw_angles') or utility.get('angles', {})
        return f"setpos {pos.get('x', 0):.2f} {pos.get('y', 0):.2f} {pos.get('z', 0):.2f}; setang {angles.get('pitch', 0):.2f} {angles.get('yaw', 0):.2f} 0"
    
    def generate_tags(self, utility):
        """生成标签"""
        tags = []
        
        # 根据投掷方式添加标签
        if utility.get('throw_type') == 'jump':
            tags.append('跳投')
        
        # 根据飞行时间添加标签
        flight_time = utility.get('flight_time', 0)
        if flight_time > 2.5:
            tags.append('远投')
        elif flight_time < 1.0:
            tags.append('近投')
        
        return tags
    
    def export_map_data(self, map_name, utilities):
        """导出单个地图的数据（合并模式）"""
        output_file = self.output_dir / 'data' / f'{map_name}.json'
        
        # 读取已有的地图数据
        existing_utilities = []
        existing_ids = set()
        
        if output_file.exists():
            try:
                with open(output_file, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
                    existing_utilities = existing_data.get('utilities', [])
                    # 记录已有道具的ID
                    existing_ids = {u['id'] for u in existing_utilities}
                    print(f"   已加载 {len(existing_utilities)} 个现有道具")
            except Exception as e:
                print(f"   [警告] 读取已有地图数据失败: {e}")
        
        # 合并道具列表：更新已有道具或添加新道具
        merged_utilities = []
        new_utility_ids = {u['id'] for u in utilities}
        
        # 保留未被更新的已有道具
        for existing_util in existing_utilities:
            if existing_util['id'] not in new_utility_ids:
                merged_utilities.append(existing_util)
        
        # 添加所有新道具（包括更新的道具）
        merged_utilities.extend(utilities)
        
        # 按ID排序，保持稳定顺序
        merged_utilities.sort(key=lambda u: u['id'])
        
        print(f"   合并后共 {len(merged_utilities)} 个道具（新增/更新 {len(utilities)} 个）")
        
        map_data = {
            'map': map_name,
            'utilities': merged_utilities
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(map_data, f, ensure_ascii=False, indent=2)
        
        print(f"\n[OK] 已导出地图数据: {output_file}")
    
    def export_index(self, maps_summary):
        """导出总索引文件"""
        index_data = {
            'version': '1.0.0',
            'last_updated': datetime.now().isoformat(),
            'maps': maps_summary,
            'statistics': self.calculate_statistics(maps_summary)
        }
        
        output_file = self.output_dir / 'data' / 'utilities.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(index_data, f, ensure_ascii=False, indent=2)
        
        print(f"[OK] 已导出索引文件: {output_file}")
    
    def calculate_statistics(self, maps_summary):
        """计算统计信息"""
        total = sum(m['utility_count'] for m in maps_summary)
        by_type = {}
        
        # 这里简化处理，实际需要从所有地图数据中统计
        return {
            'total_utilities': total,
            'by_type': by_type
        }
    
    def run(self):
        """执行导出流程"""
        print("\n" + "="*50)
        print("CS2 道具数据导出工具")
        print("="*50)
        
        # 1. 加载已批准的道具
        print("\n[加载] 已批准道具...")
        all_utilities = self.load_utilities()
        
        if not all_utilities:
            print("[错误] 没有已批准的道具")
            print("请先审核并批准一些道具")
            return
        
        # 3. 按地图分组
        utilities_by_map = {}
        for utility in all_utilities:
            map_name = utility.get('map', 'unknown')
            if map_name not in utilities_by_map:
                utilities_by_map[map_name] = []
            utilities_by_map[map_name].append(utility)
        
        # 4. 导出每个地图的数据
        maps_summary = []
        
        for map_name, utilities in utilities_by_map.items():
            print(f"\n[处理] 地图: {map_name} ({len(utilities)} 个道具)")
            
            exported_utilities = []
            
            for idx, utility in enumerate(utilities, 1):
                print(f"\n  道具 {idx}/{len(utilities)}: {utility.get('type')}")
                
                # 生成ID（使用hash值）
                utility_id = self.generate_utility_id(utility)
                
                # 导出截图
                screenshots = self.export_screenshots(utility, utility_id, map_name, utility.get('type'))
                
                # 转换数据格式
                if screenshots:  # 只导出有截图的道具
                    transformed = self.transform_utility_data(utility, utility_id, screenshots)
                    exported_utilities.append(transformed)
            
            # 保存地图数据
            if exported_utilities:
                self.export_map_data(map_name, exported_utilities)
                
                maps_summary.append({
                    'name': map_name,
                    'display_name': map_name.replace('de_', '').title(),
                    'utility_count': len(exported_utilities),
                    'data_file': f'data/{map_name}.json'
                })
        
        # 5. 导出索引
        print("\n[生成] 索引文件...")
        self.export_index(maps_summary)
        
        # 6. 完成
        print("\n" + "="*50)
        print("[完成] 导出完成！")
        print("="*50)
        print(f"\n[输出] 目录: {self.output_dir.absolute()}")
        print(f"[统计] 共导出 {sum(m['utility_count'] for m in maps_summary)} 个道具")


if __name__ == '__main__':
    exporter = UtilityExporter()
    exporter.run()
