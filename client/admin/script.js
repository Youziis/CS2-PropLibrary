// 全局变量
let allUtilities = [];
let filteredUtilities = [];
let currentFilterDemo = 'all'; // 当前筛选的 demo
let currentFilterMap = 'all';  // 当前筛选的地图
let currentFilterScreenshot = 'all'; // 当前筛选的截图状态
let currentFilterType = 'all'; // 当前筛选的道具类型

const TYPE_NAMES = {
    'smoke': '烟雾弹',
    'flashbang': '闪光弹',
    'hegrenade': '手雷',
    'incendiary': '燃烧弹',
    'molotov': '燃烧弹'
};

// 初始化
document.addEventListener('DOMContentLoaded', function() {
    initTabs();
    initSidebarToggle();
    loadStats();
    loadOverviewStats();
    loadOverviewPendingStats();
    loadDemos();
    loadTypeStats();
    loadPending();
    loadExportStats();
    loadPendingExportUtilities();
});

// 侧边栏收缩展开功能
function initSidebarToggle() {
    const sidebar = document.getElementById('sidebar');
    const toggleBtn = document.getElementById('sidebar-toggle');
    
    if (!sidebar || !toggleBtn) return;
    
    // 从localStorage读取侧边栏状态
    const isCollapsed = localStorage.getItem('sidebarCollapsed') === 'true';
    if (isCollapsed) {
        sidebar.classList.add('collapsed');
    }
    
    // 点击切换按钮
    toggleBtn.addEventListener('click', function(e) {
        e.stopPropagation();
        sidebar.classList.toggle('collapsed');
        
        // 保存状态到localStorage
        const collapsed = sidebar.classList.contains('collapsed');
        localStorage.setItem('sidebarCollapsed', collapsed);
        
        // 添加动画结束后的回调
        if (!collapsed) {
            // 展开时，延迟显示文字
            setTimeout(() => {
                sidebar.style.overflowX = 'hidden';
            }, 300);
        }
    });
    
    // 为导航项添加tooltip属性
    const navItems = document.querySelectorAll('.nav-item');
    navItems.forEach(item => {
        const text = item.querySelector('.nav-text');
        if (text) {
            item.setAttribute('data-tooltip', text.textContent.trim());
        }
    });
}

// 标签页切换
function initTabs() {
    const navItems = document.querySelectorAll('.nav-item');
    const contents = document.querySelectorAll('.tab-content');
    
    navItems.forEach(item => {
        item.addEventListener('click', () => {
            const targetTab = item.dataset.tab;
            
            // 切换活动导航项
            navItems.forEach(t => t.classList.remove('active'));
            item.classList.add('active');
            
            // 切换内容
            contents.forEach(c => c.classList.remove('active'));
            document.getElementById(`${targetTab}-tab`).classList.add('active');
            
            // 加载对应数据
            if (targetTab === 'demo') {
                loadDemos();
            } else if (targetTab === 'select') {
                loadTypeStats();
            } else if (targetTab === 'review') {
                loadPending();
            } else if (targetTab === 'export') {
                loadExportStats();
                loadPendingExportUtilities();
            } else if (targetTab === 'exported') {
                loadExportedStats();
                loadExportedUtilities();
            } else if (targetTab === 'overview') {
                loadStats();
                loadOverviewStats();
                loadOverviewPendingStats();
            }
        });
    });
}

// 加载统计信息
async function loadStats() {
    try {
        const response = await fetch('/api/stats');
        const stats = await response.json();
        
        // 更新总览页面的统计数据
        const overviewTotal = document.getElementById('overview-total-count');
        const overviewPending = document.getElementById('overview-pending-count');
        const overviewApproved = document.getElementById('overview-approved-count');
        
        if (overviewTotal) overviewTotal.textContent = stats.total_parsed || 0;
        if (overviewPending) overviewPending.textContent = stats.pending_review || 0;
        if (overviewApproved) overviewApproved.textContent = stats.approved || 0;
    } catch (error) {
        console.error('加载统计失败:', error);
    }
}

// 加载总览页面详细统计
async function loadOverviewStats() {
    try {
        const response = await fetch('/api/stats');
        const stats = await response.json();
        
        // 按地图统计
        const mapStatsList = document.getElementById('map-stats-list');
        if (mapStatsList && stats.by_map) {
            const mapEntries = Object.entries(stats.by_map).sort((a, b) => b[1] - a[1]);
            if (mapEntries.length > 0) {
                mapStatsList.innerHTML = mapEntries.map(([map, count]) => `
                    <div class="stat-row">
                        <span class="stat-name">${map.replace('de_', '')}</span>
                        <span class="stat-bar">
                            <span class="stat-bar-fill" style="width: ${(count / mapEntries[0][1]) * 100}%"></span>
                        </span>
                        <span class="stat-count">${count}</span>
                    </div>
                `).join('');
            } else {
                mapStatsList.innerHTML = '<p class="hint">暂无数据</p>';
            }
        }
        
        // 按类型统计
        const typeStatsList = document.getElementById('type-stats-list');
        if (typeStatsList && stats.by_type) {
            const typeNames = {
                'smoke': '烟雾弹',
                'flashbang': '闪光弹',
                'hegrenade': '手雷',
                'incendiary': '燃烧弹',
                'molotov': '燃烧弹'
            };
            const typeEntries = Object.entries(stats.by_type).sort((a, b) => b[1] - a[1]);
            if (typeEntries.length > 0) {
                typeStatsList.innerHTML = typeEntries.map(([type, count]) => `
                    <div class="stat-row">
                        <span class="stat-name">${typeNames[type] || type}</span>
                        <span class="stat-bar">
                            <span class="stat-bar-fill type-${type}" style="width: ${(count / typeEntries[0][1]) * 100}%"></span>
                        </span>
                        <span class="stat-count">${count}</span>
                    </div>
                `).join('');
            } else {
                typeStatsList.innerHTML = '<p class="hint">暂无数据</p>';
            }
        }
        
        // 按状态统计
        const statusStatsList = document.getElementById('status-stats-list');
        if (statusStatsList && stats.by_status) {
            const statusNames = {
                'parsed': '已解析',
                'selected': '已选择',
                'screenshotted': '已截图',
                'approved': '已批准',
                'exported': '已导出',
                'rejected': '已拒绝'
            };
            const statusEntries = Object.entries(stats.by_status)
                .filter(([_, count]) => count > 0)
                .sort((a, b) => b[1] - a[1]);
            if (statusEntries.length > 0) {
                statusStatsList.innerHTML = statusEntries.map(([status, count]) => `
                    <div class="stat-row">
                        <span class="stat-name">${statusNames[status] || status}</span>
                        <span class="stat-bar">
                            <span class="stat-bar-fill status-${status}" style="width: ${(count / statusEntries[0][1]) * 100}%"></span>
                        </span>
                        <span class="stat-count">${count}</span>
                    </div>
                `).join('');
            } else {
                statusStatsList.innerHTML = '<p class="hint">暂无数据</p>';
            }
        }
    } catch (error) {
        console.error('加载总览统计失败:', error);
    }
}

// 加载待截图道具统计
async function loadOverviewPendingStats() {
    const cardsEl = document.getElementById('overview-type-cards');
    if (!cardsEl) return;
    
    cardsEl.innerHTML = '<div class="loading">加载中</div>';
    
    try {
        const response = await fetch('/api/all_pending');
        const data = await response.json();
        
        if (data.success === false || !data.utilities) {
            cardsEl.innerHTML = '<p class="hint">加载失败</p>';
            return;
        }
        
        const allPendingUtilities = data.utilities;
        
        if (allPendingUtilities.length === 0) {
            cardsEl.innerHTML = '<p class="hint">没有待截图的道具</p>';
            return;
        }
        
        // 统计各类型数量
        const typeCounts = {};
        const typeCountsByStatus = { parsed: {}, rejected: {} };
        
        allPendingUtilities.forEach(u => {
            const type = u.type || u.grenade_type || 'unknown';
            const status = u.status || 'parsed';
            
            typeCounts[type] = (typeCounts[type] || 0) + 1;
            
            if (status === 'rejected') {
                typeCountsByStatus.rejected[type] = (typeCountsByStatus.rejected[type] || 0) + 1;
            } else {
                typeCountsByStatus.parsed[type] = (typeCountsByStatus.parsed[type] || 0) + 1;
            }
        });
        
        const rejectedUtilities = allPendingUtilities.filter(u => u.status === 'rejected');
        
        // 生成卡片HTML
        let html = `
            <div class="pending-summary">
                共 ${allPendingUtilities.length} 个待截图道具，已拒绝 ${rejectedUtilities.length} 个
            </div>
        `;
        
        const typeOrder = ['smoke', 'flashbang', 'hegrenade', 'incendiary'];
        html += '<div class="type-cards-grid">';
        
        typeOrder.forEach(type => {
            const total = typeCounts[type] || 0;
            const rejected = typeCountsByStatus.rejected[type] || 0;
            html += `
                <div class="type-card">
                    <div class="count">${total}</div>
                    <div class="label">${TYPE_NAMES[type] || type}</div>
                    <div class="sub-label">已拒绝: ${rejected}</div>
                </div>
            `;
        });
        
        html += '</div>';
        cardsEl.innerHTML = html;
        
    } catch (error) {
        console.error('加载待截图统计失败:', error);
        cardsEl.innerHTML = '<p class="hint">加载失败</p>';
    }
}

