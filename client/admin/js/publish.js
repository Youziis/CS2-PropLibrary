// 导出发布与已导出管理
// 拆分自 client/admin/script.js，以普通 <script> 加载（函数保持全局作用域）
// 依赖: utils.js

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
