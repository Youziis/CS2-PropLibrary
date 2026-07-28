// ==================== 全局状态 ====================
const state = {
    allUtilities: [],
    filteredUtilities: [],
    currentMap: 'all',
    currentType: 'all',
    currentTeam: 'all',
    searchQuery: '',
    maps: [],
    currentView: 'list' // 'list' 或 'detail'
};

// ==================== 路由系统 ====================
const router = {
    routes: {},
    currentRoute: null,
    
    // 注册路由
    register(path, handler) {
        this.routes[path] = handler;
    },
    
    // 导航到指定路由
    navigate(path) {
        window.location.hash = path;
    },
    
    // 处理路由变化
    handleRoute() {
        const hash = window.location.hash.slice(1) || '/';
        
        // 匹配路由
        if (hash === '/' || hash === '') {
            this.routes['/']();
        } else if (hash.startsWith('/utility/')) {
            const utilityId = hash.split('/')[2];
            this.routes['/utility/:id'](utilityId);
        } else {
            this.routes['/'](); // 默认返回首页
        }
    },
    
    // 初始化路由
    init() {
        window.addEventListener('hashchange', () => this.handleRoute());
        window.addEventListener('load', () => this.handleRoute());
    }
};

// ==================== 初始化 ====================
document.addEventListener('DOMContentLoaded', async () => {
    await loadData();
    setupEventListeners();
    initRouter();
});

// 初始化路由
function initRouter() {
    // 注册路由
    router.register('/', showListView);
    router.register('/utility/:id', showDetailView);
    
    // 启动路由
    router.init();
}

// 显示列表视图
function showListView() {
    state.currentView = 'list';
    document.getElementById('list-view').style.display = 'block';
    document.getElementById('detail-view').style.display = 'none';
    document.body.classList.remove('detail-page');
}

// 显示详情视图
function showDetailView(utilityId) {
    state.currentView = 'detail';
    document.getElementById('list-view').style.display = 'none';
    document.getElementById('detail-view').style.display = 'block';
    document.body.classList.add('detail-page');
    
    renderDetailPage(utilityId);
}

// ==================== 数据加载 ====================
async function loadData() {
    try {
        // 加载索引文件
        const indexResponse = await fetch('data/utilities.json');
        
        if (!indexResponse.ok) {
            if (indexResponse.status === 404) {
                // 文件不存在，显示没有道具
                document.getElementById('loading').innerHTML = 
                    '<div style="text-align: center; padding: 40px;">' +
                    '<h3 style="color: #888;">📭 暂无道具数据</h3>' +
                    '<p style="color: #666; margin-top: 15px;">管理员正在整理道具，请稍后再来...</p>' +
                    '</div>';
                return;
            }
            throw new Error(`HTTP ${indexResponse.status}`);
        }
        
        const indexData = await indexResponse.json();
        
        if (!indexData.maps || indexData.maps.length === 0) {
            // 文件存在但没有数据
            document.getElementById('loading').innerHTML = 
                '<div style="text-align: center; padding: 40px;">' +
                '<h3 style="color: #888;">📭 暂无道具数据</h3>' +
                '<p style="color: #666; margin-top: 15px;">当前没有已发布的道具...</p>' +
                '</div>';
            return;
        }
        
        state.maps = indexData.maps;
        
        // 更新最后更新时间
        document.getElementById('last-update').textContent = 
            new Date(indexData.last_updated).toLocaleDateString('zh-CN');
        
        // 创建地图筛选器
        createMapFilters(state.maps);
        
        // 加载第一个地图的数据
        if (state.maps.length > 0) {
            await loadMapData(state.maps[0].name);
        }
        
        // 隐藏加载状态，显示内容
        document.getElementById('loading').style.display = 'none';
        document.getElementById('filters').style.display = 'block';
        
    } catch (error) {
        console.error('加载数据失败:', error);
        document.getElementById('loading').innerHTML = 
            '<div style="text-align: center; padding: 40px;">' +
            '<h3 style="color: #ff4655;">❌ 加载失败</h3>' +
            '<p style="color: #666; margin-top: 15px;">请刷新页面重试</p>' +
            '</div>';
    }
}

async function loadMapData(mapName) {
    try {
        const map = state.maps.find(m => m.name === mapName);
        if (!map) return;
        
        const response = await fetch(map.data_file);
        const mapData = await response.json();
        
        state.allUtilities = mapData.utilities;
        state.currentMap = mapName;
        
        applyFilters();
        
    } catch (error) {
        console.error(`加载地图 ${mapName} 失败:`, error);
    }
}

