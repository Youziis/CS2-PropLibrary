"""
删除数据库中所有 status='parsed' 的道具条目
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.database import Database

def delete_parsed_utilities():
    """删除所有已解析但未处理的道具"""
    db = Database()
    
    print("=" * 60)
    print("删除 status='parsed' 的道具")
    print("=" * 60)
    
    # 先统计数量
    with db.get_connection() as conn:
        cursor = conn.cursor()
        
        # 查询要删除的数量
        cursor.execute("""
            SELECT COUNT(*) as count FROM utilities WHERE status = 'parsed'
        """)
        count = cursor.fetchone()['count']
        
        if count == 0:
            print("\n✓ 没有找到 status='parsed' 的道具")
            return
        
        print(f"\n找到 {count} 个 status='parsed' 的道具")
        
        # 确认删除
        confirm = input(f"\n确认删除这 {count} 个道具吗？(yes/no): ")
        
        if confirm.lower() != 'yes':
            print("\n已取消删除")
            return
        
        # 执行删除
        cursor.execute("""
            DELETE FROM utilities WHERE status = 'parsed'
        """)
        
        deleted_count = cursor.rowcount
        
        print(f"\n✅ 成功删除 {deleted_count} 个道具")
        
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

if __name__ == '__main__':
    delete_parsed_utilities()