// ========== Demo 管理 ==========

async function loadDemos() {
    const listEl = document.getElementById('demo-list');
    listEl.innerHTML = '<div class="loading">加载中</div>';
    
    try {
        const response = await fetch('/api/demos');
        const data = await response.json();
        
        if (data.demos.length === 0) {
            listEl.innerHTML = '<p class="hint">未找到 demo 文件，请将 .dem 文件放入 demos/ 文件夹</p>';
            return;
        }
        
        listEl.innerHTML = data.demos.map(demo => `
            <div class="demo-item">
                <div class="demo-info">
                    <h3>${demo.name}</h3>
                    <p>大小: ${formatFileSize(demo.size)}</p>
                    ${demo.parsed ? '<span class="badge badge-success">已解析</span>' : ''}
                </div>
                <button class="btn btn-primary" onclick="parseDemo('${demo.name}')" ${demo.parsed ? 'disabled' : ''}>
                    ${demo.parsed ? '已解析' : '解析'}
                </button>
            </div>
        `).join('');
    } catch (error) {
        listEl.innerHTML = '<p class="hint error">加载失败: ' + error.message + '</p>';
    }
}

async function parseDemo(demoName) {
    if (!confirm(`确定要解析 ${demoName} 吗？\n\n解析可能需要几分钟时间。`)) {
        return;
    }
    
    const btn = event.target;
    btn.disabled = true;
    btn.textContent = '解析中...';
    
    try {
        const response = await fetch('/api/parse_demo', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ demo_name: demoName })
        });
        
        const result = await response.json();
        
        if (result.success) {
            alert(`${result.message}`);
            loadStats();
            loadTypeStats();
        } else {
            alert(`${result.message}`);
        }
    } catch (error) {
        alert('解析失败: ' + error.message);
    } finally {
        btn.disabled = false;
        btn.textContent = '解析';
    }
}

function formatFileSize(bytes) {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / 1024 / 1024).toFixed(1) + ' MB';
}

// ========== 选择道具 ==========

let allPendingUtilities = [];
let selectedUtilities = new Set();
// 注意：currentFilterDemo 和 currentFilterMap 已在文件顶部全局声明

async function loadTypeStats() {
    const statsEl = document.getElementById('type-stats');
    statsEl.innerHTML = '<div class="loading">加载中</div>';
    
    try {
        const response = await fetch('/api/all_pending');
        const data = await response.json();
        
        // 检查是否有错误
        if (data.success === false || !data.utilities) {
            statsEl.innerHTML = `<p class="hint error">加载失败: ${data.error || '未知错误'}</p>`;
            console.error('加载失败:', data);
            return;
        }
        
        allPendingUtilities = data.utilities;
        
        if (allPendingUtilities.length === 0) {
            statsEl.innerHTML = '<p class="hint">没有待截图的道具。请先解析 demo 文件。</p>';
            return;
        }
        
        // 统计各类型数量（包含所有道具）
        const typeCounts = {};
        const typeCountsByStatus = { parsed: {}, rejected: {} };
        
        allPendingUtilities.forEach(u => {
            const type = u.type || u.grenade_type || 'unknown';
            const status = u.status || 'parsed';
            
            // 总计数
            typeCounts[type] = (typeCounts[type] || 0) + 1;
            
            // 按状态分类统计
            if (status === 'rejected') {
                typeCountsByStatus.rejected[type] = (typeCountsByStatus.rejected[type] || 0) + 1;
            } else {
                typeCountsByStatus.parsed[type] = (typeCountsByStatus.parsed[type] || 0) + 1;
            }
        });
        
        // 计算不同状态的数量
        const rejectedUtilities = allPendingUtilities.filter(u => u.status === 'rejected');
        const notRejectedUtilities = allPendingUtilities.filter(u => u.status !== 'rejected');
        
        // 统计来源demo和地图
        const demoCounts = {};
        const mapCounts = {};
        allPendingUtilities.forEach(u => {
            const demo = u.source_demo || '未知';
            const map = u.map || u.map_name || '未知';
            demoCounts[demo] = (demoCounts[demo] || 0) + 1;
            mapCounts[map] = (mapCounts[map] || 0) + 1;
        });
        
        // 显示道具列表
        let html = '';
        
        // 1. 筛选和操作区域
        html += '<div class="selection-controls">';
        
        // 1.1 筛选器区域
        html += '<div class="select-section">';
        html += '<h4>筛选道具</h4>';
        html += '<div class="select-buttons">';
        
        // 地图筛选下拉框
        if (Object.keys(mapCounts).length > 0) {
            html += '<select id="selection-filter-map" class="filter-select" onchange="filterByMap(this.value)">';
            html += `<option value="all">全部地图 (${allPendingUtilities.length})</option>`;
            html += Object.entries(mapCounts)
                .sort((a, b) => b[1] - a[1])
                .map(([map, count]) => `
                <option value="${map}">${map.replace('de_', '')} (${count})</option>
            `).join('');
            html += '</select>';
        }
        
        // Demo来源筛选下拉框
        if (Object.keys(demoCounts).length > 0) {
            html += '<select id="selection-filter-demo" class="filter-select" onchange="filterByDemo(this.value)">';
            html += `<option value="all">全部来源 (${allPendingUtilities.length})</option>`;
            html += Object.entries(demoCounts)
                .sort((a, b) => b[1] - a[1])
                .map(([demo, count]) => `
                <option value="${demo}">${demo.replace('.dem', '')} (${count})</option>
            `).join('');
            html += '</select>';
        }
        
        // 状态筛选
        html += '<select id="selection-filter-screenshot" class="filter-select" onchange="filterByScreenshotStatus(this.value)">';
        html += `<option value="all">全部状态 (${allPendingUtilities.length})</option>`;
        html += `<option value="no">未拒绝 (${notRejectedUtilities.length})</option>`;
        html += `<option value="yes">已拒绝 (${rejectedUtilities.length})</option>`;
        html += '</select>';
        
        html += '</div>';
        html += '</div>';
        
        // 1.2 道具类型筛选按钮
        html += '<div class="select-section">';
        html += '<h4>按类型筛选</h4>';
        html += '<div class="select-buttons">';
        html += '<button class="btn btn-type active" data-type="all" onclick="filterByType(\'all\')">全部类型</button>';
        html += '<button class="btn btn-type" data-type="smoke" onclick="filterByType(\'smoke\')">烟雾弹</button>';
        html += '<button class="btn btn-type" data-type="flashbang" onclick="filterByType(\'flashbang\')">闪光弹</button>';
        html += '<button class="btn btn-type" data-type="hegrenade" onclick="filterByType(\'hegrenade\')">手雷</button>';
        html += '<button class="btn btn-type" data-type="incendiary" onclick="filterByType(\'incendiary\')">燃烧弹</button>';
        html += '</div>';
        html += '</div>';
        
        // 1.3 已选择数量和保存按钮
        html += '<div class="selection-summary-inline">';
        html += '<div class="summary-info">';
        html += '<span class="label">已选择</span>';
        html += '<span id="selected-count" class="count">0</span>';
        html += '<span class="label">个道具</span>';
        html += '<span class="label"> / 当前显示</span>';
        html += '<span id="visible-count" class="count">0</span>';
        html += '<span class="label">个</span>';
        html += '</div>';
        html += '<button class="btn btn-large btn-primary" onclick="saveSelectedUtilities()">保存选择并准备截图</button>';
        html += '</div>';
        
        html += '</div>'; // 结束 selection-controls
        
        // 2. 道具列表表头
        html += '<div class="utilities-table-header">';
        html += '<div class="header-checkbox-col">';
        html += '<button id="toggle-select-all-btn" class="btn-header-select" onclick="toggleSelectAll()" title="全选/取消全选">☐</button>';
        html += '</div>';
        html += '<div class="header-info-col">类型/队伍</div>';
        html += '<div class="header-detail-col">地图</div>';
        html += '<div class="header-detail-col">玩家</div>';
        html += '<div class="header-detail-col">投掷方式</div>';
        html += '<div class="header-detail-col">来源</div>';
        html += '<div class="header-time-col">解析时间</div>';
        html += '</div>';
        
        // 3. 道具列表
        html += '<div class="utilities-select-list">';
        html += allPendingUtilities.map(u => renderUtilitySelectCard(u)).join('');
        html += '</div>';
        
        statsEl.innerHTML = html;
        
        // 重置选择并更新计数（延迟执行确保DOM已渲染）
        selectedUtilities.clear();
        setTimeout(() => {
            updateSelectedCount();
        }, 100);
        
    } catch (error) {
        console.error('加载失败:', error);
        statsEl.innerHTML = '<p class="hint error">加载失败</p>';
    }
}

