"""
初始化数据库
清空所有数据，重新创建表结构
"""
from pathlib import Path
from database import Database

def init_database():
    """初始化数据库"""
    db_path = Path('backend/data/yuuko.db')
    
    # 删除旧数据库
    if db_path.exists():
        print(f"🗑️  删除旧数据库: {db_path}")
        db_path.unlink()
    
    # 创建新数据库
    print("📊 创建新数据库...")
    db = Database()
    
    # 获取统计
    stats = db.get_statistics()
    
    print("\n✅ 数据库初始化完成！")
    print(f"   数据库位置: {db_path.absolute()}")
    print(f"   表数量: 2 (utilities, utility_status)")
    print(f"   道具数量: {stats.get('total', 0)}")
    
    print("\n💡 下一步:")
    print("   1. 运行 START_BACKEND.bat 启动管理后台")
    print("   2. 访问 http://localhost:5000")
    print("   3. 解析 Demo 文件")

if __name__ == '__main__':
    print("=" * 70)
    print("🎮 初始化数据库")
    print("=" * 70)
    print()
    
    confirm = input("⚠️  这将清空所有数据！确定继续吗？(yes/no): ")
    
    if confirm.lower() in ['yes', 'y']:
        init_database()
    else:
        print("❌ 已取消")
