"""
检查标签系统是否正常工作
"""
import sqlite3
from pathlib import Path

db_path = Path(__file__).parent / 'data' / 'yuuko.db'

conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

print("=" * 60)
print("📊 标签系统检查")
print("=" * 60)

# 1. 检查tags表
print("\n1️⃣ tags 表内容:")
cursor.execute("SELECT * FROM tags ORDER BY name")
tags = cursor.fetchall()
print(f"   共 {len(tags)} 个标签:")
for tag in tags:
    print(f"   • ID:{tag['id']} - {tag['name']}")

# 2. 检查utility_tags表
print("\n2️⃣ utility_tags 关联表:")
cursor.execute("SELECT COUNT(*) as count FROM utility_tags")
count = cursor.fetchone()['count']
print(f"   共 {count} 个关联关系")

# 3. 检查某个道具的标签
print("\n3️⃣ 检查第一个道具的标签:")
cursor.execute("""
    SELECT u.hash, u.display_name, u.status
    FROM utilities u
    WHERE u.status = 'exported'
    LIMIT 1
""")
util = cursor.fetchone()
if util:
    print(f"   道具: {util['display_name']} ({util['hash'][:8]}...)")
    
    # 从新表获取标签
    cursor.execute("""
        SELECT t.name
        FROM tags t
        JOIN utility_tags ut ON t.id = ut.tag_id
        WHERE ut.utility_hash = ?
        ORDER BY t.name
    """, (util['hash'],))
    
    new_tags = [row['name'] for row in cursor.fetchall()]
    print(f"   新表中的标签: {new_tags}")
    
    # 从旧JSON字段获取标签
    cursor.execute("SELECT tags FROM utilities WHERE hash = ?", (util['hash'],))
    old_tags_json = cursor.fetchone()['tags']
    print(f"   旧JSON字段: {old_tags_json}")
else:
    print("   ⚠️  没有已导出的道具")

# 4. 显示所有有标签的道具
print("\n4️⃣ 所有有标签的道具（从新表）:")
cursor.execute("""
    SELECT DISTINCT u.hash, u.display_name, u.status
    FROM utilities u
    JOIN utility_tags ut ON u.hash = ut.utility_hash
    WHERE u.status = 'exported'
    ORDER BY u.display_name
    LIMIT 10
""")

for row in cursor.fetchall():
    cursor.execute("""
        SELECT t.name
        FROM tags t
        JOIN utility_tags ut ON t.id = ut.tag_id
        WHERE ut.utility_hash = ?
    """, (row['hash'],))
    
    tags = [t['name'] for t in cursor.fetchall()]
    print(f"   • {row['display_name']}: {tags}")

print("\n" + "=" * 60)
conn.close()