function renderUtilitySelectCard(u) {
    const type = u.type || u.grenade_type || 'unknown';
    const map = u.map || u.map_name || 'unknown';
    const player = u.thrower || u.player_name || 'unknown';
    const team = u.team || '未知';
    const throwType = u.throw_type || 'unknown';
    const hash = u.hash;
    const sourceDemo = u.source_demo || '未知';
    const parseTime = u.parse_time || '未知';
    const status = u.status || 'parsed';
    const isRejected = status === 'rejected';
    
    return `
        <div class="utility-select-row ${isRejected ? 'is-rejected' : ''}" data-hash="${hash}" data-status="${status}">
            <div class="utility-checkbox-col">
                <input type="checkbox" id="check-${hash}" class="utility-checkbox" 
                       onchange="toggleUtility('${hash}')" data-type="${type}">
            </div>
            <div class="utility-info-col">
                <div class="utility-badges">
                    <span class="type-badge type-${type}">${TYPE_NAMES[type] || type}</span>
                    <span class="team-badge team-${team}">${team}</span>
                    ${isRejected ? '<span class="rejected-badge">已拒绝</span>' : ''}
                </div>
            </div>
            <div class="utility-detail-col">
                <span class="detail-value">${map}</span>
            </div>
            <div class="utility-detail-col">
                <span class="detail-value">${player}</span>
            </div>
            <div class="utility-detail-col">
                <span class="detail-value">${throwType}</span>
            </div>
            <div class="utility-detail-col">
                <span class="detail-value">${sourceDemo.replace('.dem', '')}</span>
            </div>
            <div class="utility-time-col">
                <span class="detail-value">${parseTime}</span>
            </div>
        </div>
    `;
}

function toggleUtility(hash) {
    if (selectedUtilities.has(hash)) {
        selectedUtilities.delete(hash);
    } else {
        selectedUtilities.add(hash);
    }
    updateSelectedCount();
}

function updateSelectedCount() {
    const countEl = document.getElementById('selected-count');
    const visibleCountEl = document.getElementById('visible-count');
    const toggleBtn = document.getElementById('toggle-select-all-btn');
    
    if (countEl) {
        countEl.textContent = selectedUtilities.size;
    }
    
    // 计算当前可见的道具数量
    const visibleCards = Array.from(document.querySelectorAll('.utility-select-row'))
        .filter(card => card.style.display !== 'none');
    
    if (visibleCountEl) {
        visibleCountEl.textContent = visibleCards.length;
    }
    
    // 更新全选按钮状态
    if (toggleBtn && visibleCards.length > 0) {
        const visibleHashes = visibleCards.map(card => card.dataset.hash);
        const allVisibleSelected = visibleHashes.every(hash => selectedUtilities.has(hash));
        
        if (allVisibleSelected) {
            // 全部选中状态
            toggleBtn.innerHTML = '☑';
            toggleBtn.classList.add('selected');
            toggleBtn.title = '取消全选';
        } else {
            // 未全部选中状态
            toggleBtn.innerHTML = '☐';
            toggleBtn.classList.remove('selected');
            toggleBtn.title = '全选';
        }
    }
}

function toggleSelectAll() {
    // 计算当前可见的道具
    const visibleCards = Array.from(document.querySelectorAll('.utility-select-row'))
        .filter(card => card.style.display !== 'none');
    
    if (visibleCards.length === 0) return;
    
    // 检查当前可见道具的选中状态
    const visibleHashes = visibleCards.map(card => card.dataset.hash);
    const allVisibleSelected = visibleHashes.every(hash => selectedUtilities.has(hash));
    
    if (allVisibleSelected) {
        // 当前全部选中，执行取消全选
        visibleCards.forEach(card => {
            const checkbox = card.querySelector('.utility-checkbox');
            checkbox.checked = false;
            selectedUtilities.delete(card.dataset.hash);
        });
    } else {
        // 当前未全部选中，执行全选
        visibleCards.forEach(card => {
            const checkbox = card.querySelector('.utility-checkbox');
            checkbox.checked = true;
            selectedUtilities.add(card.dataset.hash);
        });
    }
    
    updateSelectedCount();
}

function selectAll() {
    // 只选择当前可见的道具
    document.querySelectorAll('.utility-checkbox').forEach(cb => {
        const card = cb.closest('.utility-select-card');
        // 检查道具是否可见（没有被筛选隐藏）
        if (card && card.style.display !== 'none') {
            cb.checked = true;
            selectedUtilities.add(card.dataset.hash);
        }
    });
    updateSelectedCount();
}

function deselectAll() {
    // 只取消选择当前可见的道具
    document.querySelectorAll('.utility-checkbox').forEach(cb => {
        const card = cb.closest('.utility-select-card');
        // 检查道具是否可见
        if (card && card.style.display !== 'none') {
            cb.checked = false;
            selectedUtilities.delete(card.dataset.hash);
        }
    });
    updateSelectedCount();
}

function selectByType(type) {
    // 只选择当前可见且类型匹配的道具
    document.querySelectorAll('.utility-checkbox').forEach(cb => {
        const card = cb.closest('.utility-select-card');
        // 检查道具是否可见且类型匹配
        if (card && card.style.display !== 'none' && cb.dataset.type === type) {
            cb.checked = true;
            selectedUtilities.add(card.dataset.hash);
        }
    });
    updateSelectedCount();
}

function filterByMap(map) {
    currentFilterMap = map;
    applySelectionFilters();
}

function filterByDemo(demo) {
    currentFilterDemo = demo;
    applySelectionFilters();
}

function filterByScreenshotStatus(status) {
    currentFilterScreenshot = status;
    applySelectionFilters();
}

function filterByType(type) {
    currentFilterType = type;
    
    // 更新按钮状态
    document.querySelectorAll('.btn-type').forEach(btn => {
        if (btn.dataset.type === type) {
            btn.classList.add('active');
        } else {
            btn.classList.remove('active');
        }
    });
    
    applySelectionFilters();
}

function applySelectionFilters() {
    // 同时应用地图、demo、状态和类型筛选
    document.querySelectorAll('.utility-select-row').forEach(card => {
        const hash = card.dataset.hash;
        const utility = allPendingUtilities.find(u => u.hash === hash);
        
        if (!utility) {
            card.style.display = 'none';
            return;
        }
        
        const utilMap = utility.map || utility.map_name || '未知';
        const utilDemo = utility.source_demo || '未知';
        const utilType = utility.type || utility.grenade_type || 'unknown';
        const utilStatus = utility.status || 'parsed';
        const isRejected = utilStatus === 'rejected';
        
        // 检查是否匹配四个筛选条件
        const mapMatch = currentFilterMap === 'all' || utilMap === currentFilterMap;
        const demoMatch = currentFilterDemo === 'all' || utilDemo === currentFilterDemo;
        const statusMatch = currentFilterScreenshot === 'all' || 
                           (currentFilterScreenshot === 'yes' && isRejected) ||
                           (currentFilterScreenshot === 'no' && !isRejected);
        const typeMatch = currentFilterType === 'all' || utilType === currentFilterType;
        
        if (mapMatch && demoMatch && statusMatch && typeMatch) {
            card.style.display = '';
        } else {
            card.style.display = 'none';
        }
    });
    
    // 更新计数和按钮状态
    updateSelectedCount();
}

function selectByTypeQuick(type) {
    // 只选择当前可见且类型匹配的道具（不改变筛选器）
    document.querySelectorAll('.utility-checkbox').forEach(cb => {
        const card = cb.closest('.utility-select-card');
        // 检查道具是否可见且类型匹配
        if (card && card.style.display !== 'none' && cb.dataset.type === type) {
            cb.checked = true;
            selectedUtilities.add(card.dataset.hash);
        }
    });
    updateSelectedCount();
}

async function saveSelectedUtilities() {
    if (selectedUtilities.size === 0) {
        alert('请至少选择一个道具');
        return;
    }
    
    if (!confirm(`确定要保存选择的 ${selectedUtilities.size} 个道具吗？\n\n保存后可以运行截图工具进行截图。`)) {
        return;
    }
    
    // 获取选中的道具数据
    const selected = allPendingUtilities.filter(u => selectedUtilities.has(u.hash));
    
    try {
        // 修改为新的API端点
        const response = await fetch('/api/utilities/select', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                utilities: selected
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            alert(`${result.message}\n\n下一步：\n1. 确保后端服务器运行中（http://localhost:5000）\n2. 启动 CS2 游戏，进入对应地图\n3. 开启控制台输入：sv_cheats 1\n4. 运行截图工具：python client/screenshot.py`);
            
            // 刷新页面数据
            loadStats();
            loadTypeStats();
        } else {
            alert(`${result.message}`);
        }
    } catch (error) {
        alert('保存失败: ' + error.message);
    }
}

