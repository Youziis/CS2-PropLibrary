"""
数据库操作层
使用 SQLite 作为单一数据源
"""
import sqlite3
import json
from pathlib import Path
from datetime import datetime
from contextlib import contextmanager
from typing import List, Dict, Optional


class Database:
    # 地图ID映射（用于生成sort_id）
    MAP_ID_PREFIX = {
        'de_dust2': 1,
        'de_mirage': 2,
        'de_inferno': 3,
        'de_nuke': 4,
        'de_ancient': 5,
        'de_anubis': 6,
        'de_vertigo': 7,
        'de_cache': 8,
        'de_overpass': 9,
        'de_train': 10,
    }
    
    def __init__(self, db_path=None):
        if db_path is None:
            # 使用绝对路径，基于项目根目录
            project_root = Path(__file__).parent.parent
            db_path = project_root / 'backend' / 'data' / 'yuuko.db'
        
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
    
    @contextmanager
    def get_connection(self):
        """上下文管理器，自动处理事务"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # 返回字典形式
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def _init_db(self):
        """初始化数据库表"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # 创建状态枚举表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS utility_status (
                    name TEXT PRIMARY KEY,
                    description TEXT NOT NULL
                )
            """)
            
            # 插入状态值
            statuses = [
                ('parsed', '已解析，待选择截图'),
                ('selected', '已选择，待截图'),
                ('screenshotted', '已截图，待审核'),
                ('approved', '已批准，待导出'),
                ('exported', '已导出到用户端'),
                ('rejected', '已拒绝')
            ]
            cursor.executemany(
                "INSERT OR IGNORE INTO utility_status VALUES (?, ?)",
                statuses
            )
            
            # 创建道具表
            # 字段说明：
            # - id: 自增主键
            # - sort_id: 排序ID，格式：地图编号+递增序号（如：10001, 20001），用于前端展示排序
            # - hash: 唯一标识，基于投掷位置、角度、落点的MD5值（16位）
            # - map: 地图名称（de_dust2, de_mirage等）
            # - type: 道具类型（smoke/flashbang/hegrenade/incendiary）
            # - team: 使用阵营（T/CT/Unknown）
            # - thrower: 投掷者游戏名称
            # - throw_position: 投掷位置JSON {"x": 0.0, "y": 0.0, "z": 0.0}
            # - throw_angles: 投掷角度JSON {"pitch": 0.0, "yaw": 0.0}
            # - land_position: 落点位置JSON {"x": 0.0, "y": 0.0, "z": 0.0}
            # - throw_type: 投掷方式（跳投、站投、蹲投、走投等）
            # - flight_time: 飞行时间（秒）
            # - distance: 投掷距离
            # - source_demo: 来源Demo文件名或"手动添加"
            # - parse_time: 解析/添加时间
            # - status: 状态（parsed/selected/screenshotted/approved/exported/rejected）
            # - screenshot_filename_base: 截图文件名前缀（格式：map_hash）
            # - display_name: 显示名称（用户可编辑）
            # - notes: 备注说明
            # - tags: 标签（JSON数组，如：["简单", "常用", "拱门"]）
            # - approved_time: 批准时间
            # - exported_time: 导出时间
            # - raw_data: 原始完整数据JSON
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS utilities (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sort_id INTEGER,
                    hash TEXT UNIQUE NOT NULL,
                    
                    -- 基础信息
                    map TEXT NOT NULL,
                    type TEXT NOT NULL,
                    team TEXT NOT NULL,
                    thrower TEXT,
                    
                    -- 位置和角度（JSON存储）
                    throw_position TEXT NOT NULL,
                    throw_angles TEXT NOT NULL,
                    land_position TEXT NOT NULL,
                    
                    -- 投掷信息
                    throw_type TEXT,
                    flight_time REAL,
                    distance REAL,
                    
                    -- 来源信息
                    source_demo TEXT NOT NULL,
                    parse_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                    
                    -- 状态管理
                    status TEXT NOT NULL DEFAULT 'parsed',
                    screenshot_filename_base TEXT,
                    
                    -- 审核信息
                    display_name TEXT,
                    notes TEXT,
                    tags TEXT,
                    approved_time DATETIME,
                    exported_time DATETIME,
                    
                    -- 完整数据（JSON存储，保留所有字段）
                    raw_data TEXT,
                    
                    FOREIGN KEY (status) REFERENCES utility_status(name)
                )
            """)
            
            # 创建道具关联表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS utility_relations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    utility_hash TEXT NOT NULL,
                    related_hash TEXT NOT NULL,
                    combo_group TEXT,
                    combo_order INTEGER,
                    created_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (utility_hash) REFERENCES utilities(hash) ON DELETE CASCADE,
                    FOREIGN KEY (related_hash) REFERENCES utilities(hash) ON DELETE CASCADE,
                    UNIQUE(utility_hash, related_hash)
                )
            """)
            
            # 创建索引
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_utility_relations_utility 
                ON utility_relations(utility_hash)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_utility_relations_related 
                ON utility_relations(related_hash)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_utility_relations_combo 
                ON utility_relations(combo_group)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_status 
                ON utilities(status)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_map 
                ON utilities(map)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_map_status 
                ON utilities(map, status)
            """)
            
            # 数据库迁移：为已存在的表添加 tags 列（如果不存在）
            try:
                cursor.execute("SELECT tags FROM utilities LIMIT 1")
            except sqlite3.OperationalError:
                # tags 列不存在，添加它
                print("[数据库迁移] 添加 tags 列...")
                cursor.execute("ALTER TABLE utilities ADD COLUMN tags TEXT")
                print("[数据库迁移] tags 列添加成功")
            
            # 数据库迁移：为已存在的表添加 sort_id 列（如果不存在）
            try:
                cursor.execute("SELECT sort_id FROM utilities LIMIT 1")
            except sqlite3.OperationalError:
                # sort_id 列不存在，添加它
                print("[数据库迁移] 添加 sort_id 列...")
                cursor.execute("ALTER TABLE utilities ADD COLUMN sort_id INTEGER")
                print("[数据库迁移] sort_id 列添加成功")
                # 为现有数据生成 sort_id
                self._generate_sort_ids_for_existing_data(conn)
    
    def _generate_sort_ids_for_existing_data(self, conn):
        """为现有已导出的道具生成sort_id"""
        print("[数据库迁移] 为已导出道具生成 sort_id...")
        cursor = conn.cursor()
        
        # 只为已导出的道具（status='exported'）分配sort_id
        for map_name, map_prefix in self.MAP_ID_PREFIX.items():
            cursor.execute("""
                SELECT id FROM utilities 
                WHERE map = ? AND status = 'exported' AND (sort_id IS NULL OR sort_id = 0)
                ORDER BY parse_time ASC
            """, (map_name,))
            
            rows = cursor.fetchall()
            for index, row in enumerate(rows, start=1):
                sort_id = map_prefix * 10000 + index
                cursor.execute("""
                    UPDATE utilities SET sort_id = ? WHERE id = ?
                """, (sort_id, row['id']))
        
        print(f"[数据库迁移] sort_id 生成完成")
    
    def _get_next_sort_id(self, map_name: str) -> int:
        """获取指定地图的下一个sort_id"""
        map_prefix = self.MAP_ID_PREFIX.get(map_name, 99)  # 未知地图使用99
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # 获取该地图当前最大的sort_id（只统计已有sort_id的道具）
            cursor.execute("""
                SELECT MAX(sort_id) as max_id 
                FROM utilities 
                WHERE map = ? AND sort_id IS NOT NULL
            """, (map_name,))
            
            result = cursor.fetchone()
            max_id = result['max_id'] if result and result['max_id'] else None
            
            # 如果没有任何sort_id，从起始值开始
            start_id = map_prefix * 10000
            if max_id is None or max_id < start_id:
                return start_id + 1
            
            return max_id + 1
    
    def add_utilities(self, utilities: List[Dict]) -> tuple:
        """
        添加解析的道具（批量插入）
        返回：(新增数量, 重复数量)
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            added = 0
            duplicated = 0
            
            for util in utilities:
                try:
                    cursor.execute("""
                        INSERT INTO utilities (
                            hash, map, type, team, thrower,
                            throw_position, throw_angles, land_position,
                            throw_type, flight_time, distance,
                            source_demo, parse_time, status, raw_data
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'parsed', ?)
                    """, (
                        util['hash'],
                        util['map'],
                        util['type'],
                        util.get('team', 'Unknown'),
                        util.get('thrower'),
                        json.dumps(util.get('throw_position', {})),
                        json.dumps(util.get('throw_angles', {})),
                        json.dumps(util.get('land_position', {})),
                        util.get('throw_type'),
                        util.get('flight_time'),
                        util.get('distance'),
                        util.get('source_demo'),
                        util.get('parse_time', datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
                        json.dumps(util)  # 保存完整数据
                    ))
                    added += 1
                except sqlite3.IntegrityError:
                    duplicated += 1
            
            return added, duplicated
    
    def insert_utility(self, utility_data: Dict) -> bool:
        """
        插入单个道具（用于手动添加）
        utility_data: 包含道具信息的字典
        返回：是否成功
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            try:
                # 准备基础字段（使用默认值填充缺失字段）
                # 不在这里生成sort_id，只在导出时生成
                cursor.execute("""
                    INSERT INTO utilities (
                        hash, map, type, team, 
                        throw_position, throw_angles, land_position,
                        throw_type, source_demo, parse_time, 
                        status, screenshot_filename_base,
                        display_name, notes, tags, approved_time, raw_data
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    utility_data['hash'],
                    utility_data['map'],
                    utility_data['type'],
                    utility_data.get('team', 'Unknown'),
                    json.dumps(utility_data.get('throw_position', {})),
                    json.dumps(utility_data.get('throw_angles', {})),
                    json.dumps(utility_data.get('land_position', {})),
                    utility_data.get('throw_type', '未知'),
                    utility_data.get('demo_source', '手动添加'),
                    utility_data.get('created_time', datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
                    utility_data.get('status', 'approved'),
                    utility_data.get('screenshot_filename_base'),
                    utility_data.get('display_name'),
                    utility_data.get('notes'),
                    json.dumps(utility_data.get('tags', [])),
                    utility_data.get('approved_time'),
                    json.dumps(utility_data)  # 保存完整数据
                ))
                return True
            except sqlite3.IntegrityError as e:
                print(f"插入道具失败（重复hash）: {e}")
                return False
            except Exception as e:
                print(f"插入道具失败: {e}")
                return False
    
    def get_utilities(self, status: Optional[str] = None, 
                     map_name: Optional[str] = None,
                     limit: Optional[int] = None,
                     offset: int = 0) -> List[Dict]:
        """
        获取道具列表（支持筛选）
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            query = "SELECT * FROM utilities WHERE 1=1"
            params = []
            
            if status:
                query += " AND status = ?"
                params.append(status)
            if map_name:
                query += " AND map = ?"
                params.append(map_name)
            
            query += " ORDER BY parse_time DESC"
            
            if limit:
                query += f" LIMIT {limit} OFFSET {offset}"
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            return [self._row_to_dict(row) for row in rows]
    
    def get_utility_by_hash(self, hash_val: str) -> Optional[Dict]:
        """根据hash获取单个道具"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM utilities WHERE hash = ?", (hash_val,))
            row = cursor.fetchone()
            return self._row_to_dict(row) if row else None
    
    def update_status(self, hash_val: str, new_status: str, **extra_fields) -> bool:
        """
        更新道具状态
        extra_fields: 额外要更新的字段
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            updates = ["status = ?"]
            params = [new_status]
            
            for key, value in extra_fields.items():
                updates.append(f"{key} = ?")
                params.append(value)
            
            params.append(hash_val)
            
            cursor.execute(f"""
                UPDATE utilities 
                SET {', '.join(updates)}
                WHERE hash = ?
            """, params)
            
            return cursor.rowcount > 0
    
    def update_utility(self, hash_val: str, fields: Dict) -> bool:
        """更新道具的多个字段"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            updates = []
            params = []
            
            for key, value in fields.items():
                updates.append(f"{key} = ?")
                params.append(value)
            
            params.append(hash_val)
            
            cursor.execute(f"""
                UPDATE utilities 
                SET {', '.join(updates)}
                WHERE hash = ?
            """, params)
            
            return cursor.rowcount > 0
    
    def delete_utility(self, hash_val: str) -> bool:
        """删除道具"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM utilities WHERE hash = ?", (hash_val,))
            return cursor.rowcount > 0
    
    def get_statistics(self) -> Dict:
        """获取统计信息"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            stats = {}
            
            # 按状态统计
            cursor.execute("""
                SELECT status, COUNT(*) as count 
                FROM utilities 
                GROUP BY status
            """)
            for row in cursor.fetchall():
                stats[row['status']] = row['count']
            
            # 按地图统计
            cursor.execute("""
                SELECT map, COUNT(*) as count 
                FROM utilities 
                GROUP BY map
            """)
            stats['by_map'] = {row['map']: row['count'] for row in cursor.fetchall()}
            
            # 按类型统计
            cursor.execute("""
                SELECT type, COUNT(*) as count 
                FROM utilities 
                GROUP BY type
            """)
            stats['by_type'] = {row['type']: row['count'] for row in cursor.fetchall()}
            
            # 总数
            cursor.execute("SELECT COUNT(*) as total FROM utilities")
            stats['total'] = cursor.fetchone()['total']
            
            return stats
    
    def _row_to_dict(self, row) -> Dict:
        """SQLite Row 转字典，解析JSON字段"""
        if not row:
            return None
        
        d = dict(row)
        
        # 如果有raw_data，直接使用它（包含所有字段）
        if d.get('raw_data'):
            full_data = json.loads(d['raw_data'])
            # 覆盖数据库中可能被审核修改的字段
            full_data['sort_id'] = d.get('sort_id')  # ✅ 添加sort_id
            full_data['status'] = d['status']
            full_data['screenshot_filename_base'] = d.get('screenshot_filename_base')
            full_data['display_name'] = d.get('display_name')
            full_data['notes'] = d.get('notes')
            # ✅ 新增：覆盖审核时可能修改的字段
            if d.get('type'):
                full_data['type'] = d['type']
            if d.get('team'):
                full_data['team'] = d['team']
            if d.get('throw_type'):
                full_data['throw_type'] = d['throw_type']
            # ✅ 新增：覆盖tags字段
            if d.get('tags'):
                try:
                    full_data['tags'] = json.loads(d['tags'])
                except:
                    full_data['tags'] = []
            else:
                full_data['tags'] = []
            return full_data
        
        # 解析JSON字段
        for field in ['throw_position', 'throw_angles', 'land_position']:
            if d.get(field):
                try:
                    d[field] = json.loads(d[field])
                except:
                    pass
        
        # 解析tags字段
        if d.get('tags'):
            try:
                d['tags'] = json.loads(d['tags'])
            except:
                d['tags'] = []
        else:
            d['tags'] = []
        
        return d
    
    # ==================== 道具关联管理 ====================
    
    def add_utility_relation(self, utility_hash: str, related_hash: str, 
                            bidirectional: bool = True, 
                            combo_group: str = None, 
                            combo_order: int = None) -> bool:
        """
        添加道具关联关系
        
        Args:
            utility_hash: 源道具hash
            related_hash: 关联道具hash
            bidirectional: 是否双向关联（默认True）
            combo_group: 组合分组ID（可选）
            combo_order: 组内顺序（可选）
        
        Returns:
            bool: 是否成功
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            try:
                # 添加 A -> B 关联
                cursor.execute("""
                    INSERT OR IGNORE INTO utility_relations 
                    (utility_hash, related_hash, combo_group, combo_order)
                    VALUES (?, ?, ?, ?)
                """, (utility_hash, related_hash, combo_group, combo_order))
                
                # 如果双向关联，添加 B -> A
                if bidirectional:
                    cursor.execute("""
                        INSERT OR IGNORE INTO utility_relations 
                        (utility_hash, related_hash, combo_group, combo_order)
                        VALUES (?, ?, ?, ?)
                    """, (related_hash, utility_hash, combo_group, combo_order))
                
                return True
            except Exception as e:
                print(f"添加关联失败: {e}")
                return False
    
    def remove_utility_relation(self, utility_hash: str, related_hash: str, 
                               bidirectional: bool = True) -> bool:
        """
        移除道具关联关系
        
        Args:
            utility_hash: 源道具hash
            related_hash: 关联道具hash
            bidirectional: 是否双向移除（默认True）
        
        Returns:
            bool: 是否成功
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            try:
                # 移除 A -> B 关联
                cursor.execute("""
                    DELETE FROM utility_relations 
                    WHERE utility_hash = ? AND related_hash = ?
                """, (utility_hash, related_hash))
                
                # 如果双向移除，移除 B -> A
                if bidirectional:
                    cursor.execute("""
                        DELETE FROM utility_relations 
                        WHERE utility_hash = ? AND related_hash = ?
                    """, (related_hash, utility_hash))
                
                return True
            except Exception as e:
                print(f"移除关联失败: {e}")
                return False
    
    def get_related_utilities(self, utility_hash: str) -> List[Dict]:
        """
        获取某个道具的所有关联道具
        
        Args:
            utility_hash: 道具hash
        
        Returns:
            List[Dict]: 关联道具列表（完整信息）
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # JOIN查询获取关联道具的完整信息
            cursor.execute("""
                SELECT u.*, r.combo_group, r.combo_order
                FROM utilities u
                INNER JOIN utility_relations r ON u.hash = r.related_hash
                WHERE r.utility_hash = ?
                ORDER BY r.combo_order, u.display_name
            """, (utility_hash,))
            
            results = []
            for row in cursor.fetchall():
                d = dict(row)
                results.append(self._parse_utility_row(d))
            
            return results
    
    def batch_link_utilities(self, utility_hashes: List[str], 
                            combo_group: str = None) -> int:
        """
        批量关联多个道具（互相关联）
        
        Args:
            utility_hashes: 道具hash列表
            combo_group: 组合分组ID（可选）
        
        Returns:
            int: 创建的关联数量
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            pairs = []
            count = 0
            
            # 生成所有组合对（不包括自己关联自己）
            for i, hash_a in enumerate(utility_hashes):
                for j, hash_b in enumerate(utility_hashes):
                    if i != j:
                        order = i + 1 if combo_group else None
                        pairs.append((hash_a, hash_b, combo_group, order))
            
            # 批量插入
            try:
                cursor.executemany("""
                    INSERT OR IGNORE INTO utility_relations 
                    (utility_hash, related_hash, combo_group, combo_order)
                    VALUES (?, ?, ?, ?)
                """, pairs)
                count = cursor.rowcount
                
                return count
            except Exception as e:
                print(f"批量关联失败: {e}")
                return 0
    
    def get_relation_count(self, utility_hash: str) -> int:
        """
        获取某个道具的关联数量
        
        Args:
            utility_hash: 道具hash
        
        Returns:
            int: 关联数量
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM utility_relations
                WHERE utility_hash = ?
            """, (utility_hash,))
            
            row = cursor.fetchone()
            return row['count'] if row else 0
    
    def get_combo_utilities(self, combo_group: str) -> List[Dict]:
        """
        获取某个组合的所有道具
        
        Args:
            combo_group: 组合分组ID
        
        Returns:
            List[Dict]: 组合内的道具列表（按顺序）
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT DISTINCT u.*, r.combo_order
                FROM utilities u
                INNER JOIN utility_relations r ON u.hash = r.utility_hash
                WHERE r.combo_group = ?
                ORDER BY r.combo_order, u.display_name
            """, (combo_group,))
            
            results = []
            for row in cursor.fetchall():
                d = dict(row)
                results.append(self._parse_utility_row(d))
            
            return results
    
    def clear_all_relations(self, utility_hash: str) -> bool:
        """
        清空某个道具的所有关联（包括双向）
        
        Args:
            utility_hash: 道具hash
        
        Returns:
            bool: 是否成功
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            try:
                # 删除该道具作为源的所有关联
                cursor.execute("""
                    DELETE FROM utility_relations 
                    WHERE utility_hash = ?
                """, (utility_hash,))
                
                # 删除该道具作为目标的所有关联
                cursor.execute("""
                    DELETE FROM utility_relations 
                    WHERE related_hash = ?
                """, (utility_hash,))
                
                return True
            except Exception as e:
                print(f"清空关联失败: {e}")
                return False


# 测试代码
if __name__ == '__main__':
    db = Database()
    stats = db.get_statistics()
    print("数据库统计:")
    print(json.dumps(stats, indent=2, ensure_ascii=False))
