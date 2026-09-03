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
    imageViewer.init();
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
        // 添加时间戳参数防止缓存
        const timestamp = new Date().getTime();
        const indexResponse = await fetch(`data/utilities.json?t=${timestamp}`);
        
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

async function loadAllUtilitiesData() {
    // 如果已经加载过，直接返回
    if (state.allUtilities.length > 0) {
        return;
    }
    
    // 先加载索引
    if (state.maps.length === 0) {
        await loadData();
    }
    
    // 加载所有地图的道具数据
    const allUtilities = [];
    const timestamp = new Date().getTime(); // 添加时间戳防止缓存
    for (const map of state.maps) {
        try {
            const response = await fetch(`${map.data_file}?t=${timestamp}`);
            const mapData = await response.json();
            allUtilities.push(...mapData.utilities);
        } catch (error) {
            console.error(`加载地图 ${map.name} 数据失败:`, error);
        }
    }
    
    state.allUtilities = allUtilities;
}

async function loadMapData(mapName) {
    try {
        const map = state.maps.find(m => m.name === mapName);
        if (!map) return;
        
        const timestamp = new Date().getTime(); // 添加时间戳防止缓存
        const response = await fetch(`${map.data_file}?t=${timestamp}`);
        const mapData = await response.json();
        state.allUtilities = mapData.utilities;
        
    } catch (error) {
        console.error(`加载地图 ${mapName} 失败:`, error);
    }
}

