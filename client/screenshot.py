#!/usr/bin/env python3
"""
CS2 道具自动截图脚本
使用键盘绑定方式自动截图
"""

import time
import json
import math
import pyperclip
import keyboard
import shutil
import os
from pathlib import Path

class CS2AutoScreenshot:
    def __init__(self, utilities_file, util_type=None, output_dir='output/screenshots', 
                 console_delay=1.5, screenshot_key='F12', eye_height_offset=64.0):
        self.utilities_file = utilities_file
        self.util_type = util_type
        self.output_dir = output_dir
        self.utilities = []
        self.current_index = 0
        self.screenshot_count = 0
        self.console_delay = console_delay
        self.screenshot_key = screenshot_key
        self.eye_height_offset = eye_height_offset
        self.should_stop = False
        
        os.makedirs(output_dir, exist_ok=True)
        self.cs2_screenshot_dir = self.find_cs2_screenshot_dir()
        self.load_utilities()
        
        # 绑定 - 键强制停止
        keyboard.on_press_key('-', self.on_stop_key)
    
    def on_stop_key(self, event):
        """按下 - 键时强制停止"""
        self.should_stop = True
        print("\n\n🛑 检测到 - 键，正在停止...")
    
    def load_utilities(self):
        """加载道具数据"""
        with open(self.utilities_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        all_utilities = []
        
        # 判断数据格式
        if isinstance(data, list):
            # 新格式：直接是列表 [{...}, {...}]
            all_utilities = data
        elif isinstance(data, dict):
            # 旧格式：嵌套字典 {map: {type: {utilities: [...]}}}
            for map_name, map_data in data.items():
                if not isinstance(map_data, dict):
                    continue
                for util_type, type_data in map_data.items():
                    if not isinstance(type_data, dict):
                        continue
                    if 'utilities' in type_data:
                        utilities_list = type_data['utilities']
                        if self.util_type:
                            if util_type == self.util_type:
                                all_utilities.extend(utilities_list)
                        else:
                            all_utilities.extend(utilities_list)
        
        # 如果指定了类型筛选，进行筛选
        if self.util_type:
            all_utilities = [u for u in all_utilities if u.get('type') == self.util_type]
        
        # ⚠️ 保持原始顺序，不要重新排序！
        # 这样截图顺序才能和 selected_for_screenshot.json 一致
        self.utilities = all_utilities
        
        # 统计队伍数量（仅用于显示）
        t_count = sum(1 for u in all_utilities if u.get('team') in ['TERRORIST', 'T'])
        ct_count = sum(1 for u in all_utilities if u.get('team') in ['CT'])
        
        print(f"✅ 已加载 {len(self.utilities)} 个道具")
        print(f"   - T道具: {t_count}")
        print(f"   - CT道具: {ct_count}")
        
        # 显示数据统计
        if self.utilities:
            has_velocity = sum(1 for u in self.utilities if 'vertical_velocity' in u)
            has_throw_type = sum(1 for u in self.utilities if 'throw_type_name' in u)
            print(f"   - 包含垂直速度信息: {has_velocity}/{len(self.utilities)}")
            print(f"   - 包含投掷方式信息: {has_throw_type}/{len(self.utilities)}")
    
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
        """发送命令到控制台（会关闭控制台）"""
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
        time.sleep(1.0)  # 增加等待时间，让Steam完成保存
        
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
            dest_file = os.path.join(self.output_dir, f"{target_name}{ext}")
            
            # 重试机制：最多尝试3次
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    shutil.move(latest_file, source_renamed)
                    shutil.copy2(source_renamed, dest_file)
                    print(f"      ✅ 已保存")
                    return True
                except PermissionError:
                    if attempt < max_retries - 1:
                        time.sleep(0.5)  # 等待0.5秒后重试
                        continue
                    else:
                        raise
            
        except Exception as e:
            print(f"      ⚠️  保存失败: {e}")
            return False
    
    def process_utility(self, utility, index):
        """处理单个道具的3张截图"""
        throw_type = utility.get('throw_type_name', '未知')
        velocity = utility.get('velocity_z', 'N/A')
        velocity_str = f"{velocity:.2f}" if isinstance(velocity, (int, float)) else velocity
        util_type = utility.get('type', 'unknown')
        team = utility.get('team', 'UNKNOWN')
        flight_time = utility.get('flight_time', 1.0)  # 飞行时间（秒）
        
        print(f"\n📍 道具 {index}/{len(self.utilities)}: {utility['thrower']} [{team}]")
        print(f"   投掷方式: {throw_type} | 垂直速度: {velocity_str} | 飞行时间: {flight_time:.2f}秒")
        
        # 兼容两种字段名：position 或 throw_position
        pos = utility.get('position') or utility.get('throw_position')
        angles = utility.get('angles') or utility.get('throw_angles')
        land_pos = utility.get('land_position')
        
        if not pos or not angles or not land_pos:
            print(f"   ⚠️  道具数据不完整，跳过")
            return
        
        # 使用 position（修正后的地板高度），与数据中的 command 一致
        print(f"   使用位置 (Z={pos['z']:.2f})")
        
        map_name = utility.get('map', 'de_dust2')
        util_hash = utility['hash']  # 使用hash值作为唯一标识
        filename_base = f"{map_name}_{util_hash}"
        
        # 💾 立即保存映射关系到道具数据中
        utility['screenshot_filename_base'] = filename_base
        
        # 准备描点图指令
        if 'command' in utility:
            crosshair_cmd = utility['command']
        else:
            crosshair_cmd = f"setpos {pos['x']} {pos['y']} {pos['z']}; setang {angles['pitch']} {angles['yaw']} 0"
        
        # 1. 描点图 - 第一人称视角，noclip关闭，准星在正中心
        print(f"  📸 1/3 描点图（准星正中心，noclip关闭）...")
        print(f"     描点图指令: {crosshair_cmd}")
        self.send_command(crosshair_cmd)
        time.sleep(0.3)
        self.take_screenshot(f"{filename_base}_crosshair")
        
        # 描点图截图完毕后，开启 noclip
        print(f"     开启 noclip...")
        self.send_command("noclip")  # 开启 noclip
        time.sleep(0.2)
        
        # 2. 站位图 - 沿投掷方向前进后看向站位脚位置
        print(f"  📸 2/3 站位图（第一人称）...")
        
        # 沿着投掷方向（yaw方向）前进
        yaw_rad = math.radians(angles['yaw'])
        forward_distance = 245  # 前进距离
        
        cam_x = pos['x'] + forward_distance * math.cos(yaw_rad)
        cam_y = pos['y'] + forward_distance * math.sin(yaw_rad)
        cam_z = pos['z'] + 100  # 向上100单位（降低高度让准星更准确）
        
        # 计算看向站位脚位置（地板高度）的角度
        dx = pos['x'] - cam_x
        dy = pos['y'] - cam_y
        dz = pos['z'] - cam_z  # 看向脚位置（地板高度）
        
        # 计算yaw（水平角度）
        look_yaw = math.degrees(math.atan2(dy, dx))
        
        # 计算pitch（俯仰角）- CS2的pitch正值表示向上，负值表示向下
        # 但从高处看低处时，需要反转符号
        horizontal_distance = math.sqrt(dx**2 + dy**2)
        look_pitch = -math.degrees(math.atan2(dz, horizontal_distance))
        
        position_cmd = f"setpos {cam_x:.2f} {cam_y:.2f} {cam_z:.2f}; setang {look_pitch:.2f} {look_yaw:.2f} 0"
        print(f"     站位图指令: {position_cmd}")
        
        self.send_command(position_cmd)
        time.sleep(0.3)
        self.take_screenshot(f"{filename_base}_position")
        
        # 3. 落点图 - 俯视图，第一人称
        print(f"  📸 3/3 落点图（俯视）...")
        
        # 移动到落点位置（眼睛高度）
        land_cam_x = land_pos['x']
        land_cam_y = land_pos['y']
        land_cam_z = land_pos['z'] + 64
        
        # pitch = 90 表示完全向下看
        landing_cmd = f"setpos {land_cam_x:.2f} {land_cam_y:.2f} {land_cam_z:.2f}; setang 90 0 0"
        print(f"     落点图指令: {landing_cmd}")
        
        self.send_command(landing_cmd)
        time.sleep(0.3)
        self.take_screenshot(f"{filename_base}_landing")
        
        # 落点图截图完毕后，关闭 noclip
        print(f"     关闭 noclip...")
        self.send_command("noclip")  # 关闭 noclip
        time.sleep(0.2)
    
    def run(self, start_from=1):
        """运行自动截图"""
        print("\n" + "="*50)
        print("CS2 道具自动截图工具")
        print("="*50)
        print(f"\n📊 共 {len(self.utilities)} 个道具")
        print(f"📷 预计生成 {len(self.utilities) * 3} 张截图")
        print(f"💾 保存位置: {os.path.abspath(self.output_dir)}")
        print(f"🎮 截图键: {self.screenshot_key}")
        print(f"🎯 模式: 第一人称 + 玩家隐身 + 隐藏UI")
        
        print("\n⚠️  重要准备：")
        print("  1. 确保游戏窗口处于前台")
        print("  2. 进入地图并选择队伍（CT或T）")
        print("  3. 脚本会自动执行所有命令：")
        print("     - sv_cheats 1")
        print("     - ent_fire !self alpha 0 (玩家隐身)")
        print("     - cl_draw_only_deathnotices 1 (隐藏UI)")
        print("     - r_drawviewmodel 0 (隐藏手臂)")
        print("     - crosshair 0 (隐藏准星)")
        print("     - r_shadows 0 (隐藏阴影)")
        print(f"     - bind {self.screenshot_key} screenshot")
        print("  4. noclip 会在每个道具截图时自动开启/关闭")
        print(f"\n⏱️  预计耗时: {len(self.utilities) * 3 * 2.5 / 60:.1f} 分钟")
        print("\n按 Enter 开始，或 Ctrl+C 取消...")
        
        try:
            input()
        except KeyboardInterrupt:
            print("\n❌ 已取消")
            return
        
        print("\n⚙️  初始化游戏环境...")
        print("   请确认：")
        print("   - 已进入地图")
        print("   - 已选择队伍（CT或T）")
        print("\n   脚本将自动执行所有必需命令...")
        print("   3秒后开始...")
        time.sleep(3)
        
        # 打开控制台
        keyboard.press_and_release('`')
        time.sleep(0.3)
        
        # 批量发送初始化命令
        print("   1/4 启用作弊模式...")
        self.send_command_batch("sv_cheats 1")
             
        print("   2/4 隐藏玩家模型...")
        self.send_command_batch("ent_fire !self alpha 0")  # 设置透明度为0
        
        print("   3/4 隐藏游戏UI和阴影...")
        self.send_command_batch("cl_draw_only_deathnotices 1")  # 隐藏UI
        self.send_command_batch("r_drawviewmodel 0")  # 隐藏手臂和武器
        self.send_command_batch("crosshair 0")  # 隐藏准星
        self.send_command_batch("r_shadows 0")  # 禁用阴影
        
        print(f"   4/4 绑定 {self.screenshot_key} 为截图键...")
        self.send_command_batch(f"bind {self.screenshot_key} screenshot")
        
        # 关闭控制台
        time.sleep(0.3)
        keyboard.press_and_release('esc')
        time.sleep(self.console_delay)
        
        print("\n✅ 初始化完成！")
        print("\n🚀 开始自动截图...")
        print("⚠️  按 - 键可强制停止 | 按 Ctrl+C 可暂停\n")
        
        try:
            for i, utility in enumerate(self.utilities[start_from - 1:], start=start_from):
                if self.should_stop:
                    print(f"\n\n⏹️  已在第 {i} 个道具处停止")
                    print(f"💡 要继续，运行：python screenshot.py --start {i}")
                    keyboard.unhook_all()
                    return
                
                self.current_index = i
                self.process_utility(utility, i)
                
                if i % 10 == 0:
                    print(f"\n✅ 已完成 {i}/{len(self.utilities)} ({i*100//len(self.utilities)}%)")
                    time.sleep(1)
                    
        except KeyboardInterrupt:
            print(f"\n\n⏸️  已暂停在第 {self.current_index} 个道具")
            print(f"💡 要继续，运行：python screenshot.py --start {self.current_index + 1}")
            keyboard.unhook_all()
            return
        
        keyboard.unhook_all()
        
        # 🆕 自动同步到数据库
        print("\n💾 同步截图状态到数据库...")
        try:
            import sqlite3
            # 获取数据库路径
            script_dir = Path(__file__).parent.resolve()
            project_root = script_dir.parent
            db_path = project_root / 'backend' / 'data' / 'yuuko.db'
            
            if not db_path.exists():
                raise FileNotFoundError(f"数据库不存在: {db_path}")
            
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            updated = 0
            for util in self.utilities:
                if util.get('screenshot_filename_base'):
                    cursor.execute("""
                        UPDATE utilities 
                        SET status = 'screenshotted',
                            screenshot_filename_base = ?
                        WHERE hash = ?
                    """, (util['screenshot_filename_base'], util['hash']))
                    
                    if cursor.rowcount > 0:
                        updated += 1
            
            conn.commit()
            conn.close()
            
            print(f"   ✅ 已更新 {updated} 个道具状态: selected → screenshotted")
        except Exception as e:
            print(f"   ⚠️  同步失败: {e}")
            import traceback
            traceback.print_exc()
            print("   💡 请手动运行: python sync_screenshots.py")
        
        # 保存更新后的道具数据（包含screenshot_id）
        print("\n💾 保存道具数据到JSON...")
        with open(self.utilities_file, 'w', encoding='utf-8') as f:
            json.dump(self.utilities, f, ensure_ascii=False, indent=2)
        print("   ✅ 已保存")
        
        # 🆕 清空截图列表
        print("\n🗑️  清空截图列表...")
        try:
            with open(self.utilities_file, 'w', encoding='utf-8') as f:
                json.dump([], f, ensure_ascii=False, indent=2)
            print("   ✅ 已清空 selected_for_screenshot.json")
        except Exception as e:
            print(f"   ⚠️  清空失败: {e}")
        
        print("\n" + "="*50)
        print("🎉 截图完成！")
        print("="*50)
        print(f"\n📁 截图已保存到: {os.path.abspath(self.output_dir)}")
        print(f"📊 共生成 {len(self.utilities) * 3} 张截图")
        print(f"💾 截图命名格式: {self.utilities[0].get('map', 'map')}_{{hash}}_{{type}}.jpg")
        print(f"   例如: de_dust2_6508bb184bfb3e82_position.jpg")
        
        print("\n💡 下一步:")
        print("   1. 打开管理后台: http://localhost:5000")
        print("   2. 点击'审核'标签页查看道具")
        print("   3. 审核通过后导出到用户端")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='CS2道具自动截图工具')
    parser.add_argument('--type', type=str, choices=['smoke', 'flashbang', 'hegrenade', 'incendiary'],
                        help='道具类型')
    parser.add_argument('--start', type=int, default=1,
                        help='从第几个道具开始')
    parser.add_argument('--file', type=str, default='../output/commands/selected_for_screenshot.json',
                        help='道具数据文件路径')
    parser.add_argument('--output', type=str, default='../output/screenshots',
                        help='截图输出目录')
    parser.add_argument('--delay', type=float, default=1.5,
                        help='控制台关闭后等待时间（秒），默认1.5秒')
    parser.add_argument('--key', type=str, default='F12',
                        help='截图绑定键，默认F12')
    parser.add_argument('--eye-height', type=float, default=64.0,
                        help='眼睛高度偏移（单位），默认64.0（CS2标准站立高度）')
    
    args = parser.parse_args()
    
    if not Path(args.file).exists():
        print(f"❌ 错误: 找不到文件 {args.file}")
        return
    
    tool = CS2AutoScreenshot(
        args.file, 
        args.type, 
        args.output, 
        args.delay, 
        args.key, 
        args.eye_height
    )
    tool.run(start_from=args.start)

if __name__ == '__main__':
    main()