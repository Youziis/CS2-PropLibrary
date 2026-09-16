# Yuuko CS2 道具库

在线访问：<https://yuukocs.cyou/>

从 CS2（Counter-Strike 2）职业比赛 demo 中批量提取投掷物数据，经过人工审核后导出成可直接部署的静态网站。

项目的核心是一条数据流水线：**解析 demo → 筛选道具 → 自动截图 → 人工审核 → 导出静态站**。后台管理界面负责中间的人工环节，公开网站则是纯静态文件，不依赖任何后端。

## 功能流程

1. **解析 Demo** — 读取 `demos/*.dem`，提取投掷事件、落点、投掷角度与位置，自动匹配投掷与爆炸事件并去重，结果写入 SQLite。
2. **选择道具** — 在后台按地图、类型、来源筛选，勾选需要制作描点的道具。
3. **自动截图** — 脚本控制 CS2 依次传送、对准、截图，每个道具产出站位图、准星图、落点图三张。
4. **审核** — 在后台批准、拒绝或删除；可编辑名称、类型、阵营、投掷方式、坐标、标签与备注，已导出的道具改动后会按地图自动重新导出。
5. **导出** — 压缩图片（准星图裁剪中心区域，其它图限制尺寸压缩），生成 `public/data/*.json` 与 `public/images/**`。
6. **访问网站** — 公开站读取 JSON 渲染地图、道具列表与详情页，支持按类型/标签筛选、控制台指令一键复制、准星样式叠加预览。

## 目录结构

| 目录 | 说明 |
| --- | --- |
| `backend/` | Flask 后台服务与数据层。`app.py` 为入口，`database.py` 封装 SQLite，`routes/` 放各业务蓝图，`export_service.py` 是唯一的导出实现 |
| `client/admin/` | 后台管理前端（原生 HTML/CSS/JS，无构建步骤），页面逻辑按功能拆在 `js/` 下 |
| `client/src/` | demo 解析与数据提取（`parser.py`、`extractor.py`） |
| `client/` | 命令行工具：`screenshot.py` 自动截图、`export.py` 导出、`sync_screenshots.py` 回填截图状态 |
| `public/` | 导出的静态网站：`index.html`、`js/main.js`、`css/style.css`、`data/`（JSON）、`images/`（截图） |
| `demos/` | 原始 demo 文件（体积大，不纳入版本控制） |
| `output/` | 中间产物：`screenshots/`（截图原图）、`commands/`（截图任务清单） |
| `backend/data/yuuko.db` | SQLite 数据库，全部道具数据与状态的唯一来源 |

## 技术栈

| 用途 | 依赖 |
| --- | --- |
| 后端服务 | Flask、Flask-CORS、Werkzeug |
| 图像处理 | Pillow |
| Demo 解析 | demoparser2、pandas、numpy |
| 自动截图（仅 Windows） | keyboard、pyperclip |
| 前端 | 原生 HTML / CSS / JavaScript，零框架、零打包 |

## 快速开始

### 1. 安装依赖

需要 Python 3.8 及以上：

```bash
pip install "Flask==3.0.0" "Flask-Cors==4.0.0" "Werkzeug==3.0.6" "Pillow==10.4.0" "demoparser2==0.41.3" "pandas==2.0.3" "numpy==1.24.4" "keyboard==0.13.5" "pyperclip==1.11.0"
```

> ⚠️ **请不要在仓库里新增 `requirements.txt`（或 `.python-version` 等构建配置文件）。**
> 本项目部署的是纯静态的 `public/` 目录，不需要构建；但静态托管平台（如 Cloudflare Pages）
> 一旦在仓库里发现 `requirements.txt`，就会自动执行 `pip install`，而它的构建镜像默认是
> Python 3.13，`pandas==2.0.3`、`numpy==1.24.4` 在该版本没有预编译包，会当场编译失败并导致整次部署失败。
> 依赖清单就以上面的命令为准，改动时请同步更新本段。

### 2. 启动管理后台

同时提供静态页面与 API，端口 5000：

```bash
python backend/app.py
```

打开 <http://localhost:5000> 即可使用后台：解析 demo、选择道具、审核、导出。

### 3. 预览公开网站

纯静态，端口 8000：

```bash
TEST_LOCAL.bat
```

打开 <http://localhost:8000>。部署时只需把 `public/` 目录上传到静态服务器。

### 4. 命令行工具（可选）

```bash
cd client
python screenshot.py --type smoke   # 自动截图，需 CS2 正在运行且窗口在前台
python sync_screenshots.py          # 按已有截图文件回填数据库状态
python export.py                    # 命令行导出（与后台导出同一套实现）
```

`screenshot.py` 的默认输入输出路径（`../output/...`）是相对当前目录的，所以要先进入 `client/` 再运行；也可以直接改 `--file` 与 `--output` 参数。

## 数据状态

道具在数据库中按状态流转，后台各页面即围绕这些状态组织：

```
parsed → selected → screenshotted → approved → exported
                          ↓
                       rejected（删除截图，保留数据，可重新选择）
```

`hash`（由投掷位置、角度、落点与武器类型生成）是道具的唯一标识，贯穿解析、审核与导出去重；`sort_id`（地图编号 × 10000 + 序号）决定前端展示顺序，在导出时分配。

## 说明

- 数据文件不纳入版本控制：`demos/`、`output/`、`backend/data/`（数据库）均被 `.gitignore` 忽略，请自行备份 `backend/data/yuuko.db`。
- 公开站的 `public/data/` 与 `public/images/` 是导出产物，重新导出时会按地图合并更新，不会丢掉其它地图的数据。
- 部署到 Cloudflare Pages 时，Build command 留空、Build output directory 填 `public`，不要添加任何依赖文件。
