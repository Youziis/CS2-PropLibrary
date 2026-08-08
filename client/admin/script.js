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
    initSubTabs();
    loadStats();
    loadDemos();
    loadTypeStats();
    loadPending();
    loadExportStats();
});

// 标签页切换
function initTabs() {
    const tabs = document.querySelectorAll('.tab');
    const contents = document.querySelectorAll('.tab-content');
    
    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            const targetTab = tab.dataset.tab;
            
            // 切换活动标签
            tabs.forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
            
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
            }
        });
    });
}

// 子标签页切换
function initSubTabs() {
    const subTabs = document.querySelectorAll('.sub-tab');
    const subContents = document.querySelectorAll('.sub-tab-content');
    
    subTabs.forEach(subTab => {
        subTab.addEventListener('click', () => {
            const targetSubTab = subTab.dataset.subtab;
            
            // 切换活动子标签
            subTabs.forEach(st => st.classList.remove('active'));
            subTab.classList.add('active');
            
            // 切换内容
            subContents.forEach(sc => sc.classList.remove('active'));
            document.getElementById(`${targetSubTab}-subtab`).classList.add('active');
            
            // 加载对应数据
            if (targetSubTab === 'pending-export') {
                loadPendingExportUtilities();
            } else if (targetSubTab === 'exported') {
                loadExportedUtilities();
            }
        });
    });
}

