// 选择要截图的道具
// 拆分自 client/admin/script.js，以普通 <script> 加载（函数保持全局作用域）
// 依赖: state.js, utils.js

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
        html += '<div class="button-group">';
        html += '<button class="btn btn-large btn-primary" onclick="saveSelectedUtilities()">保存选择并准备截图</button>';
        html += '<button class="btn btn-large btn-danger" onclick="deleteSelectedUtilities()">批量删除</button>';
        html += '</div>';
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
        
        // 类型筛选：将incendiary和molotov视为同一类型（燃烧弹）
        let typeMatch;
        if (currentFilterType === 'all') {
            typeMatch = true;
        } else if (currentFilterType === 'incendiary') {
            // 选择"燃烧弹"时，同时匹配incendiary和molotov
            typeMatch = (utilType === 'incendiary' || utilType === 'molotov');
        } else {
            // 其他类型正常匹配
            typeMatch = (utilType === currentFilterType);
        }
        
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

async function deleteSelectedUtilities() {
    if (selectedUtilities.size === 0) {
        alert('请至少选择一个道具');
        return;
    }
    
    const confirmMessage = `⚠️ 确定要删除选中的 ${selectedUtilities.size} 个道具吗？\n\n` +
        `此操作将：\n` +
        `• 从数据库中删除道具记录\n` +
        `• 删除相关的截图文件（如果有）\n` +
        `• 删除前端JSON数据（如果已导出）\n\n` +
        `此操作不可撤销！`;
    
    if (!confirm(confirmMessage)) {
        return;
    }
    
    // 二次确认
    if (!confirm(`再次确认：真的要删除这 ${selectedUtilities.size} 个道具吗？`)) {
        return;
    }
    
    const selectedHashArray = Array.from(selectedUtilities);
    
    try {
        const btn = event.target;
        btn.disabled = true;
        btn.textContent = '删除中...';
        
        // 批量调用删除API
        let successCount = 0;
        let failCount = 0;
        const errors = [];
        
        for (const hash of selectedHashArray) {
            try {
                const response = await fetch(`/api/utilities/${hash}`, {
                    method: 'DELETE'
                });
                
                const result = await response.json();
                
                if (result.success) {
                    successCount++;
                } else {
                    failCount++;
                    errors.push(`${hash}: ${result.message}`);
                }
            } catch (error) {
                failCount++;
                errors.push(`${hash}: ${error.message}`);
            }
        }
        
        // 显示结果
        let message = `删除完成！\n\n成功: ${successCount} 个\n失败: ${failCount} 个`;
        if (errors.length > 0 && errors.length <= 5) {
            message += '\n\n失败详情:\n' + errors.join('\n');
        }
        
        alert(message);
        
        // 清空选择
        selectedUtilities.clear();
        
        // 刷新页面数据
        loadStats();
        loadTypeStats();
        
    } catch (error) {
        alert('删除失败: ' + error.message);
    } finally {
        const btn = event.target;
        if (btn) {
            btn.disabled = false;
            btn.textContent = '批量删除';
        }
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
