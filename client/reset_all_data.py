#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
完全重置系统 - 删除所有截图和数据，准备重新开始
"""

import os
import json
from pathlib import Path

def reset_all():
    """完全重置系统"""
    print("\n" + "="*70)
    print("  完全重置道具系统 - 删除所有截图和数据")
    print("="*70)
    
    # 路径配置
    base_dir = Path(__file__).resolve().parent.parent
    screenshots_dir = base_dir / 'output' / 'screenshots'
    data_dir = base_dir / 'output' / 'data'
    commands_dir = base_dir / 'output' / 'commands'
    public_data = base_dir / 'public' / 'data'
    public_images = base_dir / 'public' / 'images'
    
    # 统计信息
    screenshot_count = 0
    
    # 1. 删除所有截图
    print("\n[1] 删除截图文件...")
    if screenshots_dir.exists():
        for file in screenshots_dir.glob('*.jpg'):
            try:
                file.unlink()
                screenshot_count += 1
            except Exception as e:
                print(f"  [错误] 无法删除 {file.name}: {e}")
        print(f"  [OK] 已删除 {screenshot_count} 个截图文件")
    else:
        print("  [警告] 截图目录不存在")
    
    # 2. 清空数据文件
    print("\n[2] 清空数据文件...")
    
    # 列表类型的文件
    list_files = ['pending_review.json', 'approved.json', 'exported.json', 'parsed_raw.json']
    for filename in list_files:
        filepath = data_dir / filename
        if filepath.exists():
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump([], f, ensure_ascii=False, indent=2)
            print(f"  [OK] 已清空 {filename}")
    
    # 字典类型的文件
    dict_files = ['screenshot_index.json']
    for filename in dict_files:
        filepath = data_dir / filename
        if filepath.exists():
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump({}, f, ensure_ascii=False, indent=2)
            print(f"  [OK] 已清空 {filename}")
    
    # 3. 清空 commands 目录
    print("\n[3] 清空命令文件...")
    if commands_dir.exists():
        for file in commands_dir.glob('*.json'):
            try:
                file.unlink()
                print(f"  [OK] 已删除 {file.name}")
            except Exception as e:
                print(f"  [错误] 无法删除 {file.name}: {e}")
    
    # 4. 清空 public 目录
    print("\n[4] 清空前台数据...")
    
    deleted_data = 0
    if public_data.exists():
        for file in public_data.glob('*.json'):
            try:
                file.unlink()
                deleted_data += 1
            except Exception as e:
                print(f"  [错误] 无法删除 {file.name}: {e}")
    
    deleted_images = 0
    if public_images.exists():
        for subdir in public_images.rglob('*'):
            if subdir.is_file():
                try:
                    subdir.unlink()
                    deleted_images += 1
                except Exception as e:
                    print(f"  [错误] 无法删除 {subdir.name}: {e}")
    
    print(f"  [OK] 已删除 {deleted_data} 个数据文件")
    print(f"  [OK] 已删除 {deleted_images} 个前台图片")
    
    # 完成
    print("\n" + "="*70)
    print("  [完成] 重置完成！")
    print("="*70)
    
    print(f"""
[统计] 删除内容：
  - 截图文件: {screenshot_count} 个
  - 数据文件: {deleted_data} 个
  - 前台图片: {deleted_images} 个

[已清空] 以下数据文件已重置为空：
  - output/data/parsed_raw.json
  - output/data/pending_review.json
  - output/data/approved.json
  - output/data/exported.json
  - output/data/screenshot_index.json

[下一步] 重新开始工作流：
  1. 解析 demo: 在后台管理界面点击"解析"
  2. 选择道具: 前往"选择道具"标签，勾选要截图的道具
  3. 保存选择: 点击"保存选择并准备截图"
  4. 运行截图: python client/screenshot.py
  5. 创建索引: python client/create_screenshot_index.py
  6. 刷新后台审核页面进行审核
""")

if __name__ == '__main__':
    confirm = input("\n确定要重置所有数据吗？这将删除所有截图！(yes/no): ")
    if confirm.lower() == 'yes':
        reset_all()
    else:
        print("\n[取消] 未执行重置操作")
