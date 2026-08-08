# 审核页面功能更新说明

## 更新时间
2026-08-08

## 主要变更

### 1. 按钮功能调整

#### 原来：
- ✓ 批准
- 🗑️ 删除

#### 现在：
- ✓ 批准（功能不变）
- ✗ 拒绝（原删除按钮改为拒绝）
- × 删除（卡片右上角新增的删除按钮）

---

## 功能说明

### 【拒绝】按钮
**位置**：卡片底部，批准按钮旁边
**功能**：
1. 将道具状态改为 `rejected`（已拒绝）
2. **删除该道具的三张截图文件**：
   - `{地图}_{hash}_position.jpg` （站位图）
   - `{地图}_{hash}_crosshair.jpg` （描点图）
   - `{地图}_{hash}_landing.jpg` （落点图）
3. 清空数据库中的 `screenshot_id` 和 `screenshot_filename_base` 字段
4. **保留道具数据在数据库中**（方便后续查询或恢复）
5. 拒绝后的道具**不会再出现在"选择道具"列表中**

**使用场景**：
- 截图质量不好，但可能重新截图
- 道具投掷方式不好，暂时不需要
- 想保留解析数据，但不导出

**优点**：
- 数据不会丢失
- 可以通过数据库查询找回
- 释放截图占用的磁盘空间

---

### 【删除】按钮（右上角 ×）
**位置**：道具卡片右上角
**功能**：
1. **永久删除道具数据**（从数据库中完全删除）
2. **删除该道具的三张截图文件**
3. 无法恢复

**使用场景**：
- 确定不需要这个道具了
- 解析错误的垃圾数据
- 需要彻底清理

**优点**：
- 彻底清理不需要的数据
- 释放数据库空间
- 释放截图占用的磁盘空间

**注意**：
⚠️ 此操作不可恢复！建议谨慎使用。

---

## 状态流转

```
parsed（已解析）
  ↓ 选择
selected（已选择）
  ↓ 截图
screenshotted（待审核）
  ↓ 审核
  ├─ 批准 → approved（已批准）→ exported（已导出）
  ├─ 拒绝 → rejected（已拒绝，保留数据，删除截图）
  └─ 删除 → 永久删除（数据 + 截图全部删除）
```

---

## 数据库变更

### `rejected` 状态
- **状态名称**：`rejected`
- **状态描述**：已拒绝
- **特点**：
  - 不会出现在"选择道具"列表（`/api/all_pending` 不包含此状态）
  - 不会出现在"待审核"列表（`/api/pending` 不包含此状态）
  - 保留所有解析数据
  - 截图文件已删除

---

## API 变更

### 1. `/api/reject` (POST)
**变更前**：
- 只更新状态为 `rejected`

**变更后**：
- 更新状态为 `rejected`
- 删除三张截图文件
- 清空 `screenshot_id` 和 `screenshot_filename_base` 字段

---

### 2. `/api/delete_pending` (POST)
**变更前**：
- 只删除数据库记录

**变更后**：
- 删除三张截图文件
- 删除数据库记录

---

### 3. `/api/all_pending` (GET)
**变更前**：
- 只返回 `parsed` 状态的道具

**变更后**：
- 返回 `parsed` + `selected` + `screenshotted` 状态的道具
- **不包含 `rejected` 状态**（确保拒绝的道具不会再次出现）

---

## 前端变更

### 1. 审核页面卡片（`renderUtilityCard`）
**HTML结构**：
```html
<div class="utility-card">
  <!-- 新增：右上角删除按钮 -->
  <button class="btn-card-delete" onclick="deleteUtilityPermanently(hash)">×</button>
  
  <!-- 原有内容... -->
  
  <div class="actions">
    <button class="btn-approve">✓ 批准</button>
    <!-- 修改：删除改为拒绝 -->
    <button class="btn-reject">✗ 拒绝</button>
  </div>
</div>
```

### 2. CSS样式
**新增**：`.btn-card-delete` 样式
- 圆形按钮
- 红色背景
- 悬停时放大 + 旋转90度
- 位于卡片右上角

### 3. JavaScript函数
**新增**：
- `deleteUtilityPermanently(hash)` - 永久删除道具

**修改**：
- `rejectUtility(hash)` - 更新提示信息，说明会删除截图

---

## 使用建议

### 什么时候用【拒绝】？
✅ 截图质量不行，想重新截
✅ 投掷方式不理想，暂时不需要
✅ 想保留数据以便日后查询
✅ 释放截图空间但保留记录

### 什么时候用【删除】？
✅ 确定永远不需要这个道具
✅ 解析出错的垃圾数据
✅ 彻底清理不需要的数据
⚠️ 注意：此操作不可恢复！

---

## 测试场景

### 场景1：拒绝道具
1. 进入"审核道具"页面
2. 找到一个道具
3. 点击【拒绝】按钮
4. 确认操作
5. **验证**：
   - 道具消失
   - 截图文件被删除（检查 `output/screenshots/` 目录）
   - 数据库中状态为 `rejected`，`screenshot_id` 和 `screenshot_filename_base` 为空
   - "选择道具"页面不再显示该道具

### 场景2：永久删除道具
1. 进入"审核道具"页面
2. 找到一个道具
3. 点击右上角【×】按钮
4. 确认操作
5. **验证**：
   - 道具消失
   - 截图文件被删除
   - 数据库中完全没有该道具记录

---

## 回滚方案

如果需要恢复旧版本：
1. 恢复 `client/admin/script.js` 中的 `renderUtilityCard` 和相关函数
2. 恢复 `client/admin/style.css` 中的样式
3. 恢复 `backend/app.py` 中的 `/api/reject` 和 `/api/delete_pending` 端点
4. 恢复 `backend/routes/utility.py` 中的 `/api/all_pending` 端点

---

## 后续改进建议

1. **批量拒绝**：添加批量选择 + 批量拒绝功能
2. **拒绝原因**：记录拒绝原因（如"截图模糊"、"投掷不准"等）
3. **恢复功能**：添加"已拒绝"列表，可以恢复被拒绝的道具
4. **统计信息**：在统计卡片中显示已拒绝道具数量

---

## 相关文件清单

### 修改的文件：
1. `client/admin/script.js` - 前端逻辑
2. `client/admin/style.css` - 样式
3. `backend/app.py` - 后端API
4. `backend/routes/utility.py` - 道具路由

### 未修改的文件：
- `backend/database.py` - 数据库操作（已有完整的状态管理）
- `client/admin/index.html` - HTML结构
- 其他文件

---

## 完成 ✅

所有修改已完成，可以启动后端服务器进行测试：

```bash
cd backend
python app.py
```

访问：http://localhost:5000