// ==================== 创建地图筛选器 ====================
function createMapFilters(maps) {
    const container = document.getElementById('map-filters');
    
    // 添加"全部"按钮
    const allBtn = document.createElement('button');
    allBtn.className = 'filter-btn active';
    allBtn.textContent = '全部地图';
    allBtn.onclick = async () => {
        // 加载所有地图数据
        state.allUtilities = [];
        for (const map of maps) {
            const response = await fetch(map.data_file);
            const mapData = await response.json();
            state.allUtilities.push(...mapData.utilities);
        }
        state.currentMap = 'all';
        setActiveButton(container, allBtn);
        applyFilters();
    };
    container.appendChild(allBtn);
    
    // 添加各个地图按钮
    maps.forEach(map => {
        const btn = document.createElement('button');
        btn.className = 'filter-btn';
        btn.textContent = map.display_name;
        btn.onclick = async () => {
            await loadMapData(map.name);
            setActiveButton(container, btn);
        };
        container.appendChild(btn);
    });
}

// ==================== 事件监听 ====================
function setupEventListeners() {
    // 道具类型筛选
    document.querySelectorAll('[data-type]').forEach(btn => {
        btn.addEventListener('click', (e) => {
            state.currentType = e.target.dataset.type;
            setActiveButton(e.target.parentElement, e.target);
            applyFilters();
        });
    });
    
    // 队伍筛选
    document.querySelectorAll('[data-team]').forEach(btn => {
        btn.addEventListener('click', (e) => {
            state.currentTeam = e.target.dataset.team;
            setActiveButton(e.target.parentElement, e.target);
            applyFilters();
        });
    });
    
    // 搜索
    const searchInput = document.getElementById('search-input');
    if (searchInput) {
        searchInput.addEventListener('input', (e) => {
            state.searchQuery = e.target.value.toLowerCase();
            applyFilters();
        });
    }
}