// 加载统计信息
async function loadStats() {
    try {
        const response = await fetch('/api/stats');
        const stats = await response.json();
        
        document.getElementById('total-count').textContent = stats.total_parsed || 0;
        document.getElementById('pending-count').textContent = stats.pending_review || 0;
        document.getElementById('approved-count').textContent = stats.approved || 0;
    } catch (error) {
        console.error('加载统计失败:', error);
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
                    <h3>📁 ${demo.name}</h3>
                    <p>大小: ${formatFileSize(demo.size)}</p>
                    ${demo.parsed ? '<span class="badge badge-success">✅ 已解析</span>' : ''}
                </div>
                <button class="btn btn-primary" onclick="parseDemo('${demo.name}')" ${demo.parsed ? 'disabled' : ''}>
                    ${demo.parsed ? '✅ 已解析' : '🔍 解析'}
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
    btn.textContent = '⏳ 解析中...';
    
    try {
        const response = await fetch('/api/parse_demo', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ demo_name: demoName })
        });
        
        const result = await response.json();
        
        if (result.success) {
            alert(`✅ ${result.message}`);
            loadStats();
            loadTypeStats();
        } else {
            alert(`❌ ${result.message}`);
        }
    } catch (error) {
        alert('❌ 解析失败: ' + error.message);
    } finally {
        btn.disabled = false;
        btn.textContent = '🔍 解析';
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
        
        // 显示统计和道具列表
        let html = '';
        
        // 1. 统计卡片区域 - 固定4列横向显示
        html += '<div class="stats-summary">';
        html += `<h3>📊 道具统计（共 ${allPendingUtilities.length} 个，已拒绝 ${rejectedUtilities.length} 个）</h3>`;
        html += '<div class="type-cards">';
        
        // 确保按固定顺序显示4种道具类型
        const typeOrder = ['smoke', 'flashbang', 'hegrenade', 'incendiary'];
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
        html += '</div>';
        
        // 2. 标签选择区域（整合在一个框内）
        html += '<div class="selection-controls">';
        
        // 2.1 统计来源demo和地图 - 添加下拉筛选器
        const demoCounts = {};
        const mapCounts = {};
        allPendingUtilities.forEach(u => {
            const demo = u.source_demo || '未知';
            const map = u.map || u.map_name || '未知';
            demoCounts[demo] = (demoCounts[demo] || 0) + 1;
            mapCounts[map] = (mapCounts[map] || 0) + 1;
        });
        
        // 筛选器区域
        html += '<div class="filter-section">';
        html += '<h4>🔍 筛选道具</h4>';
        html += '<div class="filters" style="display: flex; gap: 10px; margin-bottom: 15px;">';
        
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
        
        // 状态筛选 - 改为：全部状态、未拒绝、已拒绝
        html += '<select id="selection-filter-screenshot" class="filter-select" onchange="filterByScreenshotStatus(this.value)">';
        html += `<option value="all">全部状态 (${allPendingUtilities.length})</option>`;
        html += `<option value="no">未拒绝 (${notRejectedUtilities.length})</option>`;
        html += `<option value="yes">已拒绝 (${rejectedUtilities.length})</option>`;
        html += '</select>';
        
        html += '</div>';
        html += '</div>';
        
        // 2.2 道具类型筛选按钮
        html += '<div class="select-section">';
        html += '<h4>🎯 按类型筛选</h4>';
        html += '<div class="select-buttons">';
        html += '<button class="btn btn-type active" data-type="all" onclick="filterByType(\'all\')">全部类型</button>';
        html += '<button class="btn btn-type" data-type="smoke" onclick="filterByType(\'smoke\')">烟雾弹</button>';
        html += '<button class="btn btn-type" data-type="flashbang" onclick="filterByType(\'flashbang\')">闪光弹</button>';
        html += '<button class="btn btn-type" data-type="hegrenade" onclick="filterByType(\'hegrenade\')">手雷</button>';
        html += '<button class="btn btn-type" data-type="incendiary" onclick="filterByType(\'incendiary\')">燃烧弹</button>';
        html += '</div>';
        html += '</div>';
        
        // 2.3 快捷操作按钮
        html += '<div class="select-section">';
        html += '<h4>💡 快捷操作</h4>';
        html += '<p class="hint" style="font-size: 12px; color: #888; margin-bottom: 10px;">对当前显示的道具进行操作</p>';
        html += '<div class="select-buttons">';
        html += '<button id="toggle-select-all-btn" class="btn btn-primary" onclick="toggleSelectAll()">✓ 全选</button>';
        html += '</div>';
        html += '</div>';
        
        // 2.4 已选择数量和保存按钮
        html += '<div class="selection-summary-inline">';
        html += '<div class="summary-info">';
        html += '<span class="label">已选择</span>';
        html += '<span id="selected-count" class="count">0</span>';
        html += '<span class="label">个道具</span>';
        html += '<span class="label"> / 当前显示</span>';
        html += '<span id="visible-count" class="count">0</span>';
        html += '<span class="label">个</span>';
        html += '</div>';
        html += '<button class="btn btn-large btn-primary" onclick="saveSelectedUtilities()">💾 保存选择并准备截图</button>';
        html += '</div>';
        
        html += '</div>'; // 结束 selection-controls
        
        // 3. 道具列表 - 固定3列
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
        <div class="utility-select-card ${isRejected ? 'is-rejected' : ''}" data-hash="${hash}" data-status="${status}">
            <div class="checkbox-wrapper">
                <input type="checkbox" id="check-${hash}" class="utility-checkbox" 
                       onchange="toggleUtility('${hash}')" data-type="${type}">
            </div>
            <div class="utility-select-info">
                <div class="utility-header">
                    <span class="type-badge type-${type}">${TYPE_NAMES[type] || type}</span>
                    <span class="team-badge team-${team}">${team}</span>
                    ${isRejected ? '<span class="rejected-badge">❌ 已拒绝</span>' : '<span class="normal-badge">✅ 正常</span>'}
                </div>
                <div class="utility-details">
                    <div><strong>地图:</strong> ${map}</div>
                    <div><strong>玩家:</strong> ${player}</div>
                    <div><strong>投掷方式:</strong> ${throwType}</div>
                    <div><strong>来源Demo:</strong> <span style="color: #667eea;">${sourceDemo}</span></div>
                    ${isRejected ? '<div style="color: #ff6b6b; font-weight: bold; margin-top: 5px;">🔄 可重新选择截图</div>' : ''}
                    <div style="font-size: 11px; color: #666; margin-top: 5px;">
                        解析时间: ${parseTime}
                    </div>
                </div>
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
    const visibleCards = Array.from(document.querySelectorAll('.utility-select-card'))
        .filter(card => card.style.display !== 'none');
    
    if (visibleCountEl) {
        visibleCountEl.textContent = visibleCards.length;
    }
    
    // 更新全选按钮状态
    if (toggleBtn && visibleCards.length > 0) {
        const visibleHashes = visibleCards.map(card => card.dataset.hash);
        const visibleSelectedCount = visibleHashes.filter(hash => selectedUtilities.has(hash)).length;
        const allVisibleSelected = visibleHashes.every(hash => selectedUtilities.has(hash));
        
        if (allVisibleSelected) {
            // 全部选中状态
            toggleBtn.innerHTML = '✗ 取消全选';
            toggleBtn.classList.remove('btn-primary');
            toggleBtn.classList.add('btn-selected');
        } else if (visibleSelectedCount > 0) {
            // 部分选中状态
            toggleBtn.innerHTML = `✓ 全选 (${visibleSelectedCount}/${visibleCards.length})`;
            toggleBtn.classList.add('btn-primary');
            toggleBtn.classList.remove('btn-selected');
        } else {
            // 未选中状态
            toggleBtn.innerHTML = '✓ 全选';
            toggleBtn.classList.add('btn-primary');
            toggleBtn.classList.remove('btn-selected');
        }
    }
}