async function selectType(type) {
    const btn = event.target;
    btn.disabled = true;
    const originalText = btn.textContent;
    btn.textContent = '处理中...';
    
    try {
        const response = await fetch('/api/select_utilities', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ type: type })
        });
        
        const result = await response.json();
        
        const resultEl = document.getElementById('select-result');
        if (resultEl) {
            resultEl.className = 'result-message show ' + (result.success ? 'success' : 'error');
            resultEl.textContent = result.message;
            
            setTimeout(() => {
                resultEl.classList.remove('show');
            }, 5000);
        }
    } catch (error) {
        alert('选择失败: ' + error.message);
    } finally {
        btn.disabled = false;
        btn.textContent = originalText;
    }
}

// ========== 审核道具 ==========

async function loadPending() {
    const gridEl = document.getElementById('utilities-grid');
    gridEl.innerHTML = '<div class="loading">加载中</div>';
    
    try {
        const response = await fetch('/api/pending');
        const data = await response.json();
        allUtilities = data.utilities;
        
        // 填充 demo 筛选下拉框
        populateDemoFilter();
        
        applyFilters();
    } catch (error) {
        gridEl.innerHTML = '<p class="hint error">加载失败</p>';
    }
}

function populateDemoFilter() {
    const mapFilter = document.getElementById('filter-map');
    const demoFilter = document.getElementById('filter-demo');
    if (!demoFilter) return;
    
    // 只统计有截图的道具（待审核的）
    const utilitiesWithScreenshots = allUtilities.filter(u => u.screenshot_filename_base && u.screenshot_filename_base !== '');
    
    // 统计有截图的道具按地图分组
    const mapCounts = {};
    utilitiesWithScreenshots.forEach(u => {
        const map = u.map || u.map_name || '未知';
        mapCounts[map] = (mapCounts[map] || 0) + 1;
    });
    
    // 统计有截图的道具按 demo 分组
    const demoCounts = {};
    utilitiesWithScreenshots.forEach(u => {
        const demo = u.source_demo || '未知';
        demoCounts[demo] = (demoCounts[demo] || 0) + 1;
    });
    
    // 生成地图选项
    if (mapFilter) {
        const mapOptions = ['<option value="">全部地图</option>'];
        Object.entries(mapCounts)
            .sort((a, b) => b[1] - a[1]) // 按数量排序
            .forEach(([map, count]) => {
                mapOptions.push(`<option value="${map}">${map.replace('de_', '')} (${count})</option>`);
            });
        mapFilter.innerHTML = mapOptions.join('');
    }
    
    // 生成demo选项
    const demoOptions = ['<option value="">全部来源</option>'];
    Object.entries(demoCounts)
        .sort((a, b) => b[1] - a[1]) // 按数量排序
        .forEach(([demo, count]) => {
            demoOptions.push(`<option value="${demo}">${demo.replace('.dem', '')} (${count})</option>`);
        });
    demoFilter.innerHTML = demoOptions.join('');
}

function applyFilters() {
    const mapFilter = document.getElementById('filter-map')?.value || '';
    const demoFilter = document.getElementById('filter-demo')?.value || '';
    const typeFilter = document.getElementById('filter-type')?.value || '';
    const teamFilter = document.getElementById('filter-team')?.value || '';
    
    filteredUtilities = allUtilities.filter(u => {
        const map = u.map || u.map_name || '';
        const demo = u.source_demo || '';
        const type = u.type || u.grenade_type || '';
        const team = u.team || '';
        
        if (mapFilter && map !== mapFilter) return false;
        if (demoFilter && demo !== demoFilter) return false;
        if (typeFilter && type !== typeFilter) return false;
        if (teamFilter && team !== teamFilter) return false;
        return true;
    });
    
    renderUtilities();
}

function renderUtilities() {
    const gridEl = document.getElementById('utilities-grid');
    const visibleCountEl = document.getElementById('visible-review-count');
    const totalCountEl = document.getElementById('total-review-count');
    
    // 只显示有截图的道具（检查 screenshot_filename_base 字段）
    const utilitiesWithScreenshots = filteredUtilities.filter(u => {
        return u.screenshot_filename_base && u.screenshot_filename_base !== '';
    });
    
    // 按地图和hash排序
    utilitiesWithScreenshots.sort((a, b) => {
        const baseA = a.screenshot_filename_base || '';
        const baseB = b.screenshot_filename_base || '';
        return baseA.localeCompare(baseB);
    });
    
    // 更新统计信息
    if (visibleCountEl) visibleCountEl.textContent = utilitiesWithScreenshots.length;
    if (totalCountEl) {
        const allWithScreenshots = allUtilities.filter(u => u.screenshot_filename_base && u.screenshot_filename_base !== '');
        totalCountEl.textContent = allWithScreenshots.length;
    }
    
    if (utilitiesWithScreenshots.length === 0) {
        // 检查是否有道具但被筛选掉了
        const allWithScreenshots = allUtilities.filter(u => u.screenshot_filename_base && u.screenshot_filename_base !== '');
        
        if (allWithScreenshots.length > 0) {
            // 有道具但都被筛选掉了
            gridEl.innerHTML = `
                <div class="info-box" style="text-align: center; padding: 40px;">
                    <h3>没有符合筛选条件的道具</h3>
                    <p style="margin: 20px 0;">请调整筛选条件或点击"全部来源/类型/队伍"</p>
                </div>
            `;
        } else {
            // 真的没有已截图的道具
            gridEl.innerHTML = `
                <div class="info-box" style="text-align: center; padding: 40px;">
                    <h3>还没有已截图的道具</h3>
                    <p style="margin: 20px 0;">共有 ${filteredUtilities.length} 个道具待截图</p>
                    <ol style="text-align: left; margin: 20px auto; max-width: 600px;">
                        <li>前往"选择道具"标签页，勾选需要截图的道具</li>
                        <li>点击"保存选择并准备截图"按钮</li>
                        <li>启动 CS2 游戏，进入对应地图</li>
                        <li>运行截图工具：<code style="background: #0f3460; padding: 2px 6px; border-radius: 3px;">python screenshot.py</code></li>
                        <li>截图完成后，运行：<code style="background: #0f3460; padding: 2px 6px; border-radius: 3px;">python create_screenshot_index.py</code></li>
                        <li>刷新此页面即可看到截图并进行审核</li>
                    </ol>
                </div>
            `;
        }
        return;
    }
    
    gridEl.innerHTML = utilitiesWithScreenshots.map(u => renderUtilityCard(u)).join('');
}

function renderUtilityCard(u) {
    const type = u.type || u.grenade_type || 'unknown';
    const map = u.map || u.map_name || 'unknown';
    const player = u.thrower || u.player_name || 'unknown';
    const screenshotBase = u.screenshot_filename_base || `${map}_unknown_${screenshotId}`;
    const team = u.team || 'Unknown';
    const throwType = u.throw_type || 'unknown';
    const flightTime = u.flight_time || 0;
    
    
    
    // 生成TP指令
    const pos = u.throw_position || u.throw_position_corrected || {};
    const angles = u.throw_angles || {};
    const tpCommand = `setpos ${pos.x?.toFixed(2) || 0} ${pos.y?.toFixed(2) || 0} ${pos.z?.toFixed(2) || 0}; setang ${angles.pitch?.toFixed(2) || 0} ${angles.yaw?.toFixed(2) || 0} 0`;
    
    return `
        <div class="utility-card" data-hash="${u.hash}">
            <button class="btn-card-delete" onclick="deleteUtilityPermanently('${u.hash}')" title="永久删除">×</button>
            
            <div class="tp-command-box">
                <label>🎮 TP到投掷位置（复制后在游戏控制台粘贴）</label>
                <div class="command-input-wrapper">
                    <input type="text" class="tp-command-input" value="${tpCommand}" readonly onclick="this.select()">
                    <button class="btn-copy" onclick="copyToClipboard('${tpCommand.replace(/'/g, "\\'")}', this)">复制</button>
                </div>
            </div>
            
            <div class="screenshots">
                <img src="/screenshots/${screenshotBase}_position.jpg" 
                     alt="站位" onclick="showImage(this.src)" 
                     onerror="this.style.display='none'">
                <img src="/screenshots/${screenshotBase}_crosshair.jpg" 
                     alt="准星" onclick="showImage(this.src)" 
                     onerror="this.style.display='none'">
                <img src="/screenshots/${screenshotBase}_landing.jpg" 
                     alt="落点" onclick="showImage(this.src)" 
                     onerror="this.style.display='none'">
            </div>
            
            <div class="utility-info">
                <div class="form-group">
                    <label>道具名称 *</label>
                    <input type="text" class="util-name" placeholder="如：A小烟、中门闪" value="${u.display_name || ''}">
                </div>
                
                <div class="form-group">
                    <label>类型</label>
                    <select class="util-type">
                        <option value="smoke" ${type === 'smoke' ? 'selected' : ''}>烟雾弹</option>
                        <option value="flashbang" ${type === 'flashbang' ? 'selected' : ''}>闪光弹</option>
                        <option value="hegrenade" ${type === 'hegrenade' ? 'selected' : ''}>手雷</option>
                        <option value="incendiary" ${type === 'incendiary' ? 'selected' : ''}>燃烧弹</option>
                    </select>
                </div>
                
                <div class="form-group">
                    <label>队伍</label>
                    <select class="util-team">
                        <option value="T" ${team === 'T' ? 'selected' : ''}>T (恐怖分子)</option>
                        <option value="CT" ${team === 'CT' ? 'selected' : ''}>CT (反恐精英)</option>
                        <option value="Unknown" ${team === 'Unknown' ? 'selected' : ''}>未知</option>
                    </select>
                </div>
                
                <div class="form-group">
                    <label>投掷方式</label>
                    <input type="text" class="util-throw-type" placeholder="如：跳投、站投、蹲投、走投等" value="${throwType}">
                </div>
                
                <div class="info-row" style="padding: 8px; background: rgba(255,255,255,0.05); border-radius: 4px;">
                    <span class="label">飞行时间</span>
                    <span class="value">${flightTime.toFixed(1)} 秒</span>
                </div>
                
                <div class="form-group">
                    <label>备注信息</label>
                    <textarea class="util-notes" placeholder="投掷技巧、注意事项等" rows="2">${u.notes || ''}</textarea>
                </div>
                
                <div class="info-row" style="margin-top: 10px; padding: 8px; background: rgba(255,255,255,0.05); border-radius: 4px;">
                    <span class="label">玩家</span>
                    <span class="value">${player}</span>
                </div>
                
                <div class="actions">
                    <button class="btn-approve" onclick="approveUtility('${u.hash}')">批准</button>
                    <button class="btn-reject" onclick="rejectUtility('${u.hash}')">拒绝</button>
                </div>
            </div>
        </div>
    `;
}

