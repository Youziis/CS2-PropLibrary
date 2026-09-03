"""
清理JSON文件中的重复道具数据
基于hash字段去重，保留最新的数据（有sort_id的版本）
"""
import json
from pathlib import Path

def clean_duplicates():
    """清理所有地图JSON文件中的重复道具"""
    
    root_dir = Path(__file__).parent.parent
    data_dir = root_dir / 'public' / 'data'
    
    if not data_dir.exists():
        print("数据目录不存在！")
        return
    
    print("=" * 60)
    print("清理重复道具数据")
    print("=" * 60)
    
    # 获取所有地图JSON文件
    map_files = list(data_dir.glob('de_*.json'))
    
    if not map_files:
        print("没有找到地图数据文件")
        return
    
    total_removed = 0
    
    for map_file in map_files:
        map_name = map_file.stem
        print(f"\n处理: {map_name}")
        
        try:
            # 读取数据
            with open(map_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            utilities = data.get('utilities', [])
            original_count = len(utilities)
            
            # 使用hash去重，如果没有hash则使用id字段
            seen = {}
            
            for util in utilities:
                util_hash = util.get('hash')
                util_id = util.get('id')
                
                # 确定唯一标识符：优先使用hash，其次使用id
                if util_hash:
                    key = ('hash', util_hash)
                elif util_id:
                    key = ('id', util_id)
                else:
                    # 没有任何标识符，跳过
                    continue
                
                # 如果已存在该key
                if key in seen:
                    existing = seen[key]
                    # 优先保留有hash的版本
                    if util_hash and not existing.get('hash'):
                        seen[key] = util
                    # 如果都有hash，保留有sort_id的版本
                    elif util_hash and existing.get('hash'):
                        if util.get('sort_id') and not existing.get('sort_id'):
                            seen[key] = util
                        elif util.get('sort_id') and existing.get('sort_id'):
                            # 都有sort_id，保留较小的
                            if util['sort_id'] < existing['sort_id']:
                                seen[key] = util
                else:
                    seen[key] = util
            
            # 重建utilities列表
            deduplicated_utilities = list(seen.values())
            
            # 按sort_id排序
            deduplicated_utilities.sort(key=lambda u: u.get('sort_id', 999999))
            
            removed_count = original_count - len(deduplicated_utilities)
            
            if removed_count > 0:
                # 更新数据
                data['utilities'] = deduplicated_utilities
                
                # 保存
                with open(map_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                
                print(f"  ✓ 原有: {original_count} 个")
                print(f"  ✓ 去重后: {len(deduplicated_utilities)} 个")
                print(f"  ✓ 删除: {removed_count} 个重复")
                
                total_removed += removed_count
            else:
                print(f"  ✓ 无重复数据（共 {original_count} 个道具）")
        
        except Exception as e:
            print(f"  ✗ 处理失败: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 60)
    if total_removed > 0:
        print(f"✅ 清理完成！共删除 {total_removed} 个重复道具")
    else:
        print("✅ 没有发现重复数据")
    print("=" * 60)

if __name__ == '__main__':
    clean_duplicates()
