"""
重新分配sort_id，确保每个地图从起始值开始连续递增
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.database import Database

def reset_sort_ids():
    """重新分配所有已导出道具的sort_id"""
    db = Database()
    
    print("=" * 60)
    print("重新分配 sort_id")
    print("=" * 60)
    
    with db.get_connection() as conn:
        cursor = conn.cursor()
        
        # 为每个地图重新分配sort_id
        for map_name, map_prefix in db.MAP_ID_PREFIX.items():
            print(f"\n处理地图: {map_name} (前缀: {map_prefix})")
            
            # 获取该地图所有已导出的道具，按parse_time排序
            cursor.execute("""
                SELECT id, hash FROM utilities 
                WHERE map = ? AND status = 'exported'
                ORDER BY parse_time ASC
            """, (map_name,))
            
            rows = cursor.fetchall()
            
            if not rows:
                print(f"  ✓ 没有已导出的道具")
                continue
            
            # 从起始值开始连续分配
            start_id = map_prefix * 10000 + 1
            
            for index, row in enumerate(rows):
                new_sort_id = start_id + index
                cursor.execute("""
                    UPDATE utilities SET sort_id = ? WHERE id = ?
                """, (new_sort_id, row['id']))
            
            print(f"  ✓ 已更新 {len(rows)} 个道具")
            print(f"  ✓ sort_id 范围: {start_id} - {start_id + len(rows) - 1}")
    
    print("\n" + "=" * 60)
    print("✅ sort_id 重新分配完成！")
    print("=" * 60)
    
    # 验证结果
    print("\n验证结果:")
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT map, MIN(sort_id) as min, MAX(sort_id) as max, COUNT(*) as count 
            FROM utilities 
            WHERE sort_id IS NOT NULL 
            GROUP BY map 
            ORDER BY map
        """)
        
        print(f"{'地图':<15} {'最小ID':>10} {'最大ID':>10} {'数量':>8}")
        print("-" * 50)
        
        for row in cursor.fetchall():
            print(f"{row[0]:<15} {row[1]:>10} {row[2]:>10} {row[3]:>8}")

if __name__ == '__main__':
    reset_sort_ids()