async function loadAllUtilities() {
    try {
        state.allUtilities = [];
        const timestamp = new Date().getTime(); // 添加时间戳防止缓存
        for (const map of state.maps) {
            const response = await fetch(`${map.data_file}?t=${timestamp}`);
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
            (u.throw_type && u.throw_type.toLowerCase().includes(state.searchQuery))
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
    
    grid.innerHTML = state.filteredUtilities.map(utility => {
        // 获取前5个标签
        const tags = utility.tags && utility.tags.length > 0 
            ? utility.tags.slice(0, 5)
            : [];
        
        const tagsHtml = tags.length > 0
            ? `<div class="utility-tags">
                   ${tags.map(tag => `<span class="mini-tag">${tag}</span>`).join('')}
               </div>`
            : '';
        
        return `
            <div class="utility-card" onclick="router.navigate('/utility/${utility.id}')">
                <img 
                    class="utility-image" 
                    src="${utility.screenshots.position}" 
                    alt="${utility.name}"
                    loading="lazy"
                    decoding="async"
                >
                <div class="utility-info">
                    <div class="utility-name">${utility.name}</div>
                    <div class="utility-meta">${utility.throw_type || '未知投掷方式'}</div>
                    ${tagsHtml}
                </div>
            </div>
        `;
    }).join('');
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
    
    // 如果数据还没加载，先加载数据再渲染详情页
    if (state.allUtilities.length === 0) {
        loadAllUtilitiesData().then(() => {
            renderDetailPage(utilityId);
        });
    } else {
        renderDetailPage(utilityId);
    }
}

function renderDetailPage(utilityId) {
    const utility = state.allUtilities.find(u => u.id === utilityId);
    
    if (!utility) {
        document.getElementById('detail-content').innerHTML = `
            <div style="text-align: center; padding: 60px 20px;">
                <h2>(っ˘ω˘ς)道具未找到</h2>
                <p style="color: var(--text-secondary); margin: 20px 0;">该道具可能已被删除或ID不正确</p>
                <button class="btn-back" onclick="history.back()">← 返回</button>
            </div>
        `;
        return;
    }
    
    const content = document.getElementById('detail-content');
    
    // 处理标签显示
    const tagsHtml = utility.tags && utility.tags.length > 0 
        ? `<div class="detail-tags">
               ${utility.tags.map(tag => `<span class="tag-badge">${tag}</span>`).join('')}
           </div>`
        : '';
    
    content.innerHTML = `
        <div class="detail-header">
            <button class="btn-back" onclick="history.back()">← 返回</button>
            <h1 class="detail-title">${utility.name}</h1>
            ${tagsHtml}
        </div>
        
        <div class="detail-body">
            <div class="detail-images-section">
                <h3>📸 截图预览</h3>
                <div class="detail-images">
                    <div class="detail-image-item">
                        <h4>站位图</h4>
                        <img class="detail-image" src="${utility.screenshots.position}" alt="站位图" loading="lazy" decoding="async" onclick="openImageViewer('${utility.screenshots.position}', '站位图', 'position')">
                    </div>
                    <div class="detail-image-item">
                        <h4>准星位置</h4>
                        <img class="detail-image detail-image-crosshair" src="${utility.screenshots.crosshair}" alt="准星图" loading="lazy" decoding="async" onclick="openImageViewer('${utility.screenshots.crosshair}', '准星位置', 'crosshair')">
                    </div>
                    <div class="detail-image-item">
                        <h4>落点位置</h4>
                        <img class="detail-image" src="${utility.screenshots.landing}" alt="落点图" loading="lazy" decoding="async" onclick="openImageViewer('${utility.screenshots.landing}', '落点位置', 'landing')">
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
                            <span class="info-value">${utility.throw_type || '未知'}</span>
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
                        <button class="copy-btn" onclick="copyCommand()">复制</button>
                    </div>
                    <p class="command-hint">
                        在CS2游戏中开启训练模式进入对应地图,按 <kbd>~</kbd> 打开控制台，
                        输入<kbd>sv_cheats 1</kbd>开启作弊模式后,
                        粘贴命令后按回车即可传送到投掷位置
                    </p>
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
    // 如果没有值，返回"未知"
    if (!type) return '未知';
    
    // 预定义的英文值翻译
    const names = {
        'jump': '跳投',
        'stand': '站投',
        'crouch': '蹲投',
        'elevated': '高台投',
        'unknown': '未知'
    };
    
    // 如果是预定义的英文值，返回翻译；否则返回原值（支持自定义投掷方式）
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

// ==================== 图片查看器 ====================
const imageViewer = {
    currentImageType: null,
    currentScale: 1,
    crosshairSettings: {
        style: 'small',     // 'dot', 'small', 'large'
        size: 20,
        thickness: 2,
        gap: 4,
        showDot: true,
        dotSize: 2,
        colorR: 0,
        colorG: 255,
        colorB: 0,
        outline: false
    },
    
    init() {
        // ESC 键关闭
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                const modal = document.getElementById('image-viewer-modal');
                if (modal && modal.style.display === 'block') {
                    this.close();
                }
            }
        });
        
        // 鼠标滚轮缩放
        const container = document.getElementById('image-container');
        if (container) {
            container.addEventListener('wheel', (e) => {
                e.preventDefault();
                const delta = e.deltaY > 0 ? -0.1 : 0.1;
                this.zoom(delta);
            });
        }
    },
    
    open(src, title, imageType) {
        this.currentImageType = imageType;
        this.currentScale = 1;
        
        const modal = document.getElementById('image-viewer-modal');
        const image = document.getElementById('viewer-image');
        const titleEl = document.getElementById('viewer-title');
        const container = document.getElementById('image-container');
        const crosshairSettings = document.getElementById('crosshair-settings');
        
        // 设置图片
        image.src = src;
        titleEl.textContent = title;
        modal.style.display = 'block';
        container.style.transform = 'scale(1)';
        
        // 只有准星位置图才显示准星设置
        if (imageType === 'crosshair') {
            crosshairSettings.classList.add('active');
            // 等待图片加载完成后绘制准星
            image.onload = () => {
                this.drawCrosshair();
            };
        } else {
            crosshairSettings.classList.remove('active');
        }
        
        this.updateZoomLevel();
    },
    
    close() {
        document.getElementById('image-viewer-modal').style.display = 'none';
        this.currentScale = 1;
    },
    
    zoom(delta) {
        this.currentScale = Math.max(0.5, Math.min(5, this.currentScale + delta));
        document.getElementById('image-container').style.transform = `scale(${this.currentScale})`;
        this.updateZoomLevel();
    },
    
    reset() {
        this.currentScale = 1;
        document.getElementById('image-container').style.transform = 'scale(1)';
        this.updateZoomLevel();
    },
    
    updateZoomLevel() {
        document.getElementById('zoom-level').textContent = `${Math.round(this.currentScale * 100)}%`;
    },
    
    drawCrosshair() {
        const svg = document.getElementById('crosshair-svg');
        const image = document.getElementById('viewer-image');
        const settings = this.crosshairSettings;
        
        // 清空 SVG
        svg.innerHTML = '';
        
        // 获取图片尺寸
        const width = image.naturalWidth;
        const height = image.naturalHeight;
        
        if (!width || !height) return;
        
        // 设置 SVG 尺寸为图片原始尺寸
        svg.setAttribute('width', width);
        svg.setAttribute('height', height);
        svg.setAttribute('viewBox', `0 0 ${width} ${height}`);
        
        // 图片中心点
        const cx = width / 2;
        const cy = height / 2;
        
        // 更新显示的数值
        document.getElementById('size-value').textContent = settings.size;
        document.getElementById('thickness-value').textContent = settings.thickness;
        document.getElementById('gap-value').textContent = settings.gap;
        document.getElementById('dot-size-value').textContent = settings.dotSize;
        
        // 绘制线条的辅助函数
        const drawLine = (x1, y1, x2, y2) => {
            if (settings.outline) {
                // 黑色描边
                const outlineLine = document.createElementNS('http://www.w3.org/2000/svg', 'line');
                outlineLine.setAttribute('x1', x1);
                outlineLine.setAttribute('y1', y1);
                outlineLine.setAttribute('x2', x2);
                outlineLine.setAttribute('y2', y2);
                outlineLine.setAttribute('stroke', '#000000');
                outlineLine.setAttribute('stroke-width', settings.thickness + 2);
                outlineLine.setAttribute('stroke-linecap', 'butt');
                svg.appendChild(outlineLine);
            }
            
            // 主线条
            const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
            line.setAttribute('x1', x1);
            line.setAttribute('y1', y1);
            line.setAttribute('x2', x2);
            line.setAttribute('y2', y2);
            line.setAttribute('stroke', `rgb(${settings.colorR}, ${settings.colorG}, ${settings.colorB})`);
            line.setAttribute('stroke-width', settings.thickness);
            line.setAttribute('stroke-linecap', 'butt');
            svg.appendChild(line);
        };
        
        // 根据样式绘制准星
        if (settings.style === 'dot') {
            // 只有中心点
        } else if (settings.style === 'small') {
            // 小准星：四条短线
            const size = settings.size;
            const gap = settings.gap;
            drawLine(cx, cy - gap, cx, cy - gap - size);        // 上
            drawLine(cx, cy + gap, cx, cy + gap + size);        // 下
            drawLine(cx - gap, cy, cx - gap - size, cy);        // 左
            drawLine(cx + gap, cy, cx + gap + size, cy);        // 右
        } else if (settings.style === 'large') {
            // 大准星：从中心到边缘的完整线条
            const gap = settings.gap;
            drawLine(cx, gap, cx, cy - gap);                    // 上
            drawLine(cx, cy + gap, cx, height - gap);           // 下
            drawLine(gap, cy, cx - gap, cy);                    // 左
            drawLine(cx + gap, cy, width - gap, cy);            // 右
        }
        
        // 绘制中心点
        if (settings.showDot) {
            if (settings.outline) {
                const outlineDot = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
                outlineDot.setAttribute('cx', cx);
                outlineDot.setAttribute('cy', cy);
                outlineDot.setAttribute('r', settings.dotSize + 1);
                outlineDot.setAttribute('fill', '#000000');
                svg.appendChild(outlineDot);
            }
            
            const dot = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
            dot.setAttribute('cx', cx);
            dot.setAttribute('cy', cy);
            dot.setAttribute('r', settings.dotSize);
            dot.setAttribute('fill', `rgb(${settings.colorR}, ${settings.colorG}, ${settings.colorB})`);
            svg.appendChild(dot);
        }
    }
};

// 全局函数供 HTML 调用
function openImageViewer(src, title, type) {
    imageViewer.open(src, title, type);
}

function closeImageViewer() {
    imageViewer.close();
}

function zoomIn() {
    imageViewer.zoom(0.2);
}

function zoomOut() {
    imageViewer.zoom(-0.2);
}

function resetZoom() {
    imageViewer.reset();
}

function updateCrosshair() {
    const settings = imageViewer.crosshairSettings;
    
    settings.size = parseInt(document.getElementById('crosshair-size').value);
    settings.thickness = parseInt(document.getElementById('crosshair-thickness').value);
    settings.gap = parseInt(document.getElementById('crosshair-gap').value);
    settings.showDot = document.getElementById('crosshair-dot').checked;
    settings.dotSize = parseInt(document.getElementById('dot-size').value);
    settings.outline = document.getElementById('crosshair-outline').checked;
    
    imageViewer.drawCrosshair();
}

function setCrosshairStyle(style) {
    imageViewer.crosshairSettings.style = style;
    
    // 更新按钮状态
    document.querySelectorAll('.style-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    const activeBtn = document.querySelector(`[data-style="${style}"]`);
    if (activeBtn) {
        activeBtn.classList.add('active');
    }
    
    // 根据准星样式显示/隐藏相关设置
    const sizeGroup = document.getElementById('setting-size');
    const thicknessGroup = document.getElementById('setting-thickness');
    const gapGroup = document.getElementById('setting-gap');
    
    if (style === 'dot') {
        // 仅中心点：隐藏大小、厚度、间隙
        if (sizeGroup) sizeGroup.style.display = 'none';
        if (thicknessGroup) thicknessGroup.style.display = 'none';
        if (gapGroup) gapGroup.style.display = 'none';
    } else if (style === 'large') {
        // 大准星：隐藏大小、间隙，显示厚度
        if (sizeGroup) sizeGroup.style.display = 'none';
        if (thicknessGroup) thicknessGroup.style.display = 'block';
        if (gapGroup) gapGroup.style.display = 'none';
    } else {
        // 小准星（small）：显示全部
        if (sizeGroup) sizeGroup.style.display = 'block';
        if (thicknessGroup) thicknessGroup.style.display = 'block';
        if (gapGroup) gapGroup.style.display = 'block';
    }
    
    imageViewer.drawCrosshair();
}

function updateCrosshairColor() {
    const settings = imageViewer.crosshairSettings;
    
    // 获取RGB值
    settings.colorR = parseInt(document.getElementById('color-r').value);
    settings.colorG = parseInt(document.getElementById('color-g').value);
    settings.colorB = parseInt(document.getElementById('color-b').value);
    
    // 更新显示的数值
    document.getElementById('color-r-value').textContent = settings.colorR;
    document.getElementById('color-g-value').textContent = settings.colorG;
    document.getElementById('color-b-value').textContent = settings.colorB;
    
    // 更新颜色预览
    const preview = document.getElementById('color-preview');
    if (preview) {
        preview.style.background = `rgb(${settings.colorR}, ${settings.colorG}, ${settings.colorB})`;
    }
    
    imageViewer.drawCrosshair();
}

function setCrosshairColor(color) {
    // 保留旧函数以防兼容性问题，但现在使用RGB滑动条
    imageViewer.drawCrosshair();
}
