# GitHub 同步配置说明

## 当前配置

### ✅ 会上传到 GitHub 的文件：

1. **代码文件**
   - `public/` - 道具库前端（HTML, CSS, JS, 图标）
   - `client/` - 客户端工具（截图、导出等Python脚本）
   - `backend/` - 后端服务器（Flask API, 数据库操作）

2. **文档文件**
   - `*.md` - 所有Markdown文档
   - `README.md` - 项目说明

3. **配置和脚本**
   - `*.bat` - 批处理启动脚本
   - `.gitignore` - Git配置

---

### ❌ 不会上传到 GitHub 的文件：

1. **数据文件**
   - `backend/data/*.db` - SQLite数据库
   - `output/data/*.json` - JSON数据文件
   - `output/commands/*.json` - 截图命令文件

2. **截图和图片**
   - `output/screenshots/*.jpg` - 原始截图
   - `public/images/` - 导出的道具图片

3. **Demo文件**
   - `demos/*.dem` - CS2 Demo文件（体积大）

4. **临时和缓存文件**
   - `__pycache__/` - Python缓存
   - `*.pyc` - Python编译文件
   - `*.log` - 日志文件

5. **敏感信息**
   - `.env` - 环境变量
   - `*.db` - 数据库文件

6. **IDE配置**
   - `.vscode/` - VS Code配置
   - `.idea/` - PyCharm配置
   - `.kiro/` - Kiro AI配置

---

## Git 工作流程

### 首次提交（如果还没提交过）

```bash
# 1. 初始化 Git（如果还没有）
git init

# 2. 添加远程仓库（替换为你的仓库地址）
git remote add origin https://github.com/你的用户名/Yuuko-cs.git

# 3. 添加文件
git add .

# 4. 查看将要提交的文件
git status

# 5. 提交
git commit -m "Initial commit: 添加项目代码"

# 6. 推送到 GitHub
git push -u origin main
```

---

### 日常更新流程

每次修改代码后：

```bash
# 1. 查看修改的文件
git status

# 2. 添加所有修改的文件
git add .

# 或者只添加特定文件
git add backend/app.py
git add client/screenshot.py

# 3. 提交修改（写清楚修改内容）
git commit -m "修复: 拒绝道具功能，添加截图删除逻辑"

# 4. 推送到 GitHub
git push
```

---

### 常用 Git 命令

```bash
# 查看状态
git status

# 查看修改历史
git log

# 查看简洁的修改历史
git log --oneline

# 查看某个文件的修改历史
git log backend/app.py

# 查看具体修改内容
git diff

# 撤销未提交的修改
git checkout -- 文件名

# 查看远程仓库
git remote -v

# 拉取最新代码（如果在多台电脑工作）
git pull
```

---

## Cloudflare Pages 部署配置

### 部署设置

1. **构建命令**：留空（不需要构建）
2. **输出目录**：`public`
3. **根目录**：`/`（或留空）

### 自动部署流程

```
本地修改代码
    ↓
git commit & push
    ↓
GitHub 收到推送
    ↓
Cloudflare 自动检测
    ↓
自动部署 public/ 目录
    ↓
网站更新完成
```

### 部署时间
- 通常 1-3 分钟
- 可以在 Cloudflare Pages 控制台查看部署进度

---

## 最佳实践

### 提交消息规范

```bash
# 新增功能
git commit -m "功能: 添加道具拒绝功能"

# 修复Bug
git commit -m "修复: 解决拒绝道具状态不更新的问题"

# 优化
git commit -m "优化: 改进选择页面的筛选逻辑"

# 文档
git commit -m "文档: 更新README部署说明"

# 样式
git commit -m "样式: 优化已拒绝道具的视觉效果"
```

### 提交频率

**推荐**：
- 每完成一个功能就提交一次
- 修复一个Bug就提交一次
- 避免积累太多修改再提交

**避免**：
- 一次提交几百个文件的修改
- 提交消息写得太简单（如："更新"）

---

## 检查哪些文件会被上传

```bash
# 查看将要提交的文件
git status

# 查看被忽略的文件
git status --ignored

# 测试.gitignore规则（不会真的添加）
git add -n .
```

---

## 目录结构（上传到GitHub的部分）

```
Yuuko-cs/
├── backend/              ✅ 上传（Python代码）
│   ├── app.py
│   ├── database.py
│   ├── routes/
│   └── data/            ❌ 不上传（数据库文件）
│
├── client/              ✅ 上传（Python工具）
│   ├── screenshot.py
│   ├── export.py
│   ├── admin_server.py
│   └── admin/
│       ├── index.html
│       ├── script.js
│       └── style.css
│
├── public/              ✅ 上传（前端代码）
│   ├── index.html
│   ├── css/
│   ├── js/
│   ├── data/           ❌ 不上传（JSON数据）
│   └── images/         ❌ 不上传（道具图片）
│
├── demos/               ❌ 不上传（Demo文件）
├── output/              ❌ 不上传（截图和数据）
│
├── .gitignore          ✅ 上传
├── README.md           ✅ 上传
├── *.md                ✅ 上传（所有文档）
└── *.bat               ✅ 上传（启动脚本）
```

---

## 故障排除

### 问题1：推送失败
```bash
# 错误: 远程有更新
# 解决: 先拉取再推送
git pull
git push
```

### 问题2：不小心提交了不该提交的文件
```bash
# 从Git中移除但保留本地文件
git rm --cached 文件名

# 提交移除操作
git commit -m "移除不需要的文件"
git push
```

### 问题3：查看某个文件是否会被忽略
```bash
git check-ignore -v 文件名
```

---

## 快速命令清单

```bash
# 每次修改后的标准流程
git add .
git commit -m "描述你的修改"
git push

# 查看状态
git status

# 查看历史
git log --oneline

# 撤销修改
git checkout -- 文件名
```

---

## 完成 ✅

现在你的 `.gitignore` 已配置完成：
- ✅ 代码会上传（public, client, backend）
- ✅ 文档会上传（*.md, README.md）
- ✅ 脚本会上传（*.bat）
- ❌ 数据不上传（*.db, output/, demos/）
- ❌ 图片不上传（screenshots/, images/）

这样既能查看代码修改历史，又不会上传大量数据文件！