function setActiveButton(container, activeBtn) {
    container.querySelectorAll('.filter-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    activeBtn.classList.add('active');
}

// ==================== 筛选逻辑 ====================
function applyFilters() {
    let filtered = [...state.allUtilities];
    
    // 道具类型筛选
    if (state.currentType !== 'all') {
        filtered = filtered.filter(u => u.type === state.currentType);
    }
    
    // 队伍筛选
    if (state.currentTeam !== 'all') {
        filtered = filtered.filter(u => u.team === state.currentTeam);
    }
    
    // 搜索筛选
    if (state.searchQuery) {
        filtered = filtered.filter(u => 
            u.name.toLowerCase().includes(state.searchQuery) ||
            u.thrower.toLowerCase().includes(state.searchQuery) ||
            u.description.toLowerCase().includes(state.searchQuery)
        );
    }
    
    state.filteredUtilities = filtered;
    renderUtilities();
    updateStats();
}

// ==================== 渲染道具列表 ====================
function renderUtilities() {
    const grid = document.getElementById('utilities-grid');
    const emptyState = document.getElementById('empty-state');
    
    if (state.filteredUtilities.length === 0) {
        grid.innerHTML = '';
        emptyState.style.display = 'block';
        return;
    }
    
    emptyState.style.display = 'none';
    
    grid.innerHTML = state.filteredUtilities.map(utility => `
        <div class="utility-card" onclick="router.navigate('/utility/${utility.id}')">
            <img 
                class="utility-image" 
                src="${utility.screenshots.position || 'images/placeholder.jpg'}" 
                alt="${utility.name}"
                loading="lazy"
            >
            <div class="utility-info">
                <div class="utility-header">
                    <span class="utility-team team-${utility.team.toLowerCase()}">${utility.team}</span>
                </div>
                <div class="utility-name">${utility.name}</div>
                <div class="utility-meta">
                    ${utility.description}
                </div>
            </div>
        </div>
    `).join('');
}

function getUtilityIcon(type) {
    const icons = {
        'smoke': '💨',
        'flashbang': '⚡',
        'hegrenade': '💣',
        'molotov': '🔥',
        'incendiary': '🔥'
    };
    return icons[type] || '❓';
}

// ==================== 更新统计信息 ====================
function updateStats() {
    const stats = document.getElementById('stats');
    stats.textContent = `显示 ${state.filteredUtilities.length} 个道具 / 共 ${state.allUtilities.length} 个`;
}

// ==================== 渲染详情页面 ====================
function renderDetailPage(utilityId) {
    const utility = state.allUtilities.find(u => u.id === utilityId);
    
    if (!utility) {
        document.getElementById('detail-content').innerHTML = `
            <div style="text-align: center; padding: 60px 20px;">
                <h2>😔 道具未找到</h2>
                <p style="color: var(--text-secondary); margin: 20px 0;">该道具可能已被删除或ID不正确</p>
                <button class="btn-back" onclick="router.navigate('/')">← 返回列表</button>
            </div>
        `;
        return;
    }
    
    const content = document.getElementById('detail-content');
    
    content.innerHTML = `
        <div class="detail-header">
            <button class="btn-back" onclick="router.navigate('/')">← 返回列表</button>
            <h1 class="detail-title">${utility.name}</h1>
            <div class="detail-badges">
                <span class="badge badge-type">${getUtilityTypeName(utility.type)}</span>
                <span class="badge badge-team team-${utility.team.toLowerCase()}">${utility.team}</span>
                <span class="badge badge-throw">${getThrowTypeName(utility.throw_type)}</span>
            </div>
        </div>
        
        <div class="detail-body">
            <div class="detail-images-section">
                <h3>📸 截图预览</h3>
                <div class="detail-images">
                    <div class="detail-image-item">
                        <h4>站位图</h4>
                        <img class="detail-image" src="${utility.screenshots.position}" alt="站位图" onclick="openFullImage('${utility.screenshots.position}')">
                    </div>
                    <div class="detail-image-item">
                        <h4>准星位置</h4>
                        <img class="detail-image" src="${utility.screenshots.crosshair}" alt="准星图" onclick="openFullImage('${utility.screenshots.crosshair}')">
                    </div>
                    <div class="detail-image-item">
                        <h4>落点位置</h4>
                        <img class="detail-image" src="${utility.screenshots.landing}" alt="落点图" onclick="openFullImage('${utility.screenshots.landing}')">
                    </div>
                </div>
            </div>
            
            <div class="detail-info-section">
                <div class="detail-section">
                    <h3>📋 基本信息</h3>
                    <div class="info-grid">
                        <div class="info-item">
                            <span class="info-label">道具名称</span>
                            <span class="info-value">${utility.name}</span>
                        </div>
                        <div class="info-item">
                            <span class="info-label">类型</span>
                            <span class="info-value">${getUtilityTypeName(utility.type)}</span>
                        </div>
                        <div class="info-item">
                            <span class="info-label">队伍</span>
                            <span class="info-value">${utility.team}</span>
                        </div>
                        <div class="info-item">
                            <span class="info-label">投掷方式</span>
                            <span class="info-value">${getThrowTypeName(utility.throw_type)}</span>
                        </div>
                        <div class="info-item">
                            <span class="info-label">飞行时间</span>
                            <span class="info-value">${utility.flight_time} 秒</span>
                        </div>
                        ${utility.notes ? `
                        <div class="info-item" style="grid-column: 1 / -1;">
                            <span class="info-label">备注</span>
                            <span class="info-value">${utility.notes}</span>
                        </div>
                        ` : ''}
                    </div>
                </div>
                
                <div class="detail-section">
                    <h3>🎮 控制台命令</h3>
                    <div class="command-box">
                        <code id="command-text">${utility.command}</code>
                        <button class="copy-btn" onclick="copyCommand()">📋 复制</button>
                    </div>
                    <p class="command-hint">
                        在CS2游戏中按 <kbd>~</kbd> 打开控制台，粘贴命令后按回车即可传送到投掷位置
                    </p>
                </div>
                
                <div class="detail-section">
                    <h3>📍 坐标信息</h3>
                    <div class="coordinates">
                        <div class="coord-item">
                            <strong>投掷位置:</strong>
                            <span>X: ${utility.position.x.toFixed(2)}, Y: ${utility.position.y.toFixed(2)}, Z: ${utility.position.z.toFixed(2)}</span>
                        </div>
                        <div class="coord-item">
                            <strong>准星角度:</strong>
                            <span>Pitch: ${utility.angles.pitch.toFixed(2)}°, Yaw: ${utility.angles.yaw.toFixed(2)}°</span>
                        </div>
                        <div class="coord-item">
                            <strong>落点位置:</strong>
                            <span>X: ${utility.land_position.x.toFixed(2)}, Y: ${utility.land_position.y.toFixed(2)}, Z: ${utility.land_position.z.toFixed(2)}</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
}

// 原来的 showDetail 函数已被 renderDetailPage 替代，移除 closeModal 和 modal 相关代码

function getUtilityTypeName(type) {
    const names = {
        'smoke': '烟雾弹',
        'flashbang': '闪光弹',
        'hegrenade': '手雷',
        'molotov': '燃烧弹 (T)',
        'incendiary': '燃烧弹 (CT)'
    };
    return names[type] || type;
}

function getThrowTypeName(type) {
    const names = {
        'jump': '跳投',
        'stand': '站投',
        'crouch': '蹲投',
        'elevated': '高台投'
    };
    return names[type] || type;
}

// ==================== 复制命令 ====================
function copyCommand() {
    const commandText = document.getElementById('command-text').textContent;
    const btn = document.querySelector('.copy-btn');
    
    navigator.clipboard.writeText(commandText).then(() => {
        btn.textContent = '✅ 已复制';
        btn.classList.add('copied');
        
        setTimeout(() => {
            btn.textContent = '📋 复制';
            btn.classList.remove('copied');
        }, 2000);
    }).catch(err => {
        console.error('复制失败:', err);
        alert('复制失败，请手动复制');
    });
}

// ==================== 打开全屏图片 ====================
function openFullImage(src) {
    window.open(src, '_blank');
}
