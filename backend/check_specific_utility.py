"""
检查特定道具的标签
"""
import sqlite3
from pathlib import Path

db_path = Path(__file__).parent / 'data' / 'yuuko.db'
target_hash = '4fded929bbf6d29b'

conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

print("=" * 60)
print(f"📊 检查道具: {target_hash}")
print("=" * 60)

# 1. 查看道具基本信息
cursor.execute("""
    SELECT hash, display_name, status, tags
    FROM utilities
    WHERE hash = ?
""", (target_hash,))

util = cursor.fetchone()
if util:
    print(f"\n✅ 道具信息:")
    print(f"   Hash: {util['hash']}")
    print(f"   名称: {util['display_name']}")
    print(f"   状态: {util['status']}")
    print(f"   旧JSON字段tags: {util['tags']}")
else:
    print(f"\n❌ 未找到道具 {target_hash}")
    conn.close()
    exit()

# 2. 查看utility_tags表中的关联
print(f"\n📋 utility_tags 表中的关联:")
cursor.execute("""
    SELECT ut.tag_id, ut.created_time, t.name
    FROM utility_tags ut
    LEFT JOIN tags t ON ut.tag_id = t.id
    WHERE ut.utility_hash = ?
""", (target_hash,))

relations = cursor.fetchall()
if relations:
    print(f"   共 {len(relations)} 个标签:")
    for rel in relations:
        print(f"   • Tag ID:{rel['tag_id']} - {rel['name']} (创建时间: {rel['created_time']})")
else:
    print(f"   ⚠️  没有标签关联")

# 3. 测试删除
print(f"\n🧪 测试删除该道具的所有标签...")
cursor.execute("DELETE FROM utility_tags WHERE utility_hash = ?", (target_hash,))
deleted_count = cursor.rowcount
print(f"   删除了 {deleted_count} 个关联")

# 不提交，只是测试
conn.rollback()
print(f"   (已回滚，未实际删除)")

print("\n" + "=" * 60)
conn.close()
