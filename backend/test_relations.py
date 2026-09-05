"""
测试关联管理功能
"""
from database import Database

def test_relations():
    db = Database()
    
    print("=" * 70)
    print("🧪 测试关联管理功能")
    print("=" * 70)
    print()
    
    # 获取已导出的道具
    utilities = db.get_utilities(status='exported')
    print(f"✅ 找到 {len(utilities)} 个已导出道具")
    
    if len(utilities) < 2:
        print("❌ 至少需要2个已导出道具才能测试关联功能")
        print("   请先在管理后台批准并导出一些道具")
        return
    
    # 选择前3个道具进行测试
    test_utils = utilities[:min(3, len(utilities))]
    hashes = [u['hash'] for u in test_utils]
    
    print(f"\n测试道具：")
    for u in test_utils:
        print(f"  - {u['display_name'] or u.get('name', '未命名')} ({u['hash'][:8]}...)")
    
    print(f"\n1️⃣  测试批量关联...")
    count = db.batch_link_utilities(hashes, combo_group="test_combo")
    print(f"   ✅ 创建了 {count} 个关联")
    
    print(f"\n2️⃣  测试查询关联...")
    for hash in hashes:
        related = db.get_related_utilities(hash)
        print(f"   道具 {hash[:8]}... 有 {len(related)} 个关联")
    
    print(f"\n3️⃣  测试添加单个关联...")
    if len(utilities) >= 4:
        fourth = utilities[3]
        success = db.add_utility_relation(hashes[0], fourth['hash'], bidirectional=True)
        if success:
            print(f"   ✅ 成功添加 {hashes[0][:8]}... 和 {fourth['hash'][:8]}... 的关联")
            count = db.get_relation_count(hashes[0])
            print(f"   道具 {hashes[0][:8]}... 现在有 {count} 个关联")
    
    print(f"\n4️⃣  测试移除关联...")
    success = db.remove_utility_relation(hashes[0], hashes[1], bidirectional=True)
    if success:
        print(f"   ✅ 成功移除 {hashes[0][:8]}... 和 {hashes[1][:8]}... 的关联")
        count = db.get_relation_count(hashes[0])
        print(f"   道具 {hashes[0][:8]}... 现在有 {count} 个关联")
    
    print(f"\n5️⃣  测试清空关联...")
    success = db.clear_all_relations(hashes[0])
    if success:
        print(f"   ✅ 成功清空 {hashes[0][:8]}... 的所有关联")
        count = db.get_relation_count(hashes[0])
        print(f"   道具 {hashes[0][:8]}... 现在有 {count} 个关联")
    
    print(f"\n✅ 测试完成！")
    print()

if __name__ == '__main__':
    test_relations()
