# Yuuko CS2 道具库 - 项目文件说明

## 📁 项目结构总览

```
Yuuko-cs/
├── backend/              # 后端服务（Flask + SQLite）
├── client/               # 客户端工具脚本
├── demos/                # CS2 Demo 文件存放目录
├── output/               # 输出文件目录
├── public/               # 用户端道具库（前端）
├── .gitignore            # Git 忽略文件配置
└── *.bat                 # 启动脚本
```

---

## 🚀 启动脚本（根目录）

### START_ALL.bat
**作用：** 启动后端服务器（Flask）  
**使用场景：** 启动管理后台和 API 服务  
**端口：** 5000  
**访问：** http://localhost:5000

### START_SCREENSHOT.bat
**作用：** 启动截图脚本  
**使用场景：** 在游戏中自动截图道具  
**前提：** 已在管理后台选择道具

### TEST_LOCAL.bat
**作用：** 启动本地道具库预览  
**使用场景：** 测试导出后的道具库效果  
**端口：** 8000  
**访问：** http://localhost:8000

### CLEAR_DATABASE.bat
**作用：** 清空整个数据库  
**使用场景：** 完全重置项目，从零开始  
**警告：** ⚠️ 会删除所有道具数据！

### CLEAR_EXPORTED_ONLY.bat
**作用：** 只清空已导出的数据  
**使用场景：** 重新导出道具，保留待审核数据  
**不会删除：** 待审核、已批准的道具

---

## 🔧 后端服务 (backend/)

### backend/app.py
**作用：** Flask 主应用程序  
**功能：**
- 提供管理后台 Web 界面
- 提供 RESTful API 接口
- 路由注册和错误处理

### backend/database.py
**作用：** 数据库操作层  
**功能：**
- SQLite 数据库连接管理
- 道具 CRUD 操作
- 状态管理（parsed, selected, screenshotted, approved, exported）
- 统计查询

### backend/init_db.py
**作用：** 数据库初始化脚本  
**功能：**
- 创建数据库表结构
- 插入初始数据

### backend/routes/
API 路由模块：

#### demo.py
- `/api/demos` - 获取 Demo 列表
- `/api/parse_demo` - 解析 Demo 文件

#### utility.py
- `/api/utilities` - 获取道具列表
- `/api/utilities/select` - 选择道具（自动导出JSON）
- `/api/utilities/<hash>/approve` - 批准道具
- `/api/utilities/<hash>/reject` - 拒绝道具
- `/api/utilities/<hash>` - 删除道具

#### screenshot.py
- `/api/screenshot/selected` - 获取已选择道具
- `/api/screenshot/export_for_script` - 导出JSON供截图脚本使用

#### export_route.py
- `/api/export` - 导出道具到用户端
- `/api/export/approved` - 获取待导出道具
- `/api/export/exported` - 获取已导出道具

---

## 🖥️ 客户端工具 (client/)

### client/screenshot.py
**作用：** 自动截图脚本（主要工具）  
**功能：**
- 读取选中的道具数据
- 自动控制游戏视角和传送
- 截取3张图片：站位图、准星图、落点图
- 自动同步状态到数据库
**使用：** `python client/screenshot.py`

### client/admin/
**管理后台前端文件：**
- `index.html` - 管理后台界面
- `script.js` - 前端逻辑
- `style.css` - 样式表

### client/src/
**Demo 解析工具：**
- `parser.py` - Demo 文件解析器
- `extractor.py` - 道具数据提取器
- `manager.py` - 数据管理器
- `database.py` - 本地数据库操作

### client/其他工具脚本
- `export.py` - 导出工具（已废弃，使用后端API）
- `sync_pending.py` - 同步脚本（已集成到截图脚本）
- `create_screenshot_index.py` - 截图索引生成（已废弃）
- `reset_all_data.py` - 重置数据（已废弃，使用 CLEAR_DATABASE.bat）
- `admin_server.py` - 本地服务器（已废弃，使用 backend/app.py）

---

## 🌐 用户端道具库 (public/)

### public/index.html
**作用：** 道具库主页  
**功能：** 展示所有导出的道具

### public/js/main.js
**作用：** 道具库前端逻辑  
**功能：**
- 道具列表展示
- 图片查看器（带准星功能）
- 准星可视化和调整
- 筛选和搜索

### public/css/style.css
**作用：** 道具库样式表

