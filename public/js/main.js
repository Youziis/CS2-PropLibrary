// ==================== 全局状态 ====================
const state = {
    allUtilities: [],
    filteredUtilities: [],
    currentType: 'all',
    searchQuery: '',
    maps: [],
    currentView: 'home'
};

// ==================== 路由系统 ====================
const router = {
    routes: {},
    
    register(path, handler) {
        this.routes[path] = handler;
    },
    
    navigate(path) {
        window.location.hash = path;
    },
    
    handleRoute() {
        const hash = window.location.hash.slice(1) || '/';
        
        if (hash === '/' || hash === '') {
            this.routes['/']();
        } else if (hash === '/maps') {
            this.routes['/maps']();
        } else if (hash === '/utilities') {
            this.routes['/utilities']();
        } else if (hash.startsWith('/map/')) {
            const mapName = hash.split('/')[2];
            this.routes['/map/:name'](mapName);
        } else if (hash.startsWith('/utility/')) {
            const utilityId = hash.split('/')[2];
            this.routes['/utility/:id'](utilityId);
        } else {
            this.routes['/']();
        }
    },
    
    init() {
        window.addEventListener('hashchange', () => this.handleRoute());
        this.handleRoute();
    }
};

// ==================== 初始化 ====================
document.addEventListener('DOMContentLoaded', async () => {
    await loadData();
    initRouter();
    setupHomeSearch();
});

function initRouter() {
    router.register('/', showHomePage);
    router.register('/maps', showMapsPage);
    router.register('/utilities', showUtilitiesPage);
    router.register('/map/:name', showMapUtilitiesPage);
    router.register('/utility/:id', showDetailPage);
    router.init();
}

// ==================== 数据加载 ====================
async function loadData() {
    try {
        const indexResponse = await fetch('data/utilities.json');
        
        if (!indexResponse.ok) {
            if (indexResponse.status === 404) {
                document.getElementById('loading').innerHTML = 
                    '<div style="text-align: center; padding: 40px;"><h3 style="color: #888;">📭 暂无道具数据</h3></div>';
                return;
            }
            throw new Error(`HTTP ${indexResponse.status}`);
        }
        
        const indexData = await indexResponse.json();
        
        if (!indexData.maps || indexData.maps.length === 0) {
            document.getElementById('loading').innerHTML = 
                '<div style="text-align: center; padding: 40px;"><h3 style="color: #888;">📭 暂无道具数据</h3></div>';
            return;
        }
        
        state.maps = indexData.maps;
        
        const lastUpdateEl = document.getElementById('last-update');
        if (lastUpdateEl) {
            lastUpdateEl.textContent = new Date(indexData.last_updated).toLocaleDateString('zh-CN');
        }
        
        document.getElementById('loading').style.display = 'none';
        
    } catch (error) {
        console.error('加载数据失败:', error);
        document.getElementById('loading').innerHTML = 
            '<div style="text-align: center; padding: 40px;"><h3 style="color: #ff4655;">❌ 加载失败</h3></div>';
    }
}

async function loadMapData(mapName) {
    try {
        const map = state.maps.find(m => m.name === mapName);
        if (!map) return;
        
        const response = await fetch(map.data_file);
        const mapData = await response.json();
        state.allUtilities = mapData.utilities;
        
    } catch (error) {
        console.error(`加载地图 ${mapName} 失败:`, error);
    }
}

async function loadAllUtilities() {
    try {
        state.allUtilities = [];
        for (const map of state.maps) {
            const response = await fetch(map.data_file);
            const mapData = await response.json();
            state.allUtilities.push(...mapData.utilities);
        }
    } catch (error) {
        console.error('加载所有道具失败:', error);
    }
}

// ==================== 视图切换 ====================
function hideAllViews() {
    document.getElementById('home-view').style.display = 'none';
    document.getElementById('maps-view').style.display = 'none';
    document.getElementById('utilities-view').style.display = 'none';
    document.getElementById('detail-view').style.display = 'none';
}

// ==================== 首页 ====================
function showHomePage() {
    hideAllViews();
    document.getElementById('home-view').style.display = 'block';
    state.currentView = 'home';
}

function setupHomeSearch() {
    const searchInput = document.getElementById('home-search');
    const searchBtn = document.getElementById('home-search-btn');
    
    const performSearch = async () => {
        const query = searchInput.value.trim().toLowerCase();
        if (!query) {
            router.navigate('/utilities');
            return;
        }
        
        await loadAllUtilities();
        router.navigate('/utilities');
        
        setTimeout(() => {
            state.searchQuery = query;
            const utilitiesSearch = document.getElementById('utilities-search');
            if (utilitiesSearch) {
                utilitiesSearch.value = query;
            }
            applyFilters();
        }, 100);
    };
    
    if (searchBtn) {
        searchBtn.onclick = performSearch;
    }
    
    if (searchInput) {
        searchInput.onkeypress = (e) => {
            if (e.key === 'Enter') {
                performSearch();
            }
        };
    }
}

