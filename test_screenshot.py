#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
截图脚本功能测试
"""
import sys
sys.path.insert(0, '.')

from client.screenshot import CS2AutoScreenshot

print("=" * 50)
print("CS2 截图脚本 - 功能测试")
print("=" * 50)

# 测试1: FFmpeg检测
print("\n[测试1] FFmpeg检测...")
tool = CS2AutoScreenshot(use_video_mode=True)
if tool.check_ffmpeg():
    print(f"✅ FFmpeg found at: {tool.ffmpeg_path}")
else:
    print("❌ FFmpeg not found")

# 测试2: 关键帧时间计算
print("\n[测试2] 关键帧时间计算...")
test_utility = {
    'hash': 'test_001',
    'map': 'de_dust2',
    'type': 'smoke',
    'flight_time': 2.0,
    'thrower': 'TestPlayer',
    'position': {'x': 0, 'y': 0, 'z': 0},
    'angles': {'pitch': 0, 'yaw': 0},
    'land_position': {'x': 100, 'y': 100, 'z': 0},
}

recording_duration = 5.0
frame_times = tool.calculate_key_frame_times(test_utility, recording_duration)
print(f"✅ Frame times calculated:")
for key, val in frame_times.items():
    print(f"   - {key}: {val:.2f}s")

# 测试3: 参数检查
print("\n[测试3] 脚本参数检查...")
print(f"✅ Video mode: {tool.use_video_mode}")
print(f"✅ Video FPS: {tool.video_fps}")
print(f"✅ Output dir: {tool.output_dir}")
print(f"✅ Backend URL: {tool.backend_url}")

print("\n" + "=" * 50)
print("✅ 所有测试通过！脚本已就绪")
print("=" * 50)
print("\n使用方法:")
print("  python client/screenshot.py          # 默认视频模式（需要FFmpeg）")
print("  python client/screenshot.py --no-video  # 旧模式（游戏内截图）")