### public/crosshair-test.html
**作用：** 准星位置测试工具  
**功能：**
- 上传截图
- 显示像素坐标
- 标记准星位置
- 计算偏移量

### public/crosshair-checker.html
**作用：** 准星检查工具（旧版）  
**状态：** 可删除（使用 crosshair-test.html）

### public/data/
**作用：** 导出的道具数据（JSON）  
**文件：**
- `utilities.json` - 总索引
- `de_dust2.json` - 各地图的道具数据
- `de_mirage.json`

### public/images/
**作用：** 导出的道具截图  
**结构：** `images/{map}/{type}/{utility_id}_{shot_type}.jpg`

---

## 📂 输出目录 (output/)

### output/screenshots/
**作用：** 截图脚本生成的原始截图  
**文件命名：** `{map}_unknown_{util_id}_{position|crosshair|landing}.jpg`

### output/commands/
**作用：** 截图脚本的数据文件  
**文件：**
- `selected_for_screenshot.json` - 待截图道具列表

### output/data/
**作用：** 旧版数据文件（已废弃）  
**状态：** 可删除

---

## 📦 Demo 文件 (demos/)

**作用：** 存放 CS2 比赛录像文件  
**格式：** `.dem` 文件  
**用途：** 使用后端 Demo 管理解析道具数据

---

## 🔄 完整工作流程

### 1. 解析 Demo
```
1. 将 .dem 文件放入 demos/ 目录
2. 打开管理后台 http://localhost:5000
3. 点击"Demo管理"标签页
4. 点击"解析"按钮
5. 道具进入数据库，状态: parsed
```

### 2. 选择道具
```
1. 点击"选择道具"标签页
2. 筛选和选择要截图的道具
3. 点击"保存选择"
4. 自动导出JSON，状态: selected
```

### 3. 截图
```
1. 启动CS2，进入对应地图
2. 运行 START_SCREENSHOT.bat
3. 自动截图3张（站位、准星、落点）
4. 自动同步数据库，状态: screenshotted
```

### 4. 审核
```
1. 刷新管理后台
2. 点击"审核"标签页
3. 查看截图，填写名称
4. 批准或拒绝，状态: approved / rejected
```

### 5. 导出
```
1. 点击"导出"标签页
2. 点击"导出道具"按钮
3. 生成用户端文件，状态: exported
```

### 6. 测试
```
1. 运行 TEST_LOCAL.bat
2. 访问 http://localhost:8000
3. 测试道具库功能
```

### 7. 发布
```
git add .
git commit -m "添加xx个新道具"
git push
```

---

## 🗑️ 可以删除的文件

以下文件已废弃或被替代：

### 根目录
- `CLEAR_EVERYTHING.bat` - 已被 CLEAR_DATABASE.bat 替代
- `test_screenshot.py` - 测试脚本，已完成测试

### client/
- `admin_server.py` - 已被 backend/app.py 替代
- `export.py` - 已被后端API替代
- `sync_pending.py` - 已集成到截图脚本
- `create_screenshot_index.py` - 已废弃
- `reset_all_data.py` - 已被 CLEAR_DATABASE.bat 替代

### public/
- `crosshair-checker.html` - 已被 crosshair-test.html 替代

### output/data/
- 整个目录可删除（旧版JSON文件）

---

## 📝 重要说明

### 数据库位置
**唯一数据库：** `backend/data/yuuko.db`  
**不应存在：** `backend/backend/data/yuuko.db`（错误路径）

### 端口使用
- `5000` - 后端管理系统
- `8000` - 本地道具库预览

### 数据流向
```
Demo文件 → 解析 → 数据库(parsed)
       ↓
    选择道具 → 数据库(selected) + JSON导出
       ↓
    截图 → output/screenshots/ + 数据库(screenshotted)
       ↓
    审核 → 数据库(approved/rejected)
       ↓
    导出 → public/data/ + public/images/ + 数据库(exported)
```

---

## 🆘 常见问题

### Q: 截图脚本显示道具数量不对？
A: 确保在管理后台点击"保存选择"后再截图

### Q: 管理后台看不到待审核道具？
A: 截图脚本现在会自动同步，无需手动操作

### Q: 数据库和页面显示不一致？
A: 检查是否有多个数据库文件，删除 backend/backend/ 目录

### Q: 准星位置不正确？
A: 截图时确保关闭 noclip（脚本自动处理）

---

**最后更新：** 2026-08-07  
**版本：** 2.0 (SQLite重构版)