function renderUtilityCardNoScreenshot(u) {
    const type = u.type || u.grenade_type || 'unknown';
    const map = u.map || u.map_name || 'unknown';
    const player = u.thrower || u.player_name || 'unknown';
    const team = u.team || '未知';
    const throwType = u.throw_type || 'unknown';
    const sourceDemo = u.source_demo || '未知';
    
    return `
        <div class="utility-card" data-hash="${u.hash}" style="opacity: 0.7;">
            <div class="utility-info">
                <div class="info-row">
                    <span class="label">地图</span>
                    <span class="value">${map}</span>
                </div>
                <div class="info-row">
                    <span class="label">类型</span>
                    <span class="value">${TYPE_NAMES[type] || type}</span>
                </div>
                <div class="info-row">
                    <span class="label">队伍</span>
                    <span class="value">${team}</span>
                </div>
                <div class="info-row">
                    <span class="label">玩家</span>
                    <span class="value">${player}</span>
                </div>
                <div class="info-row">
                    <span class="label">投掷方式</span>
                    <span class="value">${throwType}</span>
                </div>
                <div class="info-row">
                    <span class="label">来源Demo</span>
                    <span class="value" style="color: #667eea;">${sourceDemo}</span>
                </div>
                
                <div style="margin-top: 15px; padding: 10px; background: #0f3460; border-radius: 5px; text-align: center;">
                    <small style="color: #888;">等待截图</small>
                </div>
                
                <div class="actions">
                    <button class="btn-delete" onclick="deletePending('${u.hash}')">删除</button>
                </div>
            </div>
        </div>
    `;
}

function getScreenshotHTML(map, screenshotId, viewType) {
    // 使用服务器的截图路由：/screenshots/文件名
    const filename = `${map}_unknown_${screenshotId}_${viewType}.jpg`;
    const path = `/screenshots/${filename}`;
    
    const labels = {
        'position': '站位',
        'crosshair': '准星', 
        'landing': '落点'
    };
    
    return `<div class="screenshot-wrapper">
                <img src="${path}" alt="${labels[viewType]}" onclick="showImage('${path}')" 
                     onerror="this.parentElement.style.display='none'">
                <div class="screenshot-label">${labels[viewType]}</div>
            </div>`;
}

function showImage(src) {
    event.stopPropagation();
    document.getElementById('modal-image').src = src;
    document.getElementById('image-modal').classList.add('active');
}

function closeModal() {
    document.getElementById('image-modal').classList.remove('active');
}

async function approveUtility(hash) {
    // 限定在审核页面的道具网格中查找
    const grid = document.getElementById('utilities-grid');
    if (!grid) {
        alert('错误：找不到审核页面');
        return;
    }
    
    const card = grid.querySelector(`[data-hash="${hash}"]`);
    
    if (!card) {
        alert('错误：找不到道具卡片元素');
        console.error('找不到 data-hash:', hash);
        return;
    }
    
    const nameInput = card.querySelector('.util-name');
    
    if (!nameInput) {
        alert('错误：找不到道具名称输入框\n\n请刷新页面后重试（Ctrl+Shift+R 强制刷新）');
        console.error('找不到 .util-name 元素，卡片内容:', card.innerHTML.substring(0, 500));
        return;
    }
    
    const name = nameInput.value.trim();
    
    // 验证必填字段
    if (!name) {
        alert('请填写道具名称');
        nameInput.focus();
        return;
    }
    
    // 收集所有表单数据
    const utilityInfo = {
        display_name: name,
        type: card.querySelector('.util-type').value,
        team: card.querySelector('.util-team').value,
        throw_type: card.querySelector('.util-throw-type').value.trim(),
        notes: card.querySelector('.util-notes').value.trim()
    };
    
    // 保存当前的筛选器状态
    const currentMap = document.getElementById('filter-map')?.value || '';
    const currentDemo = document.getElementById('filter-demo')?.value || '';
    const currentType = document.getElementById('filter-type')?.value || '';
    const currentTeam = document.getElementById('filter-team')?.value || '';
    
    try {
        const response = await fetch('/api/approve', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                hash: hash,
                info: utilityInfo
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            card.style.opacity = '0';
            setTimeout(() => {
                loadPending().then(() => {
                    // 重新应用筛选器
                    if (currentMap) document.getElementById('filter-map').value = currentMap;
                    if (currentDemo) document.getElementById('filter-demo').value = currentDemo;
                    if (currentType) document.getElementById('filter-type').value = currentType;
                    if (currentTeam) document.getElementById('filter-team').value = currentTeam;
                    
                    // 重新应用筛选
                    applyFilters();
                });
                loadStats();
                loadExportStats();
            }, 300);
        } else {
            alert('' + result.message);
        }
    } catch (error) {
        alert('操作失败: ' + error.message);
    }
}

async function rejectUtility(hash) {
    // 限定在审核页面的道具网格中查找
    const grid = document.getElementById('utilities-grid');
    if (!grid) {
        alert('错误：找不到审核页面');
        return;
    }
    
    const card = grid.querySelector(`[data-hash="${hash}"]`);
    
    if (!card) {
        alert('错误：找不到道具卡片元素');
        console.error('找不到 data-hash:', hash);
        return;
    }
    
    // 收集表单数据（在确认前）
    const nameInput = card.querySelector('.util-name');
    const typeSelect = card.querySelector('.util-type');
    const teamSelect = card.querySelector('.util-team');
    const throwTypeInput = card.querySelector('.util-throw-type');
    const notesTextarea = card.querySelector('.util-notes');
    
    if (!nameInput) {
        alert('错误：找不到道具名称输入框\n\n请刷新页面后重试（Ctrl+Shift+R 强制刷新）');
        console.error('找不到 .util-name 元素');
        return;
    }
    
    // 收集所有表单数据
    const utilityInfo = {
        display_name: nameInput.value.trim(),
        type: typeSelect ? typeSelect.value : '',
        team: teamSelect ? teamSelect.value : '',
        throw_type: throwTypeInput ? throwTypeInput.value.trim() : '',
        notes: notesTextarea ? notesTextarea.value.trim() : ''
    };
    
    console.log('[拒绝道具] 收集到的信息:', utilityInfo);
    
    if (!confirm('确定要拒绝这个道具吗？\n\n拒绝后：\n- 道具状态变为"已拒绝"\n- 截图文件将被删除\n- 不会再出现在选择列表中\n- 数据保留在数据库中\n- 你填写的名称和备注也会被保存')) {
        return;
    }
    
    // 保存当前的筛选器状态
    const currentMap = document.getElementById('filter-map')?.value || '';
    const currentDemo = document.getElementById('filter-demo')?.value || '';
    const currentType = document.getElementById('filter-type')?.value || '';
    const currentTeam = document.getElementById('filter-team')?.value || '';
    
    try {
        const response = await fetch('/api/reject', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                hash: hash,
                info: utilityInfo
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            const card = document.querySelector(`[data-hash="${hash}"]`);
            if (card) {
                card.style.opacity = '0';
            }
            setTimeout(() => {
                loadPending().then(() => {
                    // 重新应用筛选器
                    if (currentMap) document.getElementById('filter-map').value = currentMap;
                    if (currentDemo) document.getElementById('filter-demo').value = currentDemo;
                    if (currentType) document.getElementById('filter-type').value = currentType;
                    if (currentTeam) document.getElementById('filter-team').value = currentTeam;
                    
                    // 重新应用筛选
                    applyFilters();
                });
                loadStats();
            }, 300);
            alert('' + result.message);
        } else {
            alert('' + result.message);
        }
    } catch (error) {
        alert('操作失败: ' + error.message);
    }
}

