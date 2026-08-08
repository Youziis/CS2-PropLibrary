# 调试拒绝功能

## 当前问题
- ✅ 截图文件被正确删除
- ❌ 道具状态没有改为 `rejected`
- ❌ `screenshot_filename_base` 没有被清空

## 已修改的代码

### 修改点1：合并数据库更新操作
之前是分两次更新：
1. 先清空 `screenshot_filename_base`
2. 再更新 `status`

现在合并为一次操作：
```python
db.update_status(
    hash_val, 
    'rejected',
    screenshot_filename_base=None
)
```

### 修改点2：添加详细日志
在后端终端会显示完整的操作流程：
- 收到的hash值
- 道具当前状态
- 截图文件删除过程
- 数据库更新结果
- 更新后的验证信息

---

## 🚨 重要：现在需要做的

### 1️⃣ 重启后端服务器
```bash
# 在后端终端按 Ctrl+C 停止
# 然后重新启动：
cd c:\Users\bb162\Desktop\Yuuko-cs\backend
python app.py
```

### 2️⃣ 测试拒绝功能
1. 刷新浏览器（Ctrl+Shift+R）
2. 进入"审核道具"页面
3. 点击【拒绝】按钮

### 3️⃣ 观察后端终端输出
你会看到类似这样的日志：

```
[拒绝道具] 开始处理: abc123def456
[拒绝道具] 找到道具，当前状态: screenshotted
[拒绝道具] 截图文件前缀: de_mirage_abc123def456
[拒绝道具] 已删除: de_mirage_abc123def456_position.jpg
[拒绝道具] 已删除: de_mirage_abc123def456_crosshair.jpg
[拒绝道具] 已删除: de_mirage_abc123def456_landing.jpg
[拒绝道具] 共删除 3 个截图文件
[拒绝道具] 更新数据库...
[拒绝道具] 数据库更新成功
[拒绝道具] 验证 - 新状态: rejected
[拒绝道具] 验证 - screenshot_filename_base: None
```

### 4️⃣ 检查结果

**成功的标志**：
- 后端日志显示 "数据库更新成功"
- 验证日志显示 "新状态: rejected"
- 验证日志显示 "screenshot_filename_base: None"

**失败的标志**：
- 后端日志显示 "数据库更新失败"
- 或者出现异常堆栈

---

## 可能的问题和解决方案

### 问题1：数据库字段不存在
**症状**：后端报错 "no such column: screenshot_filename_base"

**解决方案**：
```bash
# 运行数据库迁移
cd c:\Users\bb162\Desktop\Yuuko-cs
MIGRATE_DATABASE.bat
```

### 问题2：数据库文件被锁定
**症状**：后端报错 "database is locked"

**解决方案**：
1. 关闭所有正在访问数据库的程序
2. 检查是否有多个后端服务器在运行（只能运行一个）
3. 重启后端服务器

### 问题3：update_status 方法不支持额外字段
**症状**：状态更新了，但 screenshot_filename_base 没有清空

**解决方案**：
这个问题应该已经被修复了。如果还有问题，请复制完整的后端日志。

---

## 验证数据库是否正确更新

### 方法1：通过后端日志
查看后端终端的验证日志：
```
[拒绝道具] 验证 - 新状态: rejected
[拒绝道具] 验证 - screenshot_filename_base: None
```

### 方法2：直接查询数据库
使用SQLite工具或命令：
```bash
cd backend\data
sqlite3 yuuko.db "SELECT hash, status, screenshot_filename_base FROM utilities WHERE hash='你的hash值';"
```

期望输出：
```
hash值|rejected|
```
（最后一个字段为空）

---

## 测试清单

- [ ] 1. 重启后端服务器
- [ ] 2. 刷新浏览器
- [ ] 3. 点击【拒绝】按钮
- [ ] 4. 检查后端终端日志
- [ ] 5. 确认道具从列表消失
- [ ] 6. 确认截图文件被删除
- [ ] 7. 确认日志显示 "新状态: rejected"
- [ ] 8. 确认日志显示 "screenshot_filename_base: None"

---

## 如果还有问题

请提供：
1. **完整的后端终端日志**（从 `[拒绝道具] 开始处理` 到最后）
2. **前端显示的错误信息**（如果有）
3. **浏览器控制台的错误**（按F12，查看Console标签）

这样我可以精确定位问题！

---

## 快速命令

```bash
# 重启后端
cd c:\Users\bb162\Desktop\Yuuko-cs\backend
# 按 Ctrl+C 停止旧服务器
python app.py

# 查询数据库（可选）
cd backend\data
sqlite3 yuuko.db
sqlite> SELECT hash, status, screenshot_filename_base FROM utilities LIMIT 5;
sqlite> .quit
```
