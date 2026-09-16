#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据导出工具（命令行）

将审核通过的道具导出到 public/ 目录，用于静态网站部署。
实际的导出动作与后台 /api/export 共用 backend/export_service.py，不再各写一份。
"""

import sys
import io
from pathlib import Path

# 设置标准输出编码为 UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 添加项目根目录到 sys.path 以导入 backend 模块
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir.resolve()))

from backend.database import Database
from backend.export_service import export_utilities_to_public


class UtilityExporter:
    """命令行导出器（保留原有构造参数以兼容旧调用方式）"""

    def __init__(self, input_data_dir=None, input_screenshots_dir=None, output_dir=None):
        self.input_data_dir = Path(input_data_dir) if input_data_dir else root_dir / 'output' / 'data'
        self.input_screenshots_dir = Path(input_screenshots_dir) if input_screenshots_dir else root_dir / 'output' / 'screenshots'
        self.output_dir = Path(output_dir) if output_dir else root_dir / 'public'

        (self.output_dir / 'data').mkdir(parents=True, exist_ok=True)
        (self.output_dir / 'images').mkdir(parents=True, exist_ok=True)

        self.db = Database()

    def load_utilities(self):
        """从数据库加载已批准和已导出的道具"""
        utilities = []

        approved = self.db.get_utilities(status='approved')
        if approved:
            utilities.extend(approved)
            print(f"[OK] 从数据库加载了 {len(approved)} 个待导出道具（状态=approved）")

        exported = self.db.get_utilities(status='exported')
        if exported:
            utilities.extend(exported)
            print(f"[OK] 从数据库加载了 {len(exported)} 个已导出道具（状态=exported，将重新导出）")

        if not utilities:
            print("[错误] 没有需要导出的道具")
            print("[提示] 请先在审核页面批准道具，或使用后端导出 API")
            return []

        print(f"[OK] 共加载了 {len(utilities)} 个道具")
        return utilities

    def run(self):
        """执行导出流程"""
        print("\n" + "=" * 50)
        print("CS2 道具数据导出工具")
        print("=" * 50)

        print("\n[加载] 已批准 / 已导出的道具...")
        all_utilities = self.load_utilities()
        if not all_utilities:
            return

        print("\n[处理] 写入 public 目录...")
        try:
            counts = export_utilities_to_public(
                self.db,
                all_utilities,
                public_dir=self.output_dir,
                screenshots_dir=self.input_screenshots_dir
            )
        except Exception as e:
            import traceback
            print(f"[错误] 导出失败: {e}")
            traceback.print_exc()
            return

        total_processed = 0
        for map_name, stat in counts.items():
            total_processed += stat['processed']
            print(f"  [OK] {map_name}: 处理 {stat['processed']} 个，地图内共 {stat['merged']} 个道具")

        print("\n" + "=" * 50)
        print("[完成] 导出完成！")
        print("=" * 50)
        print(f"\n[输出] 目录: {self.output_dir.absolute()}")
        print(f"[统计] 本次处理 {total_processed} 个道具，涉及 {len(counts)} 张地图")
        print("[说明] 本次导出不改变道具状态（状态变更由后台导出接口负责）")


if __name__ == '__main__':
    exporter = UtilityExporter()
    exporter.run()
