#!/usr/bin/env python3
"""
手动同步截图状态到数据库
根据截图文件夹中的图片文件，更新数据库中道具的状态
"""

import sys
import sqlite3
from pathlib import Path

def sync_screenshots():
    """同步截图状态到数据库"""
    # 获取脚本所在目录（client）
    script_dir = Path(__file__).parent.resolve()
    # 项目根目录是 client 的父目录
    project_root = script_dir.parent
    
    db_path = project_root / 'backend' / 'data' / 'yuuko.db'
    screenshots_dir = project_root / 'output' / 'screenshots'
    
    print(f"项目根目录: {project_root}")
    print(f"数据库路径: {db_path}")
    print(f"截图目录: {screenshots_dir}\n")
    
    if not db_path.exists():
        print(f"✗ 数据库不存在: {db_path}")
        print(f"✗ 请检查数据库文件是否在正确位置")
        return
    
    if not screenshots_dir.exists():
        print(f"✗ 截图目录不存在: {screenshots_dir}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 获取所有 selected 状态的道具
    cursor.execute("""
        SELECT hash, map, type FROM utilities 
        WHERE status = 'selected'
    """)
    selected_utils = cursor.fetchall()
    
    if not selected_utils:
        print("⚠️  没有找到 selected 状态的道具")
        conn.close()
        return
    
    print(f"找到 {len(selected_utils)} 个待同步的道具\n")
    
    updated = 0
    not_found = 0
    
    for util_hash, map_name, util_type in selected_utils:
        # 构建文件名前缀
        filename_base = f"{map_name}_{util_hash}"
        
        # 检查是否存在所有三张图片
        position_file = screenshots_dir / f"{filename_base}_position.jpg"
        crosshair_file = screenshots_dir / f"{filename_base}_crosshair.jpg"
        landing_file = screenshots_dir / f"{filename_base}_landing.jpg"
        
        if position_file.exists() and crosshair_file.exists() and landing_file.exists():
            # 更新数据库状态
            cursor.execute("""
                UPDATE utilities 
                SET status = 'screenshotted',
                    screenshot_filename_base = ?
                WHERE hash = ?
            """, (filename_base, util_hash))
            
            print(f"✓ {filename_base} - 已同步")
            updated += 1
        else:
            # 检查哪些文件缺失
            missing = []
            if not position_file.exists():
                missing.append('position')
            if not crosshair_file.exists():
                missing.append('crosshair')
            if not landing_file.exists():
                missing.append('landing')
            
            print(f"✗ {filename_base} - 缺少文件: {', '.join(missing)}")
            not_found += 1
    
    conn.commit()
    conn.close()
    
    print(f"\n{'='*60}")
    print(f"同步完成！")
    print(f"{'='*60}")
    print(f"✅ 成功同步: {updated} 个道具")
    if not_found > 0:
        print(f"⚠️  未找到截图: {not_found} 个道具")
    
    print(f"\n💡 下一步:")
    print(f"   1. 刷新管理后台: http://localhost:5000")
    print(f"   2. 点击'审核'标签页查看已截图的道具")

if __name__ == '__main__':
    sync_screenshots()