function toggleSelectAll() {
    // 计算当前可见的道具
    const visibleCards = Array.from(document.querySelectorAll('.utility-select-card'))
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
    document.querySelectorAll('.utility-select-card').forEach(card => {
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
        alert('❌ 请至少选择一个道具');
        return;
    }
    
    if (!confirm(`确定要保存选择的 ${selectedUtilities.size} 个道具吗？\n\n保存后可以运行截图工具进行截图。`)) {
        return;
    }
    
    // 获取选中的道具数据
    const selected = allPendingUtilities.filter(u => selectedUtilities.has(u.hash));
    
    try {
        // ✅ 修改为新的API端点
        const response = await fetch('/api/utilities/select', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                utilities: selected
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            alert(`✅ ${result.message}\n\n下一步：\n1. 确保后端服务器运行中（http://localhost:5000）\n2. 启动 CS2 游戏，进入对应地图\n3. 开启控制台输入：sv_cheats 1\n4. 运行截图工具：python client/screenshot.py`);
            
            // 刷新页面数据
            loadStats();
            loadTypeStats();
        } else {
            alert(`❌ ${result.message}`);
        }
    } catch (error) {
        alert('❌ 保存失败: ' + error.message);
    }
}

async function selectType(type) {
    const btn = event.target;
    btn.disabled = true;
    const originalText = btn.textContent;
    btn.textContent = '⏳ 处理中...';
    
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
        alert('❌ 选择失败: ' + error.message);
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
                    <h3>🔍 没有符合筛选条件的道具</h3>
                    <p style="margin: 20px 0;">请调整筛选条件或点击"全部来源/类型/队伍"</p>
                </div>
            `;
        } else {
            // 真的没有已截图的道具
            gridEl.innerHTML = `
                <div class="info-box" style="text-align: center; padding: 40px;">
                    <h3>📸 还没有已截图的道具</h3>
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
    const screenshotId = u.screenshot_id || 'unknown';
    const team = u.team || 'Unknown';
    const throwType = u.throw_type || 'unknown';
    const flightTime = u.flight_time || 0;
    
    // 使用 screenshot_filename_base 字段（包含完整的文件名前缀）
    const screenshotBase = u.screenshot_filename_base || `${map}_unknown_${screenshotId}`;
    
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
                    <button class="btn-copy" onclick="copyToClipboard('${tpCommand.replace(/'/g, "\\'")}', this)">📋 复制</button>
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
                    <button class="btn-approve" onclick="approveUtility('${u.hash}')">✓ 批准</button>
                    <button class="btn-reject" onclick="rejectUtility('${u.hash}')">✗ 拒绝</button>
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
                    <small style="color: #888;">📸 等待截图</small>
                </div>
                
                <div class="actions">
                    <button class="btn-delete" onclick="deletePending('${u.hash}')">🗑️ 删除</button>
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
        alert('❌ 错误：找不到审核页面');
        return;
    }
    
    const card = grid.querySelector(`[data-hash="${hash}"]`);
    
    if (!card) {
        alert('❌ 错误：找不到道具卡片元素');
        console.error('找不到 data-hash:', hash);
        return;
    }
    
    const nameInput = card.querySelector('.util-name');
    
    if (!nameInput) {
        alert('❌ 错误：找不到道具名称输入框\n\n请刷新页面后重试（Ctrl+Shift+R 强制刷新）');
        console.error('找不到 .util-name 元素，卡片内容:', card.innerHTML.substring(0, 500));
        return;
    }
    
    const name = nameInput.value.trim();
    
    // 验证必填字段
    if (!name) {
        alert('❌ 请填写道具名称');
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
                loadPending();
                loadStats();
                loadExportStats();
            }, 300);
        } else {
            alert('❌ ' + result.message);
        }
    } catch (error) {
        alert('❌ 操作失败: ' + error.message);
    }
}

