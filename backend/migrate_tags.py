"""
标签系统迁移脚本
将现有的JSON标签迁移到多表结构
"""
import sqlite3
import json
from pathlib import Path

def migrate_tags():
    """迁移标签数据"""
    
    # 数据库路径
    db_path = Path(__file__).parent / 'data' / 'yuuko.db'
    
    if not db_path.exists():
        print(f"❌ 数据库文件不存在: {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    print("=" * 60)
    print("🔄 开始迁移标签系统...")
    print("=" * 60)
    
    try:
        # 1. 创建新表
        print("\n📋 步骤1: 创建新表...")
        
        # 创建标签表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tags (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                description TEXT,
                color TEXT,
                created_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("✅ 创建 tags 表")
        
        # 创建关联表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS utility_tags (
                utility_hash TEXT NOT NULL,
                tag_id INTEGER NOT NULL,
                created_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (utility_hash, tag_id),
                FOREIGN KEY (utility_hash) REFERENCES utilities(hash) ON DELETE CASCADE,
                FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE
            )
        """)
        print("✅ 创建 utility_tags 关联表")
        
        # 创建索引
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_utility_tags_hash 
            ON utility_tags(utility_hash)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_utility_tags_tag 
            ON utility_tags(tag_id)
        """)
        print("✅ 创建索引")
        
        # 2. 迁移现有标签数据
        print("\n📦 步骤2: 迁移现有标签数据...")
        
        # 获取所有有标签的道具
        cursor.execute("""
            SELECT hash, tags 
            FROM utilities 
            WHERE tags IS NOT NULL AND tags != '[]' AND tags != ''
        """)
        
        utilities_with_tags = cursor.fetchall()
        
        if not utilities_with_tags:
            print("⚠️  没有找到需要迁移的标签数据")
        else:
            print(f"📊 找到 {len(utilities_with_tags)} 个道具有标签")
            
            # 收集所有唯一标签
            all_tags = set()
            utility_tag_map = {}  # {utility_hash: [tag_names]}
            
            for row in utilities_with_tags:
                utility_hash = row['hash']
                tags_json = row['tags']
                
                try:
                    tags = json.loads(tags_json) if isinstance(tags_json, str) else tags_json
                    
                    if isinstance(tags, list) and tags:
                        utility_tag_map[utility_hash] = tags
                        all_tags.update(tags)
                except Exception as e:
                    print(f"⚠️  解析标签失败 ({utility_hash[:8]}): {e}")
            
            print(f"📌 找到 {len(all_tags)} 个唯一标签")
            
            # 3. 插入标签到tags表
            print("\n✨ 步骤3: 插入标签到 tags 表...")
            
            tag_id_map = {}  # {tag_name: tag_id}
            
            for tag_name in sorted(all_tags):
                cursor.execute("""
                    INSERT OR IGNORE INTO tags (name) 
                    VALUES (?)
                """, (tag_name,))
                
                # 获取插入的tag_id
                cursor.execute("SELECT id FROM tags WHERE name = ?", (tag_name,))
                tag_id = cursor.fetchone()['id']
                tag_id_map[tag_name] = tag_id
                
                print(f"  ✓ {tag_name} (ID: {tag_id})")
            
            # 4. 建立关联关系
            print(f"\n🔗 步骤4: 建立道具-标签关联...")
            
            relation_count = 0
            for utility_hash, tag_names in utility_tag_map.items():
                for tag_name in tag_names:
                    tag_id = tag_id_map.get(tag_name)
                    if tag_id:
                        cursor.execute("""
                            INSERT OR IGNORE INTO utility_tags (utility_hash, tag_id)
                            VALUES (?, ?)
                        """, (utility_hash, tag_id))
                        relation_count += 1
            
            print(f"✅ 创建了 {relation_count} 个关联关系")
        
        # 5. 提交事务
        conn.commit()
        
        # 6. 验证迁移结果
        print("\n🔍 步骤5: 验证迁移结果...")
        
        cursor.execute("SELECT COUNT(*) as count FROM tags")
        tag_count = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) as count FROM utility_tags")
        relation_count = cursor.fetchone()['count']
        
        print(f"📊 tags 表: {tag_count} 条记录")
        print(f"📊 utility_tags 表: {relation_count} 条记录")
        
        # 显示前10个标签
        print("\n📋 标签列表（前10个）:")
        cursor.execute("""
            SELECT t.id, t.name, COUNT(ut.utility_hash) as usage_count
            FROM tags t
            LEFT JOIN utility_tags ut ON t.id = ut.tag_id
            GROUP BY t.id
            ORDER BY usage_count DESC
            LIMIT 10
        """)
        
        for row in cursor.fetchall():
            print(f"  • {row['name']:<20} (使用次数: {row['usage_count']})")
        
        print("\n" + "=" * 60)
        print("✅ 迁移完成！")
        print("=" * 60)
        print("\n⚠️  注意: 原有的 utilities.tags JSON字段仍然保留")
        print("   可以先测试新系统，确认无误后再删除该字段")
        print()
        
    except Exception as e:
        conn.rollback()
        print(f"\n❌ 迁移失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()


if __name__ == '__main__':
    migrate_tags()
