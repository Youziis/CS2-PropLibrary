"""
删除所有待审核（screenshotted）的道具及其截图文件
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.database import Database

def delete_screenshotted_utilities():
    """删除所有待审核的道具及截图"""
    db = Database()
    
    print("=" * 60)
    print("删除待审核道具及截图")
    print("=" * 60)
    
    screenshots_dir = Path(__file__).parent.parent / 'output' / 'screenshots'
    
    with db.get_connection() as conn:
        cursor = conn.cursor()
        
        # 查询要删除的道具
        cursor.execute("""
            SELECT hash, screenshot_filename_base, type, map 
            FROM utilities 
            WHERE status = 'screenshotted'
        """)
        
        utilities_to_delete = cursor.fetchall()
        count = len(utilities_to_delete)
        
        if count == 0:
            print("\n✓ 没有找到待审核的道具")
            return
        
        print(f"\n找到 {count} 个待审核道具")
        
        # 显示按类型分组的统计
        cursor.execute("""
            SELECT type, COUNT(*) as count 
            FROM utilities 
            WHERE status = 'screenshotted'
            GROUP BY type
        """)
        
        print("\n类型分布：")
        for row in cursor.fetchall():
            print(f"  - {row['type']}: {row['count']} 个")
        
        print(f"\n将删除 {count} 个道具及其截图...")
        
        # 删除截图文件
        deleted_files = 0
        missing_files = 0
        
        print("\n正在删除截图文件...")
        for util in utilities_to_delete:
            screenshot_base = util['screenshot_filename_base']
            
            if not screenshot_base:
                continue
            
            # 删除三张截图
            for shot_type in ['position', 'crosshair', 'landing']:
                screenshot_file = screenshots_dir / f"{screenshot_base}_{shot_type}.jpg"
                
                if screenshot_file.exists():
                    try:
                        screenshot_file.unlink()
                        deleted_files += 1
                    except Exception as e:
                        print(f"  [警告] 删除失败: {screenshot_file.name} - {e}")
                else:
                    missing_files += 1
        
        print(f"  ✓ 已删除 {deleted_files} 个截图文件")
        if missing_files > 0:
            print(f"  ⚠ {missing_files} 个文件不存在（可能已被删除）")
        
        # 删除数据库记录
        print("\n正在删除数据库记录...")
        cursor.execute("""
            DELETE FROM utilities WHERE status = 'screenshotted'
        """)
        
        deleted_count = cursor.rowcount
        
        print(f"  ✓ 已删除 {deleted_count} 条数据库记录")
        
        # 显示剩余统计
        cursor.execute("""
            SELECT status, COUNT(*) as count 
            FROM utilities 
            GROUP BY status 
            ORDER BY status
        """)
        
        print("\n当前数据库状态：")
        print(f"{'状态':<20} {'数量':>10}")
        print("-" * 35)
        
        total = 0
        for row in cursor.fetchall():
            print(f"{row['status']:<20} {row['count']:>10}")
            total += row['count']
        
        print("-" * 35)
        print(f"{'总计':<20} {total:>10}")
    
    print("\n" + "=" * 60)
    print("✅ 删除完成！")
    print("=" * 60)

if __name__ == '__main__':
    delete_screenshotted_utilities()