async function rejectUtility(hash) {
    if (!confirm('确定要拒绝这个道具吗？\n\n拒绝后：\n- 道具状态变为"已拒绝"\n- 截图文件将被删除\n- 不会再出现在选择列表中\n- 数据保留在数据库中')) {
        return;
    }
    
    try {
        const response = await fetch('/api/reject', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ hash: hash })
        });
        
        const result = await response.json();
        
        if (result.success) {
            const card = document.querySelector(`[data-hash="${hash}"]`);
            if (card) {
                card.style.opacity = '0';
            }
            setTimeout(() => {
                loadPending();
                loadStats();
            }, 300);
            alert('✅ ' + result.message);
        } else {
            alert('❌ ' + result.message);
        }
    } catch (error) {
        alert('❌ 操作失败: ' + error.message);
    }
}

async function deleteUtilityPermanently(hash) {
    if (!confirm('⚠️ 确定要永久删除这个道具吗？\n\n此操作将：\n- 永久删除道具数据\n- 删除所有截图文件\n- 无法恢复\n\n建议：如果只是暂时不需要，请使用"拒绝"按钮')) {
        return;
    }
    
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
                loadPending();
                loadStats();
            }, 300);
            alert('✅ ' + result.message);
        } else {
            alert('❌ ' + result.message);
        }
    } catch (error) {
        alert('❌ 操作失败: ' + error.message);
    }
}

async function deletePending(hash) {
    // 这个函数现在被 deleteUtilityPermanently 替代
    return deleteUtilityPermanently(hash);
}

// ========== 导出发布 ==========

