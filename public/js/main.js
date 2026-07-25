// ==================== 全局状态 ====================
const state = {
    allUtilities: [],
    filteredUtilities: [],
    currentMap: 'all',
    currentType: 'all',
    currentTeam: 'all',
    searchQuery: '',
    maps: []
};

// ==================== 初始化 ====================
document.addEventListener('DOMContentLoaded', async () => {
    await loadData();
    setupEventListeners();
});

// ==================== 数据加载 ====================
async function loadData() {
    try {
        // 加载索引文件
        const indexResponse = await fetch('data/utilities.json');
        const indexData = await indexResponse.json();
        
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
            '<p style="color: #ff4655;">❌ 加载失败，请刷新页面重试</p>';
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
    document.getElementById('search-input').addEventListener('input', (e) => {
        state.searchQuery = e.target.value.toLowerCase();
        applyFilters();
    });
    
    // 模态框关闭
    document.querySelector('.close').addEventListener('click', closeModal);
    window.addEventListener('click', (e) => {
        const modal = document.getElementById('detail-modal');
        if (e.target === modal) {
            closeModal();
        }
    });
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
        <div class="utility-card" onclick="showDetail('${utility.id}')">
            <img 
                class="utility-image" 
                src="${utility.screenshots.position || 'images/placeholder.jpg'}" 
                alt="${utility.name}"
                loading="lazy"
            >
            <div class="utility-info">
                <div class="utility-header">
                    <span class="utility-type">${getUtilityIcon(utility.type)}</span>
                    <span class="utility-team team-${utility.team.toLowerCase()}">${utility.team}</span>
                </div>
                <div class="utility-name">${utility.name}</div>
                <div class="utility-meta">
                    ${utility.description}
                </div>
                <div class="utility-meta">
                    投掷者: ${utility.thrower}
                </div>
                <div class="utility-tags">
                    ${utility.tags.map(tag => `<span class="tag">${tag}</span>`).join('')}
                    <span class="tag">${'⭐'.repeat(utility.quality)}</span>
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

// ==================== 显示详情 ====================
function showDetail(utilityId) {
    const utility = state.filteredUtilities.find(u => u.id === utilityId);
    if (!utility) return;
    
    const modal = document.getElementById('detail-modal');
    const content = document.getElementById('detail-content');
    
    content.innerHTML = `
        <h2>${getUtilityIcon(utility.type)} ${utility.name}</h2>
        
        <div class="detail-images">
            <div>
                <h4>站位图</h4>
                <img class="detail-image" src="${utility.screenshots.position}" alt="站位图" onclick="openFullImage('${utility.screenshots.position}')">
            </div>
            <div>
                <h4>准星位置</h4>
                <img class="detail-image" src="${utility.screenshots.crosshair}" alt="准星图" onclick="openFullImage('${utility.screenshots.crosshair}')">
            </div>
            <div>
                <h4>落点位置</h4>
                <img class="detail-image" src="${utility.screenshots.landing}" alt="落点图" onclick="openFullImage('${utility.screenshots.landing}')">
            </div>
        </div>
        
        <div class="detail-section">
            <h3>📋 基本信息</h3>
            <p><strong>类型:</strong> ${getUtilityTypeName(utility.type)}</p>
            <p><strong>队伍:</strong> ${utility.team}</p>
            <p><strong>投掷方式:</strong> ${getThrowTypeName(utility.throw_type)}</p>
            <p><strong>飞行时间:</strong> ${utility.flight_time} 秒</p>
            <p><strong>投掷距离:</strong> ${utility.distance} 单位</p>
            <p><strong>投掷者:</strong> ${utility.thrower}</p>
        </div>
        
        <div class="detail-section">
            <h3>🎮 控制台命令</h3>
            <div class="command-box">
                <code id="command-text">${utility.command}</code>
                <button class="copy-btn" onclick="copyCommand()">📋 复制</button>
            </div>
            <p style="color: var(--text-secondary); font-size: 0.9rem;">
                在CS2游戏中按 <kbd>~</kbd> 打开控制台，粘贴命令后按回车即可传送到投掷位置
            </p>
        </div>
        
        <div class="detail-section">
            <h3>📍 坐标信息</h3>
            <p><strong>投掷位置:</strong> X: ${utility.position.x.toFixed(2)}, Y: ${utility.position.y.toFixed(2)}, Z: ${utility.position.z.toFixed(2)}</p>
            <p><strong>准星角度:</strong> Pitch: ${utility.angles.pitch.toFixed(2)}°, Yaw: ${utility.angles.yaw.toFixed(2)}°</p>
            <p><strong>落点位置:</strong> X: ${utility.land_position.x.toFixed(2)}, Y: ${utility.land_position.y.toFixed(2)}, Z: ${utility.land_position.z.toFixed(2)}</p>
        </div>
    `;
    
    modal.style.display = 'block';
}

function closeModal() {
    document.getElementById('detail-modal').style.display = 'none';
}

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