async function deleteUtilityPermanently(hash) {
    if (!confirm('确定要永久删除这个道具吗？\n\n此操作将：\n- 永久删除道具数据\n- 删除所有截图文件\n- 无法恢复\n\n建议：如果只是暂时不需要，请使用"拒绝"按钮')) {
        return;
    }
    
    // 保存当前的筛选器状态
    const currentMap = document.getElementById('filter-map')?.value || '';
    const currentDemo = document.getElementById('filter-demo')?.value || '';
    const currentType = document.getElementById('filter-type')?.value || '';
    const currentTeam = document.getElementById('filter-team')?.value || '';
    
    try {
        const response = await fetch('/api/delete_pending', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ hash: hash })
        });
        
        const result = await response.json();
        
        if (result.success) {
            const grid = document.getElementById('utilities-grid');
            if (grid) {
                const card = grid.querySelector(`[data-hash="${hash}"]`);
                if (card) {
                    card.style.opacity = '0';
                }
            }
            setTimeout(() => {
                loadPending().then(() => {
                    // 重新应用筛选器
                    if (currentMap) document.getElementById('filter-map').value = currentMap;
                    if (currentDemo) document.getElementById('filter-demo').value = currentDemo;
                    if (currentType) document.getElementById('filter-type').value = currentType;
                    if (currentTeam) document.getElementById('filter-team').value = currentTeam;
                    
                    // 重新应用筛选
                    applyFilters();
                });
                loadStats();
            }, 300);
            alert('' + result.message);
        } else {
            alert('' + result.message);
        }
    } catch (error) {
        alert('操作失败: ' + error.message);
    }
}

async function deletePending(hash) {
    // 这个函数现在被 deleteUtilityPermanently 替代
    return deleteUtilityPermanently(hash);
}

// ========== 导出发布 ==========

async function loadExportStats() {
    const countEl = document.getElementById('pending-export-count');
    
    if (!countEl) return;
    
    try {
        const response = await fetch('/api/export/approved');
        const data = await response.json();
        
        countEl.textContent = data.utilities ? data.utilities.length : 0;
    } catch (error) {
        console.error('加载导出统计失败:', error);
    }
}

// 加载已导出道具统计
async function loadExportedStats() {
    const countEl = document.getElementById('exported-count');
    
    if (!countEl) return;
    
    try {
        const response = await fetch('/api/export/exported');
        const data = await response.json();
        
        countEl.textContent = data.utilities ? data.utilities.length : 0;
    } catch (error) {
        console.error('加载已导出统计失败:', error);
    }
}

// 加载待导出道具（已批准但未导出）
async function loadPendingExportUtilities() {
    const listEl = document.getElementById('pending-export-list');
    const countEl = document.getElementById('pending-export-count');
    
    if (!listEl || !countEl) return;
    
    listEl.innerHTML = '<div class="loading">加载中...</div>';
    
    try {
        const response = await fetch('/api/export/approved');
        const data = await response.json();
        
        countEl.textContent = data.utilities.length;
        
        if (data.utilities.length === 0) {
            listEl.innerHTML = '<p class="hint">还没有待导出的道具</p>';
            return;
        }
        
        listEl.innerHTML = `
            <h3 style="margin-bottom: 15px;">待导出道具列表</h3>
            <div class="approved-items">
                ${data.utilities.map(u => {
                    const type = u.type || u.grenade_type || 'unknown';
                    const name = u.display_name || '未命名';
                    return `
                        <div class="approved-item">
                            <div class="approved-info">
                                <strong>${name}</strong>
                                <span style="color: #888; font-size: 12px;">
                                    ${TYPE_NAMES[type] || type} · ${u.team || '未知'} · ${u.thrower || '未知'}
                                </span>
                            </div>
                            <button class="btn btn-delete" onclick="deleteApproved('${u.hash}')">
                                删除
                            </button>
                        </div>
                    `;
                }).join('')}
            </div>
        `;
    } catch (error) {
        console.error('加载待导出道具失败:', error);
        listEl.innerHTML = '<p class="hint error">加载失败</p>';
    }
}

// 加载已导出道具
// 全局变量存储已导出道具数据
let allExportedUtilities = [];

async function loadExportedUtilities() {
    const gridEl = document.getElementById('exported-grid');
    const countEl = document.getElementById('exported-count');
    
    if (!gridEl || !countEl) return;
    
    gridEl.innerHTML = '<div class="loading">加载中...</div>';
    
    try {
        const response = await fetch('/api/export/exported');
        const data = await response.json();
        
        // 存储全部数据供搜索使用
        allExportedUtilities = data.utilities;
        
        countEl.textContent = data.utilities.length;
        
        if (data.utilities.length === 0) {
            gridEl.innerHTML = '<p class="hint">还没有已导出的道具</p>';
            return;
        }
        
        // 清空搜索框
        const searchInput = document.getElementById('exported-search-input');
        if (searchInput) {
            searchInput.value = '';
        }
        
        // 渲染全部道具
        renderExportedUtilities(allExportedUtilities);
    } catch (error) {
        console.error('加载已导出道具失败:', error);
        gridEl.innerHTML = '<p class="hint error">加载失败</p>';
    }
}

// 渲染已导出道具列表
function renderExportedUtilities(utilities) {
    const gridEl = document.getElementById('exported-grid');
    
    if (!gridEl) return;
    
    if (utilities.length === 0) {
        gridEl.innerHTML = '<p class="hint">没有符合条件的道具</p>';
        return;
    }
    
    gridEl.innerHTML = utilities.map(u => renderExportedUtilityCard(u)).join('');
}

// 搜索过滤已导出道具
function filterExportedUtilities() {
    const searchInput = document.getElementById('exported-search-input');
    if (!searchInput) return;
    
    const searchTerm = searchInput.value.toLowerCase().trim();
    
    if (!searchTerm) {
        // 如果搜索框为空，显示全部
        renderExportedUtilities(allExportedUtilities);
        return;
    }
    
    // 过滤道具
    const filtered = allExportedUtilities.filter(u => {
        const map = (u.map || u.map_name || '').toLowerCase();
        const type = (u.type || u.grenade_type || '').toLowerCase();
        const hash = (u.hash || '').toLowerCase();
        const name = (u.display_name || '').toLowerCase();
        const screenshotBase = (u.screenshot_filename_base || '').toLowerCase();
        
        // 构建完整的道具ID（如：de_dust2_smoke_7d0b3c27）
        const utilityId = `${map}_${type}_${hash.substring(0, 8)}`.toLowerCase();
        
        // 搜索条件：匹配道具ID、screenshot_filename_base、名称、地图、类型或hash
        return utilityId.includes(searchTerm) || 
               screenshotBase.includes(searchTerm) ||
               name.includes(searchTerm) ||
               map.includes(searchTerm) ||
               type.includes(searchTerm) ||
               hash.includes(searchTerm);
    });
    
    renderExportedUtilities(filtered);
}

// 渲染已导出道具卡片
function renderExportedUtilityCard(u) {
    const type = u.type || u.grenade_type || 'unknown';
    const map = u.map || u.map_name || 'unknown';
    const screenshotBase = u.screenshot_filename_base || `${map}_unknown_${screenshotId}`;
    const name = u.display_name || '未命名';
    const hash = (u.hash || '').substring(0, 8);
    
    
    // 构建道具ID（如：de_dust2_smoke_7d0b3c27）
    const utilityId = `${map}_${type}_${hash}`;
    
    return `
        <div class="utility-card" data-utility-id="${utilityId}">
            <div class="screenshots">
                <img src="/screenshots/${screenshotBase}_position.jpg" 
                     alt="站位" onclick="showImage(this.src)" 
                     onerror="this.style.display='none'">
                <img src="/screenshots/${screenshotBase}_crosshair.jpg" 
                     alt="准星" onclick="showImage(this.src)" 
                     onerror="this.style.display='none'">
                <img src="/screenshots/${screenshotBase}_landing.jpg" 
                     alt="落点" onclick="showImage(this.src)" 
                     onerror="this.style.display='none'">
            </div>
            
            <div class="utility-info">
                <div class="info-row">
                    <span class="label">道具ID</span>
                    <span class="value" style="font-family: monospace; font-size: 12px; color: #667eea;">${utilityId}</span>
                </div>
                <div class="info-row">
                    <span class="label">名称</span>
                    <span class="value">${name}</span>
                </div>
                <div class="info-row">
                    <span class="label">类型</span>
                    <span class="value">${TYPE_NAMES[type] || type}</span>
                </div>
                <div class="info-row">
                    <span class="label">队伍</span>
                    <span class="value">${u.team || '未知'}</span>
                </div>
                <div class="info-row">
                    <span class="label">投掷方式</span>
                    <span class="value">${u.throw_type || '未知'}</span>
                </div>
                ${u.notes ? `
                <div class="info-row">
                    <span class="label">备注</span>
                    <span class="value">${u.notes}</span>
                </div>
                ` : ''}
                
                <div class="actions" style="margin-top: 15px;">
                    <button class="btn" onclick="editExported('${u.hash}')">编辑</button>
                    <button class="btn-delete" onclick="deleteExportedUtility('${u.hash}')">删除</button>
                </div>
            </div>
        </div>
    `;
}

