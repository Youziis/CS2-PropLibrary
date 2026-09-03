"""
诊断工具：检查数据库中各类道具的数量分布
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.database import Database

def diagnose_utilities():
    """诊断道具数据"""
    db = Database()
    
    print("=" * 60)
    print("道具类型分布诊断")
    print("=" * 60)
    
    with db.get_connection() as conn:
        cursor = conn.cursor()
        
        # 按类型和状态统计
        cursor.execute("""
            SELECT type, status, COUNT(*) as count 
            FROM utilities 
            GROUP BY type, status 
            ORDER BY type, status
        """)
        
        print("\n按类型和状态分组：")
        print(f"{'类型':<15} {'状态':<15} {'数量':>10}")
        print("-" * 45)
        
        current_type = None
        type_total = 0
        
        for row in cursor.fetchall():
            if current_type and current_type != row['type']:
                print(f"{'小计':<15} {'':<15} {type_total:>10}")
                print("-" * 45)
                type_total = 0
            
            current_type = row['type']
            type_total += row['count']
            print(f"{row['type']:<15} {row['status']:<15} {row['count']:>10}")
        
        if type_total > 0:
            print(f"{'小计':<15} {'':<15} {type_total:>10}")
        
        # 总统计
        cursor.execute("""
            SELECT type, COUNT(*) as count 
            FROM utilities 
            GROUP BY type 
            ORDER BY type
        """)
        
        print("\n" + "=" * 45)
        print("总计（按类型）：")
        print(f"{'类型':<15} {'总数量':>10}")
        print("-" * 45)
        
        total = 0
        for row in cursor.fetchall():
            print(f"{row['type']:<15} {row['count']:>10}")
            total += row['count']
        
        print("-" * 45)
        print(f"{'总计':<15} {total:>10}")
        
        # 检查是否有手雷
        cursor.execute("""
            SELECT COUNT(*) as count 
            FROM utilities 
            WHERE type = 'hegrenade'
        """)
        
        hegrenade_count = cursor.fetchone()['count']
        
        print("\n" + "=" * 60)
        if hegrenade_count == 0:
            print("⚠️  警告：数据库中没有手雷（hegrenade）类型的道具！")
        else:
            print(f"✓ 数据库中有 {hegrenade_count} 个手雷")
        print("=" * 60)

if __name__ == '__main__':
    diagnose_utilities()
