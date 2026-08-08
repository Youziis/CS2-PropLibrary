"""
同步待审核道具
将 parsed_raw.json 中状态为 pending 的道具同步到 pending_review.json
"""
import json
from pathlib import Path

def main():
    print("=" * 70)
    print("[同步] 同步待审核道具")
    print("=" * 70)
    
    base_path = Path(__file__).resolve().parent.parent / "output" / "data"
    
    raw_file = base_path / "parsed_raw.json"
    pending_file = base_path / "pending_review.json"
    approved_file = base_path / "approved.json"
    
    # 读取数据
    with open(raw_file, 'r', encoding='utf-8') as f:
        raw_data = json.load(f)
    
    with open(approved_file, 'r', encoding='utf-8') as f:
        approved_data = json.load(f)
    
    print(f"[加载] parsed_raw.json: {len(raw_data)} 个道具")
    print(f"[加载] approved.json: {len(approved_data)} 个道具")
    
    # 获取已批准的哈希集合
    approved_hashes = {u.get('hash') for u in approved_data if 'hash' in u}
    
    # 筛选出待审核的道具（在 raw 中但不在 approved 中）
    pending_data = []
    for util in raw_data:
        util_hash = util.get('hash')
        if util_hash and util_hash not in approved_hashes:
            # 确保状态为 pending
            util['status'] = 'pending'
            pending_data.append(util)
    
    print(f"[计算] 待审核道具: {len(pending_data)} 个")
    
    # 保存到 pending_review.json
    with open(pending_file, 'w', encoding='utf-8') as f:
        json.dump(pending_data, f, ensure_ascii=False, indent=2)
    
    print(f"[完成] 已同步 {len(pending_data)} 个道具到 pending_review.json")
    print("=" * 70)

if __name__ == '__main__':
    main()