async function deleteApproved(hash) {
    if (!confirm('确定要删除这个道具吗？\n\n删除后会移回待审核列表。')) {
        return;
    }
    
    try {
        const response = await fetch('/api/delete_approved', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ hash: hash })
        });
        
        const result = await response.json();
        
        if (result.success) {
            alert('' + result.message);
            loadExportStats();
            loadStats();
        } else {
            alert('' + result.message);
        }
    } catch (error) {
        alert('操作失败: ' + error.message);
    }
}

// 删除已导出道具（永久删除）
async function deleteExportedUtility(hash) {
    if (!confirm('确定要永久删除此道具吗？\n\n此操作将：\n1. 从数据库中永久删除道具数据\n2. 删除所有截图文件\n3. 客户端需要重新导出和部署才能生效\n\n此操作不可撤销！')) {
        return;
    }
    
    try {
        const response = await fetch('/api/delete_exported', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ hash: hash })
        });
        
        const result = await response.json();
        
        if (result.success) {
            alert('道具已永久删除');
            loadExportedUtilities();
            loadExportStats();
            loadStats();
        } else {
            alert('删除失败：' + result.message);
        }
    } catch (error) {
        alert('删除失败: ' + error.message);
    }
}

// 编辑已导出道具
let currentEditingUtility = null;

function editExported(hash) {
    // 从已导出列表中找到道具
    fetch('/api/exported')
        .then(r => r.json())
        .then(data => {
            const utility = data.utilities.find(u => u.hash === hash);
            if (!utility) {
                alert('道具未找到');
                return;
            }
            
            currentEditingUtility = utility;
            
            // 切换到编辑页面
            switchToEditUtilityTab(utility);
        })
        .catch(error => {
            console.error('加载道具失败:', error);
            alert('加载失败');
        });
}

// 切换到编辑道具页面并填充数据
function switchToEditUtilityTab(utility) {
    // 切换标签页
    document.querySelectorAll('.tab-content').forEach(tab => tab.classList.remove('active'));
    document.querySelectorAll('.nav-item').forEach(nav => nav.classList.remove('active'));
    document.getElementById('edit-utility-tab').classList.add('active');
    
    // 填充基本信息
    document.getElementById('edit-util-hash').value = utility.hash;
    document.getElementById('edit-util-name').value = utility.display_name || '';
    document.getElementById('edit-util-map').value = utility.map || '';
    document.getElementById('edit-util-type').value = utility.type || 'smoke';
    document.getElementById('edit-util-team').value = utility.team || 'Unknown';
    document.getElementById('edit-util-throw-type').value = utility.throw_type || '';
    document.getElementById('edit-util-notes').value = utility.notes || '';
    
    // 填充标签（数组转换为逗号分隔的字符串）
    const tags = utility.tags || [];
    document.getElementById('edit-util-tags').value = Array.isArray(tags) ? tags.join(', ') : '';
    
    // 填充坐标信息
    if (utility.throw_position) {
        document.getElementById('edit-util-throw-x').value = utility.throw_position.x || 0;
        document.getElementById('edit-util-throw-y').value = utility.throw_position.y || 0;
        document.getElementById('edit-util-throw-z').value = utility.throw_position.z || 0;
    }
    
    if (utility.throw_angles) {
        document.getElementById('edit-util-pitch').value = utility.throw_angles.pitch || 0;
        document.getElementById('edit-util-yaw').value = utility.throw_angles.yaw || 0;
    }
    
    // 加载现有图片
    const screenshotBase = utility.screenshot_filename_base;
    if (screenshotBase) {
        loadExistingImage('edit-preview-position', `/screenshots/${screenshotBase}_position.jpg`, '站位图');
        loadExistingImage('edit-preview-crosshair', `/screenshots/${screenshotBase}_crosshair.jpg`, '准星图');
        loadExistingImage('edit-preview-landing', `/screenshots/${screenshotBase}_landing.jpg`, '落点图');
    }
    
    // 滚动到顶部
    window.scrollTo(0, 0);
}

// 加载现有图片到预览框
function loadExistingImage(previewId, imageUrl, label) {
    const preview = document.getElementById(previewId);
    preview.innerHTML = `
        <img src="${imageUrl}" 
             style="width: 100%; height: 100%; object-fit: cover;" 
             onerror="this.parentElement.innerHTML='<span style=\\'font-size: 48px; color: #667eea;\\'>📷</span><p style=\\'margin-top: 10px; color: #666;\\'>${label}</p>'">
        <div style="position: absolute; bottom: 10px; left: 0; right: 0; text-align: center; background: rgba(0,0,0,0.6); color: white; padding: 5px; font-size: 12px;">
            点击替换
        </div>
    `;
}

// 预览编辑时的新图片
function previewEditImage(input, previewId) {
    if (input.files && input.files[0]) {
        const reader = new FileReader();
        reader.onload = function(e) {
            const preview = document.getElementById(previewId);
            preview.innerHTML = `
                <img src="${e.target.result}" style="width: 100%; height: 100%; object-fit: cover;">
                <div style="position: absolute; bottom: 10px; left: 0; right: 0; text-align: center; background: rgba(0,0,0,0.6); color: white; padding: 5px; font-size: 12px;">
                    新图片
                </div>
            `;
        };
        reader.readAsDataURL(input.files[0]);
    }
}

// 取消编辑，返回道具管理页面
function cancelEditUtility() {
    if (confirm('确定要取消编辑吗？未保存的更改将丢失。')) {
        // 切换回道具管理标签页
        document.querySelectorAll('.tab-content').forEach(tab => tab.classList.remove('active'));
        document.querySelectorAll('.nav-item').forEach(nav => nav.classList.remove('active'));
        document.getElementById('exported-tab').classList.add('active');
        document.querySelector('.nav-item[data-tab="exported"]').classList.add('active');
        
        // 清空表单
        document.getElementById('edit-utility-form').reset();
        currentEditingUtility = null;
        
        // 刷新道具列表
        loadExportedUtilities();
    }
}

