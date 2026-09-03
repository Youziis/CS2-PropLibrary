"""
清理sort_id：只保留exported状态道具的sort_id，并重新连续分配
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.database import Database

def cleanup_and_reset_sort_ids():
    """清理并重新分配sort_id"""
    db = Database()
    
    print("=" * 60)
    print("清理并重新分配 sort_id")
    print("=" * 60)
    
    with db.get_connection() as conn:
        cursor = conn.cursor()
        
        # 第一步：清除所有非exported状态道具的sort_id
        print("\n第一步：清除非exported状态道具的sort_id...")
        cursor.execute("""
            UPDATE utilities 
            SET sort_id = NULL 
            WHERE status != 'exported' AND sort_id IS NOT NULL
        """)
        cleared_count = cursor.rowcount
        print(f"  ✓ 已清除 {cleared_count} 个非exported道具的sort_id")
        
        # 第二步：为每个地图的exported道具重新连续分配sort_id
        print("\n第二步：为exported道具重新分配sort_id...")
        
        for map_name, map_prefix in db.MAP_ID_PREFIX.items():
            # 获取该地图所有已导出的道具，按parse_time排序
            cursor.execute("""
                SELECT id, hash FROM utilities 
                WHERE map = ? AND status = 'exported'
                ORDER BY parse_time ASC
            """, (map_name,))
            
            rows = cursor.fetchall()
            
            if not rows:
                continue
            
            # 从起始值开始连续分配
            start_id = map_prefix * 10000 + 1
            
            for index, row in enumerate(rows):
                new_sort_id = start_id + index
                cursor.execute("""
                    UPDATE utilities SET sort_id = ? WHERE id = ?
                """, (new_sort_id, row['id']))
            
            print(f"  ✓ {map_name}: {start_id} - {start_id + len(rows) - 1} (共 {len(rows)} 个)")
    
    print("\n" + "=" * 60)
    print("✅ 清理和重新分配完成！")
    print("=" * 60)
    
    # 验证结果
    print("\n最终结果:")
    with db.get_connection() as conn:
        cursor = conn.cursor()
        
        # 所有有sort_id的道具
        cursor.execute("""
            SELECT map, status, COUNT(*) as count 
            FROM utilities 
            WHERE sort_id IS NOT NULL 
            GROUP BY map, status 
            ORDER BY map, status
        """)
        
        print(f"\n{'地图':<15} {'状态':<15} {'数量':>8}")
        print("-" * 45)
        
        for row in cursor.fetchall():
            print(f"{row[0]:<15} {row[1]:<15} {row[2]:>8}")
        
        # 每个地图的sort_id范围
        cursor.execute("""
            SELECT map, MIN(sort_id) as min, MAX(sort_id) as max, COUNT(*) as count 
            FROM utilities 
            WHERE sort_id IS NOT NULL 
            GROUP BY map 
            ORDER BY map
        """)
        
        print(f"\n{'地图':<15} {'最小ID':>10} {'最大ID':>10} {'数量':>8}")
        print("-" * 50)
        
        for row in cursor.fetchall():
            print(f"{row[0]:<15} {row[1]:>10} {row[2]:>10} {row[3]:>8}")

if __name__ == '__main__':
    cleanup_and_reset_sort_ids()
