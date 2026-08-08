"""
道具数据管理模块
负责：解析、去重、数据流转
"""
import json
import os
from pathlib import Path
import hashlib

class UtilityManager:
    def __init__(self):
        self.base_path = Path(__file__).parent.parent.parent
        self.output_path = self.base_path / "output" / "data"
        
        # 数据文件路径
        self.raw_file = self.output_path / "parsed_raw.json"
        self.pending_file = self.output_path / "pending_review.json"
        self.approved_file = self.output_path / "approved.json"
        self.exported_file = self.output_path / "exported.json"
        
        # 确保文件存在
        self._ensure_files()
    
    def _ensure_files(self):
        """确保所有数据文件存在"""
        self.output_path.mkdir(parents=True, exist_ok=True)
        
        for file in [self.raw_file, self.pending_file, self.approved_file, self.exported_file]:
            if not file.exists():
                with open(file, 'w', encoding='utf-8') as f:
                    json.dump([], f, ensure_ascii=False, indent=2)
    
    def _generate_utility_hash(self, utility):
        """
        生成道具的唯一哈希值
        基于：位置、角度、落点
        """
        # 兼容不同的数据格式
        position = utility.get('throw_position') or utility.get('position', {})
        angles = utility.get('throw_angles') or utility.get('viewangles', {})
        landing = utility.get('landing_position')
        grenade_type = utility.get('type') or utility.get('grenade_type', 'unknown')
        map_name = utility.get('map') or utility.get('map_name', 'unknown')
        
        hash_string = f"{position['x']:.2f},{position['y']:.2f},{position['z']:.2f}"
        hash_string += f"|{angles['pitch']:.2f},{angles['yaw']:.2f}"
        hash_string += f"|{grenade_type}|{map_name}"
        
        # 如果有落点信息，加入哈希
        if landing:
            hash_string += f"|{landing['x']:.2f},{landing['y']:.2f},{landing['z']:.2f}"
        
        return hashlib.md5(hash_string.encode()).hexdigest()
    
    def load_data(self, file_type='raw'):
        """加载数据"""
        file_map = {
            'raw': self.raw_file,
            'pending': self.pending_file,
            'approved': self.approved_file,
            'exported': self.exported_file
        }
        
        with open(file_map[file_type], 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def save_data(self, data, file_type='raw'):
        """保存数据"""
        file_map = {
            'raw': self.raw_file,
            'pending': self.pending_file,
            'approved': self.approved_file,
            'exported': self.exported_file
        }
        
        with open(file_map[file_type], 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def add_parsed_utilities(self, new_utilities):
        """
        添加新解析的道具
        返回：(新增数量, 重复数量)
        """
        # 加载现有数据
        raw_data = self.load_data('raw')
        pending_data = self.load_data('pending')
        approved_data = self.load_data('approved')
        
        # 生成所有已存在道具的哈希集合
        existing_hashes = set()
        for utility in raw_data + pending_data + approved_data:
            if 'hash' in utility:
                existing_hashes.add(utility['hash'])
        
        # 筛选新道具
        truly_new = []
        duplicate_count = 0
        
        for utility in new_utilities:
            # 生成哈希
            util_hash = self._generate_utility_hash(utility)
            utility['hash'] = util_hash
            utility['status'] = 'pending'  # 标记为待审核
            
            if util_hash not in existing_hashes:
                truly_new.append(utility)
                existing_hashes.add(util_hash)
            else:
                duplicate_count += 1
        
        # 保存新道具
        if truly_new:
            # 添加到原始数据
            raw_data.extend(truly_new)
            self.save_data(raw_data, 'raw')
            
            # 添加到待审核
            pending_data.extend(truly_new)
            self.save_data(pending_data, 'pending')
        
        return len(truly_new), duplicate_count
    
    def get_pending_utilities(self, filters=None):
        """
        获取待审核道具
        filters: {'grenade_type': 'smoke', 'map_name': 'de_dust2'}
        """
        pending = self.load_data('pending')
        
        if not filters:
            return pending
        
        # 应用筛选
        filtered = pending
        for key, value in filters.items():
            filtered = [u for u in filtered if u.get(key) == value]
        
        return filtered
    
    def approve_utility(self, utility_hash, updated_info=None):
        """
        批准道具
        updated_info: 更新的信息字典
        """
        # 从 selected_for_screenshot.json 读取（包含 screenshot_id）
        screenshot_file = self.base_path / 'output' / 'commands' / 'selected_for_screenshot.json'
        pending_utilities = []
        
        if screenshot_file.exists():
            with open(screenshot_file, 'r', encoding='utf-8') as f:
                pending_utilities = json.load(f)
        
        approved = self.load_data('approved')
        
        # 找到待审核的道具
        utility = None
        utility_index = None
        for i, u in enumerate(pending_utilities):
            if u['hash'] == utility_hash:
                utility = u
                utility_index = i
                break
        
        if not utility:
            return False, "道具未找到"
        
        # 更新信息
        if updated_info:
            utility.update(updated_info)
        
        # 标记为已批准
        utility['status'] = 'approved'
        
        # 移动到已批准
        approved.append(utility)
        
        # 从 selected_for_screenshot.json 中移除
        pending_utilities.pop(utility_index)
        
        # 保存
        with open(screenshot_file, 'w', encoding='utf-8') as f:
            json.dump(pending_utilities, f, ensure_ascii=False, indent=2)
        
        self.save_data(approved, 'approved')
        
        return True, "批准成功"
    
    def reject_utility(self, utility_hash):
        """拒绝道具（从 selected_for_screenshot.json 中移除）"""
        screenshot_file = self.base_path / 'output' / 'commands' / 'selected_for_screenshot.json'
        
        if not screenshot_file.exists():
            return False, "截图文件不存在"
        
        with open(screenshot_file, 'r', encoding='utf-8') as f:
            utilities = json.load(f)
        
        # 找到并移除
        for i, u in enumerate(utilities):
            if u['hash'] == utility_hash:
                utilities.pop(i)
                
                # 保存
                with open(screenshot_file, 'w', encoding='utf-8') as f:
                    json.dump(utilities, f, ensure_ascii=False, indent=2)
                
                return True, "已拒绝"
        
        return False, "道具未找到"
    
    def delete_approved_utility(self, utility_hash):
        """删除已批准的道具（移回 selected_for_screenshot.json）"""
        approved = self.load_data('approved')
        screenshot_file = self.base_path / 'output' / 'commands' / 'selected_for_screenshot.json'
        
        # 找到已批准的道具
        utility = None
        for i, u in enumerate(approved):
            if u['hash'] == utility_hash:
                utility = approved.pop(i)
                break
        
        if not utility:
            return False, "道具未找到"
        
        # 恢复状态
        utility['status'] = 'pending'
        # 清除审核时添加的名称
        if 'display_name' in utility:
            del utility['display_name']
        
        # 移回 selected_for_screenshot.json
        if screenshot_file.exists():
            with open(screenshot_file, 'r', encoding='utf-8') as f:
                utilities = json.load(f)
        else:
            utilities = []
        
        utilities.append(utility)
        
        # 按 screenshot_id 排序
        utilities.sort(key=lambda u: u.get('screenshot_id', 'util999'))
        
        with open(screenshot_file, 'w', encoding='utf-8') as f:
            json.dump(utilities, f, ensure_ascii=False, indent=2)
        
        # 保存
        self.save_data(approved, 'approved')
        
        return True, "已删除并移回待审核"
    
    def delete_pending_utility(self, utility_hash):
        """删除待审核的道具（从 selected_for_screenshot.json 和 pending_review.json 中删除）"""
        screenshot_file = self.base_path / 'output' / 'commands' / 'selected_for_screenshot.json'
        pending = self.load_data('pending')
        raw = self.load_data('raw')
        
        found = False
        
        # 从 selected_for_screenshot.json 中删除
        if screenshot_file.exists():
            with open(screenshot_file, 'r', encoding='utf-8') as f:
                utilities = json.load(f)
            
            for i, u in enumerate(utilities):
                if u['hash'] == utility_hash:
                    utilities.pop(i)
                    found = True
                    
                    with open(screenshot_file, 'w', encoding='utf-8') as f:
                        json.dump(utilities, f, ensure_ascii=False, indent=2)
                    break
        
        # 从待审核列表中删除
        for i, u in enumerate(pending):
            if u['hash'] == utility_hash:
                pending.pop(i)
                found = True
                break
        
        # 也从原始数据中删除（保持数据一致性）
        for i, u in enumerate(raw):
            if u.get('hash') == utility_hash:
                raw.pop(i)
                break
        
        if not found:
            return False, "道具未找到"
        
        # 保存
        self.save_data(pending, 'pending')
        self.save_data(raw, 'raw')
        
        return True, "已永久删除"
    
    def mark_as_exported(self, utility_hashes):
        """
        标记道具为已导出
        utility_hashes: 道具哈希列表
        """
        approved = self.load_data('approved')
        exported = self.load_data('exported')
        
        moved_count = 0
        for util_hash in utility_hashes:
            # 从已批准中找到道具
            utility = None
            for i, u in enumerate(approved):
                if u['hash'] == util_hash:
                    utility = approved.pop(i)
                    break
            
            if utility:
                utility['status'] = 'exported'
                utility['export_time'] = str(Path(__file__).parent.parent.parent)  # 临时占位，应该用datetime
                exported.append(utility)
                moved_count += 1
        
        # 保存
        self.save_data(approved, 'approved')
        self.save_data(exported, 'exported')
        
        return True, f"已标记 {moved_count} 个道具为已导出"
    
    def unexport_utility(self, utility_hash):
        """
        撤销导出（将已导出道具移回已批准状态）
        """
        exported = self.load_data('exported')
        approved = self.load_data('approved')
        
        # 从已导出中找到道具
        utility = None
        for i, u in enumerate(exported):
            if u['hash'] == utility_hash:
                utility = exported.pop(i)
                break
        
        if not utility:
            return False, "道具未找到"
        
        # 恢复状态并移回已批准
        utility['status'] = 'approved'
        if 'export_time' in utility:
            del utility['export_time']
        
        approved.append(utility)
        
        # 保存
        self.save_data(exported, 'exported')
        self.save_data(approved, 'approved')
        
        return True, "已撤销导出，道具已移回待导出列表"
    
    def edit_exported_utility(self, utility_hash, updated_info):
        """
        编辑已导出道具的信息
        """
        exported = self.load_data('exported')
        
        # 找到道具
        utility = None
        for u in exported:
            if u['hash'] == utility_hash:
                utility = u
                break
        
        if not utility:
            return False, "道具未找到"
        
        # 更新信息
        if updated_info:
            utility.update(updated_info)
        
        # 保存
        self.save_data(exported, 'exported')
        
        return True, "修改成功！需要重新导出才能在客户端生效"
    
    def get_statistics(self):
        """获取统计信息"""
        raw = self.load_data('raw')
        approved_file = self.load_data('approved')
        exported_file = self.load_data('exported')
        
        # 从 selected_for_screenshot.json 读取待审核道具（已截图的）
        screenshot_file = self.base_path / 'output' / 'commands' / 'selected_for_screenshot.json'
        pending_with_screenshots = 0
        approved_in_screenshot_file = 0
        
        if screenshot_file.exists():
            try:
                with open(screenshot_file, 'r', encoding='utf-8') as f:
                    screenshot_utilities = json.load(f)
                    for u in screenshot_utilities:
                        status = u.get('status', 'pending')
                        if status == 'pending':
                            pending_with_screenshots += 1
                        elif status == 'approved':
                            approved_in_screenshot_file += 1
            except:
                pass
        
        # 已批准数量 = approved.json + exported.json + selected_for_screenshot.json 中状态为 approved 的
        total_approved = len(approved_file) + len(exported_file) + approved_in_screenshot_file
        
        return {
            'total_parsed': len(raw),
            'pending_review': pending_with_screenshots,  # 已截图且待审核的数量
            'approved': total_approved,  # 包括已导出的
            'rejection_rate': 0  # 暂时不计算拒绝率
        }


if __name__ == "__main__":
    # 测试
    manager = UtilityManager()
    stats = manager.get_statistics()
    print("📊 统计信息:")
    print(f"  总解析: {stats['total_parsed']}")
    print(f"  待审核: {stats['pending_review']}")
    print(f"  已批准: {stats['approved']}")
