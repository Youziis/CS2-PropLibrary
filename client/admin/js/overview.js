// 总览统计
// 拆分自 client/admin/script.js，以普通 <script> 加载（函数保持全局作用域）
// 依赖: state.js

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