// 提交编辑后的道具
async function submitEditedUtility(event) {
    event.preventDefault();
    
    const resultEl = document.getElementById('edit-utility-result');
    resultEl.className = 'result-message';
    resultEl.textContent = '正在保存...';
    resultEl.classList.add('show');
    
    const formData = new FormData();
    
    // 基本信息
    formData.append('hash', document.getElementById('edit-util-hash').value);
    formData.append('name', document.getElementById('edit-util-name').value);
    formData.append('map', document.getElementById('edit-util-map').value);
    formData.append('type', document.getElementById('edit-util-type').value);
    formData.append('team', document.getElementById('edit-util-team').value);
    formData.append('throw_type', document.getElementById('edit-util-throw-type').value || '未知');
    formData.append('notes', document.getElementById('edit-util-notes').value || '');
    formData.append('tags', document.getElementById('edit-util-tags').value || '');  // 添加标签
    
    // 坐标信息
    const throwX = parseFloat(document.getElementById('edit-util-throw-x').value);
    const throwY = parseFloat(document.getElementById('edit-util-throw-y').value);
    const throwZ = parseFloat(document.getElementById('edit-util-throw-z').value);
    formData.append('throw_position', JSON.stringify({x: throwX, y: throwY, z: throwZ}));
    
    const pitch = parseFloat(document.getElementById('edit-util-pitch').value);
    const yaw = parseFloat(document.getElementById('edit-util-yaw').value);
    formData.append('throw_angles', JSON.stringify({pitch: pitch, yaw: yaw}));
    
    // 落点位置（保持默认或从原数据读取）
    formData.append('land_position', JSON.stringify({x: 0, y: 0, z: 0}));
    
    // 图片文件（如果有新上传的）
    const positionFile = document.getElementById('edit-util-img-position').files[0];
    const crosshairFile = document.getElementById('edit-util-img-crosshair').files[0];
    const landingFile = document.getElementById('edit-util-img-landing').files[0];
    
    if (positionFile) formData.append('img_position', positionFile);
    if (crosshairFile) formData.append('img_crosshair', crosshairFile);
    if (landingFile) formData.append('img_landing', landingFile);
    
    try {
        const response = await fetch('/api/update_utility', {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        
        if (result.success) {
            resultEl.className = 'result-message show success';
            resultEl.textContent = '✓ ' + result.message;
            
            // 3秒后淡出隐藏提示，停留在编辑页面
            setTimeout(() => {
                resultEl.classList.remove('show');
            }, 3000);
        } else {
            resultEl.className = 'result-message show error';
            resultEl.textContent = '✗ 保存失败：' + (result.error || '未知错误');
            
            // 3秒后淡出隐藏错误提示
            setTimeout(() => {
                resultEl.classList.remove('show');
            }, 3000);
        }
    } catch (error) {
        console.error('保存道具错误:', error);
        resultEl.className = 'result-message show error';
        resultEl.textContent = '✗ 保存失败：网络错误';
        
        // 3秒后淡出隐藏错误提示
        setTimeout(() => {
            resultEl.classList.remove('show');
        }, 3000);
    }
}

function closeEditModal(event) {
    if (event) {
        // 如果点击的是模态框背景，才关闭
        if (event.target.id !== 'edit-modal') return;
    }
    document.getElementById('edit-modal').classList.remove('active');
    currentEditingUtility = null;
}

async function saveEditedUtility(event) {
    event.preventDefault();
    
    const hash = document.getElementById('edit-hash').value;
    const updatedInfo = {
        display_name: document.getElementById('edit-name').value.trim(),
        type: document.getElementById('edit-type').value,
        team: document.getElementById('edit-team').value,
        throw_type: document.getElementById('edit-throw-type').value.trim(),
        notes: document.getElementById('edit-notes').value.trim()
    };
    
    if (!updatedInfo.display_name) {
        alert('请填写道具名称');
        return;
    }
    
    try {
        const response = await fetch('/api/edit_exported', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                hash: hash,
                info: updatedInfo
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            alert('' + result.message);
            closeEditModal();
            loadExportedUtilities();
        } else {
            alert('' + result.message);
        }
    } catch (error) {
        alert('保存失败: ' + error.message);
    }
}

async function exportData() {
    if (!confirm('确定要导出数据吗？\n\n这会将已批准的道具导出到 public/ 目录。')) {
        return;
    }
    
    const btn = event.target;
    const resultEl = document.getElementById('export-result');
    
    btn.disabled = true;
    btn.textContent = '导出中...';
    resultEl.className = 'result-message';
    resultEl.textContent = '';
    
    try {
        const response = await fetch('/api/export', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        
        const result = await response.json();
        
        resultEl.className = 'result-message show ' + (result.success ? 'success' : 'error');
        resultEl.textContent = result.message;
        
        if (result.success) {
            resultEl.innerHTML += '<br><br><strong>导出完成！</strong><br>下一步: 使用 Git 推送更新';
            loadExportStats();
        }
    } catch (error) {
        resultEl.className = 'result-message show error';
        resultEl.textContent = '导出失败: ' + error.message;
    } finally {
        btn.disabled = false;
        btn.textContent = '开始导出';
    }
}

async function reExportData() {
    if (!confirm('确定要重新导出数据吗？\n\n这会重新生成 public/ 目录中的所有道具数据（包括已编辑的道具）。')) {
        return;
    }
    
    const btn = event.target;
    const resultEl = document.getElementById('re-export-result');
    
    btn.disabled = true;
    btn.textContent = '导出中...';
    resultEl.className = 'result-message';
    resultEl.textContent = '';
    
    try {
        const response = await fetch('/api/export', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        
        const result = await response.json();
        
        resultEl.className = 'result-message show ' + (result.success ? 'success' : 'error');
        resultEl.textContent = result.message;
        
        if (result.success) {
            resultEl.innerHTML += '<br><br><strong>导出完成！</strong><br>下一步: 使用 Git 推送更新';
            loadExportedUtilities();
        }
    } catch (error) {
        resultEl.className = 'result-message show error';
        resultEl.textContent = '导出失败: ' + error.message;
    } finally {
        btn.disabled = false;
        btn.textContent = '重新导出';
    }
}

// ========== 工具函数 ==========

// 复制文本到剪贴板
function copyToClipboard(text, button) {
    // 创建临时文本域
    const textarea = document.createElement('textarea');
    textarea.value = text;
    textarea.style.position = 'fixed';
    textarea.style.opacity = '0';
    document.body.appendChild(textarea);
    
    // 选择并复制
    textarea.select();
    textarea.setSelectionRange(0, 99999); // 兼容移动设备
    
    try {
        document.execCommand('copy');
        
        // 更新按钮状态
        const originalText = button.textContent;
        button.textContent = '已复制';
        button.style.background = '#00d4aa';
        
        // 2秒后恢复
        setTimeout(() => {
            button.textContent = originalText;
            button.style.background = '';
        }, 2000);
    } catch (err) {
        console.error('复制失败:', err);
        alert('复制失败，请手动选择并复制');
    } finally {
        document.body.removeChild(textarea);
    }
}


// ========== 添加道具功能 ==========

// 图片预览功能
function previewImage(input, previewId) {
    const preview = document.getElementById(previewId);
    const file = input.files[0];
    
    if (file && file.size > 5 * 1024 * 1024) {
        showAddResult('图片大小不能超过 5MB', 'error');
        input.value = '';
        return;
    }
    
    if (file) {
        const reader = new FileReader();
        reader.onload = function(e) {
            preview.innerHTML = `<img src="${e.target.result}" alt="Preview">`;
        };
        reader.readAsDataURL(file);
    }
}

// 提交手动添加的道具
async function submitManualUtility(event) {
    event.preventDefault();
    
    const formData = new FormData();
    
    // 基本信息
    formData.append('name', document.getElementById('add-name').value);
    formData.append('map', document.getElementById('add-map').value);
    formData.append('type', document.getElementById('add-type').value);
    formData.append('team', document.getElementById('add-team').value);
    formData.append('throw_type', document.getElementById('add-throw-type').value || '未知');
    formData.append('source', '手动添加');  // 固定值
    formData.append('notes', document.getElementById('add-notes').value || '');
    formData.append('tags', document.getElementById('add-tags').value || '');  // 添加标签
    
    // 坐标信息 - 投掷位置
    const throwX = parseFloat(document.getElementById('add-throw-x').value);
    const throwY = parseFloat(document.getElementById('add-throw-y').value);
    const throwZ = parseFloat(document.getElementById('add-throw-z').value);
    formData.append('throw_position', JSON.stringify({x: throwX, y: throwY, z: throwZ}));
    
    // 坐标信息 - 投掷角度
    const pitch = parseFloat(document.getElementById('add-pitch').value);
    const yaw = parseFloat(document.getElementById('add-yaw').value);
    formData.append('throw_angles', JSON.stringify({pitch: pitch, yaw: yaw}));
    
    // 落点位置使用默认值（0, 0, 0），因为实际落点由游戏物理引擎决定
    formData.append('land_position', JSON.stringify({x: 0, y: 0, z: 0}));
    
    // 图片文件
    const positionFile = document.getElementById('add-img-position').files[0];
    const crosshairFile = document.getElementById('add-img-crosshair').files[0];
    const landingFile = document.getElementById('add-img-landing').files[0];
    
    if (!positionFile || !crosshairFile || !landingFile) {
        showAddResult('请上传所有三张截图', 'error');
        return;
    }
    
    formData.append('img_position', positionFile);
    formData.append('img_crosshair', crosshairFile);
    formData.append('img_landing', landingFile);
    
    try {
        const response = await fetch('/api/add_manual_utility', {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        
        if (result.success) {
            showAddResult('道具添加成功！已自动导出到前端，无需手动导出', 'success');
            resetAddForm();
            // 刷新统计数据
            loadStats();
            loadOverviewStats();
        } else {
            showAddResult('添加失败：' + (result.error || '未知错误'), 'error');
        }
    } catch (error) {
        console.error('添加道具错误:', error);
        showAddResult('添加失败：网络错误', 'error');
    }
}

// 重置添加表单
function resetAddForm() {
    document.getElementById('add-utility-form').reset();
    document.getElementById('preview-position').innerHTML = '<span style="font-size: 48px; color: #667eea;">📷</span><p style="margin-top: 10px; color: #666;">站位图</p>';
    document.getElementById('preview-crosshair').innerHTML = '<span style="font-size: 48px; color: #667eea;">📷</span><p style="margin-top: 10px; color: #666;">准星图</p>';
    document.getElementById('preview-landing').innerHTML = '<span style="font-size: 48px; color: #667eea;">📷</span><p style="margin-top: 10px; color: #666;">落点图</p>';
}

// 显示添加结果消息
function showAddResult(message, type) {
    const resultDiv = document.getElementById('add-utility-result');
    resultDiv.textContent = message;
    resultDiv.className = `result-message ${type} show`;
    
    setTimeout(() => {
        resultDiv.classList.remove('show');
    }, 5000);
}
