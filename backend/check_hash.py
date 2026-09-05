"""检查数据库中hash的实际格式"""
from database import Database

db = Database()

# 获取一些已导出的道具
utils = db.get_utilities(status='exported', limit=10)

print("=" * 70)
print("数据库中的Hash格式检查")
print("=" * 70)
print()

if not utils:
    print("❌ 没有找到已导出的道具")
else:
    print(f"找到 {len(utils)} 个已导出道具:\n")
    for i, u in enumerate(utils, 1):
        hash_val = u.get('hash', '无')
        name = u.get('display_name') or u.get('name', '未命名')
        map_name = u.get('map', '未知')
        print(f"{i}. Hash: {hash_val}")
        print(f"   名称: {name}")
        print(f"   地图: {map_name}")
        print()

# 测试搜索6c7a61fa
print("\n" + "=" * 70)
print("测试搜索: 6c7a61fa")
print("=" * 70)

with db.get_connection() as conn:
    cursor = conn.cursor()
    
    # 尝试LIKE查询
    cursor.execute("""
        SELECT hash, display_name, name, map 
        FROM utilities 
        WHERE hash LIKE ? 
        LIMIT 5
    """, ('6c7a61fa%',))
    
    results = cursor.fetchall()
    
    if results:
        print(f"✅ 找到 {len(results)} 个匹配结果:")
        for row in results:
            print(f"   Hash: {row['hash']}")
            print(f"   名称: {row['display_name'] or row['name']}")
            print(f"   地图: {row['map']}")
            print()
    else:
        print("❌ 没有找到匹配的道具")
        print("\n尝试搜索所有包含'6c7a61fa'的hash:")
        cursor.execute("""
            SELECT hash, display_name, name 
            FROM utilities 
            WHERE hash LIKE ? 
            LIMIT 5
        """, ('%6c7a61fa%',))
        results2 = cursor.fetchall()
        if results2:
            print(f"找到 {len(results2)} 个结果:")
            for row in results2:
                print(f"   Hash: {row['hash']}")
        else:
            print("完全没有找到")