// ==================== 地图选择页 ====================
function showMapsPage() {
    hideAllViews();
    document.getElementById('maps-view').style.display = 'block';
    state.currentView = 'maps';
    renderMapsGrid();
}

function renderMapsGrid() {
    const grid = document.getElementById('maps-grid');
    
    grid.innerHTML = state.maps.map(map => `
        <div class="map-card" onclick="router.navigate('/map/${map.name}')">
            <div class="map-name">${map.display_name}</div>
            <div class="map-count">${map.utility_count} 个道具</div>
        </div>
    `).join('');
}

// ==================== 道具列表页 ====================
async function showUtilitiesPage() {
    hideAllViews();
    document.getElementById('utilities-view').style.display = 'block';
    state.currentView = 'utilities';
    
    document.getElementById('utilities-title').textContent = '所有道具';
    
    await loadAllUtilities();
    setupUtilitiesFilters();
    applyFilters();
}

async function showMapUtilitiesPage(mapName) {
    hideAllViews();
    document.getElementById('utilities-view').style.display = 'block';
    state.currentView = 'map';
    
    const map = state.maps.find(m => m.name === mapName);
    document.getElementById('utilities-title').textContent = map ? map.display_name : '道具列表';
    
    await loadMapData(mapName);
    setupUtilitiesFilters();
    applyFilters();
}

function setupUtilitiesFilters() {
    // 重置筛选状态
    state.currentType = 'all';
    state.searchQuery = '';
    
    // 道具类型筛选
    document.querySelectorAll('[data-type]').forEach(btn => {
        btn.onclick = () => {
            state.currentType = btn.dataset.type;
            setActiveButton(btn.parentElement, btn);
            applyFilters();
        };
    });
    
    // 搜索
    const searchInput = document.getElementById('utilities-search');
    if (searchInput) {
        searchInput.value = '';
        searchInput.oninput = (e) => {
            state.searchQuery = e.target.value.toLowerCase();
            applyFilters();
        };
    }
}

function setActiveButton(container, activeBtn) {
    container.querySelectorAll('.filter-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    activeBtn.classList.add('active');
}

function applyFilters() {
    let filtered = [...state.allUtilities];
    
    // 类型筛选
    if (state.currentType !== 'all') {
        filtered = filtered.filter(u => u.type === state.currentType);
    }
    
    // 搜索筛选
    if (state.searchQuery) {
        filtered = filtered.filter(u => 
            u.name.toLowerCase().includes(state.searchQuery) ||
            u.description.toLowerCase().includes(state.searchQuery)
        );
    }
    
    state.filteredUtilities = filtered;
    renderUtilities();
    updateStats();
}

function renderUtilities() {
    const grid = document.getElementById('utilities-grid');
    const emptyState = document.getElementById('utilities-empty');
    
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
                src="${utility.screenshots.position}" 
                alt="${utility.name}"
                loading="lazy"
            >
            <div class="utility-info">
                <div class="utility-header">
                    <span class="utility-team team-${utility.team.toLowerCase()}">${utility.team}</span>
                </div>
                <div class="utility-name">${utility.name}</div>
                <div class="utility-meta">${utility.description}</div>
            </div>
        </div>
    `).join('');
}

function updateStats() {
    const stats = document.getElementById('utilities-stats');
    if (stats) {
        stats.textContent = `显示 ${state.filteredUtilities.length} 个道具 / 共 ${state.allUtilities.length} 个`;
    }
}

// ==================== 详情页 ====================
function showDetailPage(utilityId) {
    hideAllViews();
    document.getElementById('detail-view').style.display = 'block';
    state.currentView = 'detail';
    renderDetailPage(utilityId);
}

function renderDetailPage(utilityId) {
    const utility = state.allUtilities.find(u => u.id === utilityId);
    
    if (!utility) {
        document.getElementById('detail-content').innerHTML = `
            <div style="text-align: center; padding: 60px 20px;">
                <h2>😔 道具未找到</h2>
                <p style="color: var(--text-secondary); margin: 20px 0;">该道具可能已被删除或ID不正确</p>
                <button class="btn-back" onclick="history.back()">← 返回</button>
            </div>
        `;
        return;
    }
    
    const content = document.getElementById('detail-content');
    
    content.innerHTML = `
        <div class="detail-header">
            <button class="btn-back" onclick="history.back()">← 返回</button>
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

// ==================== 辅助函数 ====================
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

function openFullImage(src) {
    window.open(src, '_blank');
}
