#!/usr/bin/env python3
"""
CS2 道具自动截图测试脚本
用于测试截图效果，每次运行会覆盖测试文件夹中的截图
不影响主程序的截图文件
"""

import time
import json
import math
import pyperclip
import keyboard
import shutil
import os
from pathlib import Path

class CS2ScreenshotTester:
    def __init__(self, utilities_file, test_output_dir='output/screenshots_test', 
                 console_delay=1.5, screenshot_key='F12'):
        self.utilities_file = utilities_file
        self.test_output_dir = test_output_dir
        self.utilities = []
        self.console_delay = console_delay
        self.screenshot_key = screenshot_key
        self.should_stop = False
        
        # 创建测试目录（如果存在则清空）
        self.setup_test_directory()
        
        self.cs2_screenshot_dir = self.find_cs2_screenshot_dir()
        self.load_utilities()
        
        # 绑定 - 键强制停止
        keyboard.on_press_key('-', self.on_stop_key)
    
    def on_stop_key(self, event):
        """按下 - 键时强制停止"""
        self.should_stop = True
        print("\n\n🛑 检测到 - 键，正在停止...")
    
    def setup_test_directory(self):
        """设置测试目录，每次运行前清空"""
        test_path = Path(self.test_output_dir)
        
        if test_path.exists():
            print(f"🗑️  清空测试目录: {test_path}")
            shutil.rmtree(test_path)
        
        test_path.mkdir(parents=True, exist_ok=True)
        print(f"📁 创建测试目录: {test_path.absolute()}")
    
    def load_utilities(self):
        """加载道具数据"""
        with open(self.utilities_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        all_utilities = []
        
        # 判断数据格式
        if isinstance(data, list):
            all_utilities = data
        elif isinstance(data, dict):
            for map_name, map_data in data.items():
                if not isinstance(map_data, dict):
                    continue
                for util_type, type_data in map_data.items():
                    if not isinstance(type_data, dict):
                        continue
                    if 'utilities' in type_data:
                        all_utilities.extend(type_data['utilities'])
        
        self.utilities = all_utilities
        
        print(f"✅ 已加载 {len(self.utilities)} 个道具用于测试")
        
        if self.utilities:
            # 显示前3个道具信息
            print("\n📋 测试道具列表（前3个）：")
            for i, util in enumerate(self.utilities[:3], 1):
                map_name = util.get('map', 'unknown')
                util_type = util.get('type', 'unknown')
                team = util.get('team', 'Unknown')
                thrower = util.get('thrower', 'unknown')
                print(f"   {i}. {map_name} - {util_type} [{team}] - {thrower}")
            
            if len(self.utilities) > 3:
                print(f"   ... 还有 {len(self.utilities) - 3} 个道具")
    
    def find_cs2_screenshot_dir(self):
        """查找CS2截图目录"""
        possible_paths = [
            r"D:\Game\Steam\userdata\418027410\760\remote\730\screenshots",
            r"C:\Program Files (x86)\Steam\userdata\418027410\760\remote\730\screenshots",
        ]
        
        steam_paths = [
            r"D:\Game\Steam\userdata",
            r"C:\Program Files (x86)\Steam\userdata",
        ]
        
        for steam_path in steam_paths:
            if os.path.exists(steam_path):
                try:
                    for user_id in os.listdir(steam_path):
                        screenshot_path = os.path.join(steam_path, user_id, "760", "remote", "730", "screenshots")
                        if os.path.exists(screenshot_path):
                            possible_paths.insert(0, screenshot_path)
                except:
                    pass
        
        for path in possible_paths:
            if os.path.exists(path):
                print(f"✅ 找到CS2截图目录: {path}")
                return path
        
        print(f"⚠️  未找到CS2截图目录")
        return None
    
    def send_command(self, command):
        """发送命令到控制台"""
        pyperclip.copy(command)
        keyboard.press_and_release('`')
        time.sleep(0.1)
        keyboard.press_and_release('ctrl+v')
        time.sleep(0.1)
        keyboard.press_and_release('enter')
        time.sleep(0.1)
        keyboard.press_and_release('esc')
        time.sleep(self.console_delay)
    
    def send_command_batch(self, command):
        """批量初始化指令"""
        pyperclip.copy(command)
        keyboard.press_and_release('ctrl+v')
        time.sleep(0.01)
        keyboard.press_and_release('enter')
        time.sleep(0.01)
    
    def take_screenshot(self, filename):
        """使用绑定键截图"""
        keyboard.press_and_release(self.screenshot_key)
        time.sleep(1.0)
        
        if self.cs2_screenshot_dir and os.path.exists(self.cs2_screenshot_dir):
            return self.find_and_rename_latest_screenshot(filename)
        return False
    
    def find_and_rename_latest_screenshot(self, target_name):
        """查找最新的截图文件并重命名"""
        try:
            files = []
            for f in os.listdir(self.cs2_screenshot_dir):
                if f.endswith(('.tga', '.jpg', '.jpeg', '.png')):
                    full_path = os.path.join(self.cs2_screenshot_dir, f)
                    files.append((full_path, os.path.getmtime(full_path)))
            
            if not files:
                return False
            
            latest_file = max(files, key=lambda x: x[1])[0]
            ext = os.path.splitext(latest_file)[1]
            
            source_renamed = os.path.join(self.cs2_screenshot_dir, f"{target_name}{ext}")
            dest_file = os.path.join(self.test_output_dir, f"{target_name}{ext}")
            
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    shutil.move(latest_file, source_renamed)
                    shutil.copy2(source_renamed, dest_file)
                    print(f"      ✅ 已保存")
                    return True
                except PermissionError:
                    if attempt < max_retries - 1:
                        time.sleep(0.5)
                        continue
                    else:
                        raise
            
        except Exception as e:
            print(f"      ⚠️  保存失败: {e}")
            return False
    
    def test_utility(self, utility, index):
        """测试单个道具的3张截图"""
        throw_type = utility.get('throw_type_name', '未知')
        util_type = utility.get('type', 'unknown')
        team = utility.get('team', 'UNKNOWN')
        
        print(f"\n{'='*60}")
        print(f"📍 测试道具 {index}/{len(self.utilities)}: {utility.get('thrower', 'unknown')} [{team}]")
        print(f"   地图: {utility.get('map', 'unknown')}")
        print(f"   类型: {util_type} | 投掷方式: {throw_type}")
        print(f"{'='*60}")
        
        pos = utility.get('position') or utility.get('throw_position')
        angles = utility.get('angles') or utility.get('throw_angles')
        land_pos = utility.get('land_position')
        
        if not pos or not angles or not land_pos:
            print(f"   ⚠️  道具数据不完整，跳过")
            return
        
        map_name = utility.get('map', 'de_dust2')
        util_hash = utility['hash']
        filename_base = f"test_{index}_{map_name}_{util_hash[:8]}"
        
        # 准备准星图指令
        if 'command' in utility:
            crosshair_cmd = utility['command']
        else:
            crosshair_cmd = f"setpos {pos['x']} {pos['y']} {pos['z']}; setang {angles['pitch']} {angles['yaw']} 0"
        
        print(f"\n  📸 1/3 准星图（第一人称）...")
        print(f"     指令: {crosshair_cmd}")
        self.send_command(crosshair_cmd)
        time.sleep(0.3)
        self.take_screenshot(f"{filename_base}_crosshair")
        
        # 开启 noclip
        print(f"     开启 noclip...")
        self.send_command("noclip")
        time.sleep(0.2)
        
        # 站位图 - 正上方俯视
        print(f"\n  📸 2/3 站位图（正上方俯视）...")
        
        cam_x = pos['x']
        cam_y = pos['y']
        cam_z = pos['z'] + 300  # 正上方300单位
        
        look_pitch = 90  # 完全向下看
        look_yaw = 0
        
        position_cmd = f"setpos {cam_x:.2f} {cam_y:.2f} {cam_z:.2f}; setang {look_pitch:.2f} {look_yaw:.2f} 0"
        print(f"     指令: {position_cmd}")
        
        self.send_command(position_cmd)
        time.sleep(0.3)
        self.take_screenshot(f"{filename_base}_position")
        
        # 落点图 - 俯视
        print(f"\n  📸 3/3 落点图（俯视）...")
        
        land_cam_x = land_pos['x']
        land_cam_y = land_pos['y']
        land_cam_z = land_pos['z'] + 64
        
        landing_cmd = f"setpos {land_cam_x:.2f} {land_cam_y:.2f} {land_cam_z:.2f}; setang 90 0 0"
        print(f"     指令: {landing_cmd}")
        
        self.send_command(landing_cmd)
        time.sleep(0.3)
        self.take_screenshot(f"{filename_base}_landing")
        
        # 关闭 noclip
        print(f"     关闭 noclip...")
        self.send_command("noclip")
        time.sleep(0.2)
        
        print(f"\n✅ 测试道具 {index} 完成")
        print(f"   截图已保存到: {os.path.abspath(self.test_output_dir)}")
    
    def run(self, test_count=3):
        """运行测试（默认测试前3个道具）"""
        print("\n" + "="*60)
        print("🧪 CS2 道具截图测试工具")
        print("="*60)
        
        if not self.utilities:
            print("❌ 没有可测试的道具数据")
            return
        
        actual_count = min(test_count, len(self.utilities))
        
        print(f"\n📊 测试信息:")
        print(f"   - 总道具数: {len(self.utilities)}")
        print(f"   - 本次测试: {actual_count} 个道具")
        print(f"   - 预计截图: {actual_count * 3} 张")
        print(f"   - 保存位置: {os.path.abspath(self.test_output_dir)}")
        print(f"   - 截图键: {self.screenshot_key}")
        
        print(f"\n💡 测试特点:")
        print(f"   ✅ 每次运行自动清空旧截图")
        print(f"   ✅ 截图保存在独立测试文件夹")
        print(f"   ✅ 不影响主程序截图")
        print(f"   ✅ 文件名包含序号便于识别")
        
        print("\n⚠️  准备工作：")
        print("  1. 确保游戏窗口处于前台")
        print("  2. 进入地图并选择队伍")
        print("  3. 脚本会自动执行初始化命令")
        
        print(f"\n⏱️  预计耗时: {actual_count * 3 * 2.5 / 60:.1f} 分钟")
        print("\n按 Enter 开始测试，或 Ctrl+C 取消...")
        
        try:
            input()
        except KeyboardInterrupt:
            print("\n❌ 已取消")
            return
        
        print("\n⚙️  初始化游戏环境...")
        print("   3秒后开始...")
        time.sleep(3)
        
        # 打开控制台并初始化
        keyboard.press_and_release('`')
        time.sleep(0.3)
        
        print("   1/4 启用作弊模式...")
        self.send_command_batch("sv_cheats 1")
        
        print("   2/4 隐藏玩家模型...")
        self.send_command_batch("ent_fire !self alpha 0")
        
        print("   3/4 隐藏游戏UI和阴影...")
        self.send_command_batch("cl_draw_only_deathnotices 1")
        self.send_command_batch("r_drawviewmodel 0")
        self.send_command_batch("crosshair 0")
        self.send_command_batch("r_shadows 0")
        
        print(f"   4/4 绑定 {self.screenshot_key} 为截图键...")
        self.send_command_batch(f"bind {self.screenshot_key} screenshot")
        
        # 关闭控制台
        time.sleep(0.3)
        keyboard.press_and_release('esc')
        time.sleep(self.console_delay)
        
        print("\n✅ 初始化完成！")
        print("\n🚀 开始测试截图...")
        print("⚠️  按 - 键可强制停止 | 按 Ctrl+C 可暂停\n")
        
        try:
            for i in range(actual_count):
                if self.should_stop:
                    print(f"\n\n⏹️  测试已停止")
                    keyboard.unhook_all()
                    return
                
                self.test_utility(self.utilities[i], i + 1)
                
                if i < actual_count - 1:
                    print(f"\n⏸️  等待2秒后继续...")
                    time.sleep(2)
                    
        except KeyboardInterrupt:
            print(f"\n\n⏸️  测试已暂停")
            keyboard.unhook_all()
            return
        
        keyboard.unhook_all()
        
        print("\n" + "="*60)
        print("🎉 测试完成！")
        print("="*60)
        print(f"\n📁 测试截图已保存到:")
        print(f"   {os.path.abspath(self.test_output_dir)}")
        print(f"\n📊 生成截图:")
        print(f"   - 准星图: {actual_count} 张")
        print(f"   - 站位图: {actual_count} 张 (正上方俯视 ⭐)")
        print(f"   - 落点图: {actual_count} 张")
        print(f"   - 总计: {actual_count * 3} 张")
        
        print(f"\n📝 文件命名格式:")
        print(f"   test_{{序号}}_{{地图}}_{{hash}}_{{类型}}.jpg")
        print(f"   例如: test_1_de_dust2_6508bb18_position.jpg")
        
        print("\n💡 下一步:")
        print(f"   1. 打开文件夹查看截图效果")
        print(f"   2. 如需重新测试，直接运行脚本即可（会自动覆盖）")
        print(f"   3. 满意后可运行主程序: python screenshot.py")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='CS2道具截图测试工具')
    parser.add_argument('--file', type=str, default='../output/commands/selected_for_screenshot.json',
                        help='道具数据文件路径')
    parser.add_argument('--output', type=str, default='../output/screenshots_test',
                        help='测试截图输出目录')
    parser.add_argument('--count', type=int, default=3,
                        help='测试道具数量，默认3个')
    parser.add_argument('--delay', type=float, default=1.5,
                        help='控制台关闭后等待时间（秒），默认1.5秒')
    parser.add_argument('--key', type=str, default='F12',
                        help='截图绑定键，默认F12')
    
    args = parser.parse_args()
    
    if not Path(args.file).exists():
        print(f"❌ 错误: 找不到文件 {args.file}")
        print(f"\n💡 请先在管理后台选择道具并保存")
        return
    
    tester = CS2ScreenshotTester(
        args.file, 
        args.output, 
        args.delay, 
        args.key
    )
    tester.run(test_count=args.count)

if __name__ == '__main__':
    main()