async function loadExportStats() {
    loadPendingExportUtilities();
    loadExportedUtilities();
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
            <h3 style="margin-bottom: 15px;">📋 待导出道具列表</h3>
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
                                🗑️ 删除
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
async function loadExportedUtilities() {
    const gridEl = document.getElementById('exported-grid');
    const countEl = document.getElementById('exported-count');
    
    if (!gridEl || !countEl) return;
    
    gridEl.innerHTML = '<div class="loading">加载中...</div>';
    
    try {
        const response = await fetch('/api/export/exported');
        const data = await response.json();
        
        countEl.textContent = data.utilities.length;
        
        if (data.utilities.length === 0) {
            gridEl.innerHTML = '<p class="hint">还没有已导出的道具</p>';
            return;
        }
        
        gridEl.innerHTML = data.utilities.map(u => renderExportedUtilityCard(u)).join('');
    } catch (error) {
        console.error('加载已导出道具失败:', error);
        gridEl.innerHTML = '<p class="hint error">加载失败</p>';
    }
}

// 渲染已导出道具卡片
function renderExportedUtilityCard(u) {
    const type = u.type || u.grenade_type || 'unknown';
    const map = u.map || u.map_name || 'unknown';
    const screenshotId = u.screenshot_id;
    const name = u.display_name || '未命名';
    
    // 使用 screenshot_filename_base 字段
    const screenshotBase = u.screenshot_filename_base || `${map}_unknown_${screenshotId}`;
    
    return `
        <div class="utility-card">
            <div class="screenshots">
                <img src="../../output/screenshots/${screenshotBase}_position.jpg" 
                     alt="站位" onclick="showImage(this.src)" 
                     onerror="this.style.display='none'">
                <img src="../../output/screenshots/${screenshotBase}_crosshair.jpg" 
                     alt="准星" onclick="showImage(this.src)" 
                     onerror="this.style.display='none'">
                <img src="../../output/screenshots/${screenshotBase}_landing.jpg" 
                     alt="落点" onclick="showImage(this.src)" 
                     onerror="this.style.display='none'">
            </div>
            
            <div class="utility-info">
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
                    <button class="btn" onclick="editExported('${u.hash}')">✏️ 编辑</button>
                    <button class="btn-delete" onclick="unExportUtility('${u.hash}')">↩️ 撤销导出</button>
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
            alert('✅ ' + result.message);
            loadExportStats();
            loadStats();
        } else {
            alert('❌ ' + result.message);
        }
    } catch (error) {
        alert('❌ 操作失败: ' + error.message);
    }
}

// 撤销导出（将已导出道具移回已批准状态）
async function unExportUtility(hash) {
    if (!confirm('确定要撤销导出吗？\n\n道具将移回"待导出"状态，客户端需要重新部署才能生效。')) {
        return;
    }
    
    try {
        const response = await fetch('/api/unexport', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ hash: hash })
        });
        
        const result = await response.json();
        
        if (result.success) {
            alert('✅ ' + result.message);
            loadExportStats();
            loadStats();
        } else {
            alert('❌ ' + result.message);
        }
    } catch (error) {
        alert('❌ 操作失败: ' + error.message);
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
                alert('❌ 道具未找到');
                return;
            }
            
            currentEditingUtility = utility;
            
            // 填充表单
            document.getElementById('edit-hash').value = utility.hash;
            document.getElementById('edit-name').value = utility.display_name || '';
            document.getElementById('edit-type').value = utility.type || 'smoke';
            document.getElementById('edit-team').value = utility.team || 'Unknown';
            document.getElementById('edit-throw-type').value = utility.throw_type || '';
            document.getElementById('edit-notes').value = utility.notes || '';
            
            // 显示模态框
            document.getElementById('edit-modal').classList.add('active');
        })
        .catch(error => {
            console.error('加载道具失败:', error);
            alert('❌ 加载失败');
        });
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
        alert('❌ 请填写道具名称');
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
            alert('✅ ' + result.message);
            closeEditModal();
            loadExportedUtilities();
        } else {
            alert('❌ ' + result.message);
        }
    } catch (error) {
        alert('❌ 保存失败: ' + error.message);
    }
}

async function exportData() {
    if (!confirm('确定要导出数据吗？\n\n这会将已批准的道具导出到 public/ 目录。')) {
        return;
    }
    
    const btn = event.target;
    const resultEl = document.getElementById('export-result');
    
    btn.disabled = true;
    btn.textContent = '⏳ 导出中...';
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
            resultEl.innerHTML += '<br><br><strong>✅ 导出完成！</strong><br>下一步: 使用 Git 推送更新';
            loadExportStats();
        }
    } catch (error) {
        resultEl.className = 'result-message show error';
        resultEl.textContent = '导出失败: ' + error.message;
    } finally {
        btn.disabled = false;
        btn.textContent = '🚀 开始导出';
    }
}

async function reExportData() {
    if (!confirm('确定要重新导出数据吗？\n\n这会重新生成 public/ 目录中的所有道具数据（包括已编辑的道具）。')) {
        return;
    }
    
    const btn = event.target;
    const resultEl = document.getElementById('re-export-result');
    
    btn.disabled = true;
    btn.textContent = '⏳ 导出中...';
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
            resultEl.innerHTML += '<br><br><strong>✅ 导出完成！</strong><br>下一步: 使用 Git 推送更新';
            loadExportedUtilities();
        }
    } catch (error) {
        resultEl.className = 'result-message show error';
        resultEl.textContent = '导出失败: ' + error.message;
    } finally {
        btn.disabled = false;
        btn.textContent = '🚀 重新导出';
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
        button.textContent = '✅ 已复制';
        button.style.background = '#00d4aa';
        
        // 2秒后恢复
        setTimeout(() => {
            button.textContent = originalText;
            button.style.background = '';
        }, 2000);
    } catch (err) {
        console.error('复制失败:', err);
        alert('❌ 复制失败，请手动选择并复制');
    } finally {
        document.body.removeChild(textarea);
    }
}
