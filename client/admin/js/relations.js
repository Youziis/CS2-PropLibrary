// 道具关联管理
// 拆分自 client/admin/script.js，以普通 <script> 加载（函数保持全局作用域）
// 依赖: utils.js

// ==================== 关联管理功能（通过Hash搜索） ====================

let selectedUtilitiesMap = new Map(); // hash -> utility对象
let searchedUtilities = []; // 所有搜索过的道具

// ==================== 关联管理：子标签页切换 ====================
function showRelationsSubTab(subtab) {
    // 更新标签页按钮状态
    document.querySelectorAll('.sub-tab').forEach(tab => {
        tab.classList.remove('active');
        if (tab.dataset.subtab === subtab) {
            tab.classList.add('active');
        }
    });
    
    // 切换内容显示
    document.querySelectorAll('.sub-tab-content').forEach(content => {
        content.classList.remove('active');
    });
    
    if (subtab === 'create') {
        document.getElementById('relations-create-tab').classList.add('active');
    } else if (subtab === 'edit') {
        document.getElementById('relations-edit-tab').classList.add('active');
        // 加载关联组列表
        loadRelationGroups();
    }
}

// ==================== 关联管理：编辑页面 ====================

// 加载所有关联组
async function loadRelationGroups() {
    const container = document.getElementById('relation-groups-container');
    container.innerHTML = '<div class="loading">加载中...</div>';
    
    try {
        const response = await fetch('/api/relations/groups');
        const result = await response.json();
        
        if (!response.ok) {
            throw new Error(result.error || '加载失败');
        }
        
        if (result.groups.length === 0) {
            container.innerHTML = '<div class="empty-state">暂无关联组</div>';
            return;
        }
        
        // 渲染关联组
        container.innerHTML = result.groups.map((group, index) => 
            renderRelationGroup(group, index)
        ).join('');
        
    } catch (error) {
        console.error('加载关联组失败:', error);
        container.innerHTML = `<div class="error-message">❌ 加载失败：${error.message}</div>`;
    }
}

// 渲染单个关联组
function renderRelationGroup(group, index) {
    const groupName = group.combo_group || `关联组 #${index + 1}`;
    const utilities = group.utilities || [];
    const groupId = `group-${index}`;
    const hashesJson = JSON.stringify(utilities.map(u => u.hash));
    
    // 存储到临时变量，避免HTML属性中的引号问题
    window[`groupHashes_${groupId}`] = utilities.map(u => u.hash);
    
    return `
        <div class="relation-group-card" data-group="${group.combo_group || ''}" data-group-id="${groupId}">
            <div class="relation-group-header">
                <div class="relation-group-title">
                    <h4>📦 ${groupName}</h4>
                    <span class="relation-group-badge">${group.count} 个道具</span>
                </div>
                <div class="relation-group-actions">
                    <button class="btn btn-sm btn-primary" onclick="addUtilityToGroup('${group.combo_group || ''}', window['groupHashes_${groupId}'])">
                        ➕ 添加道具
                    </button>
                    <button class="btn btn-sm btn-danger" onclick="deleteRelationGroup('${group.combo_group || ''}', window['groupHashes_${groupId}'])">
                        🗑️ 删除组
                    </button>
                </div>
            </div>
            
            <div class="relation-group-utilities">
                ${utilities.map((utility, idx) => `
                    <div class="relation-utility-item">
                        <div class="relation-utility-info">
                            <div class="relation-utility-name">
                                ${utility.combo_order ? `${utility.combo_order}. ` : ''}${utility.display_name || utility.name}
                            </div>
                            <div class="relation-utility-meta">
                                ${utility.map_name} · ${utility.utility_type}
                            </div>
                        </div>
                        <button class="btn btn-sm btn-danger" onclick="removeUtilityFromGroup('${utility.hash}', '${group.combo_group || ''}', window['groupHashes_${groupId}'])">
                            ✕
                        </button>
                    </div>
                `).join('')}
            </div>
        </div>
    `;
}

// 从组中移除单个道具
async function removeUtilityFromGroup(utilityHash, comboGroup, allHashes) {
    if (!confirm(`确定要从关联组中移除这个道具吗？`)) {
        return;
    }
    
    try {
        // 获取该道具在这个组中的所有关联
        const otherHashes = allHashes.filter(h => h !== utilityHash);
        
        // 逐个移除关联
        for (const otherHash of otherHashes) {
            const response = await fetch('/api/relations/remove', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    utility_hash: utilityHash,
                    related_hash: otherHash,
                    bidirectional: true
                })
            });
            
            if (!response.ok) {
                throw new Error('移除失败');
            }
        }
        
        alert('✅ 已从关联组中移除');
        loadRelationGroups();
        
    } catch (error) {
        alert('❌ 移除失败：' + error.message);
    }
}

// 删除整个关联组
async function deleteRelationGroup(comboGroup, allHashes) {
    const groupName = comboGroup || '该关联组';
    
    if (!confirm(`确定要删除 "${groupName}" 吗？\n这将移除组内所有道具之间的关联关系。`)) {
        return;
    }
    
    try {
        // 移除组内所有道具的相互关联
        for (let i = 0; i < allHashes.length; i++) {
            for (let j = i + 1; j < allHashes.length; j++) {
                await fetch('/api/relations/remove', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        utility_hash: allHashes[i],
                        related_hash: allHashes[j],
                        bidirectional: true
                    })
                });
            }
        }
        
        alert('✅ 关联组已删除');
        loadRelationGroups();
        
    } catch (error) {
        alert('❌ 删除失败：' + error.message);
    }
}

// 向关联组添加道具
function addUtilityToGroup(comboGroup, existingHashes) {
    const groupName = comboGroup || '该关联组';
    
    // 存储到window以避免HTML属性引号问题
    window._tempExistingHashes = existingHashes;
    window._tempComboGroup = comboGroup;
    
    // 创建弹窗
    const modal = document.createElement('div');
    modal.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: rgba(0,0,0,0.5);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 10000;
    `;
    
    modal.innerHTML = `
        <div style="background: white; border-radius: 12px; padding: 30px; max-width: 600px; width: 90%;">
            <h3 style="margin-top: 0;">➕ 添加道具到 "${groupName}"</h3>
            
            <div class="search-input-wrapper" style="margin: 20px 0;">
                <input type="text" id="add-utility-search" placeholder="输入Hash值或道具名称搜索..." 
                       style="width: 100%; padding: 12px; border: 2px solid #ddd; border-radius: 8px; font-size: 14px;">
            </div>
            
            <div id="add-utility-results" style="max-height: 400px; overflow-y: auto; margin: 20px 0;">
                <div class="empty-state">请输入关键词搜索道具</div>
            </div>
            
            <div style="display: flex; gap: 10px; justify-content: flex-end;">
                <button class="btn btn-secondary" onclick="this.closest('div[style*=fixed]').remove()">取消</button>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    
    // 搜索功能
    const searchInput = modal.querySelector('#add-utility-search');
    const resultsDiv = modal.querySelector('#add-utility-results');
    
    let searchTimeout;
    searchInput.addEventListener('input', () => {
        clearTimeout(searchTimeout);
        const query = searchInput.value.trim();
        
        if (!query) {
            resultsDiv.innerHTML = '<div class="empty-state">请输入关键词搜索道具</div>';
            return;
        }
        
        searchTimeout = setTimeout(async () => {
            try {
                resultsDiv.innerHTML = '<div class="loading">搜索中...</div>';
                
                const response = await fetch(`/api/relations/search?q=${encodeURIComponent(query)}`);
                const result = await response.json();
                
                if (!response.ok) {
                    resultsDiv.innerHTML = `<div class="error-message">${result.error}</div>`;
                    return;
                }
                
                // 过滤掉已在组中的道具
                const filtered = result.utilities.filter(u => !existingHashes.includes(u.hash));
                
                if (filtered.length === 0) {
                    resultsDiv.innerHTML = '<div class="empty-state">没有找到可添加的道具</div>';
                    return;
                }
                
                resultsDiv.innerHTML = filtered.map(utility => `
                    <div style="border: 1px solid #ddd; border-radius: 8px; padding: 12px; margin-bottom: 10px; display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <div style="font-weight: 600;">${utility.display_name || utility.name}</div>
                            <div style="font-size: 12px; color: #666;">${utility.map_name} · ${utility.utility_type}</div>
                        </div>
                        <button class="btn btn-sm btn-primary" onclick="confirmAddUtilityToGroup('${utility.hash}')">
                            添加
                        </button>
                    </div>
                `).join('');
                
            } catch (error) {
                resultsDiv.innerHTML = `<div class="error-message">❌ 搜索失败：${error.message}</div>`;
            }
        }, 300);
    });
}

// 确认添加道具到组
async function confirmAddUtilityToGroup(newHash) {
    const comboGroup = window._tempComboGroup;
    const existingHashes = window._tempExistingHashes;
    try {
        // 将新道具与组内所有现有道具建立关联
        for (const existingHash of existingHashes) {
            const response = await fetch('/api/relations/add', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    utility_hash: newHash,
                    related_hash: existingHash,
                    bidirectional: true,
                    combo_group: comboGroup || null
                })
            });
            
            if (!response.ok) {
                throw new Error('添加关联失败');
            }
        }
        
        alert('✅ 道具已添加到关联组');
        
        // 关闭弹窗
        document.querySelector('div[style*="position: fixed"]').remove();
        
        // 刷新列表
        loadRelationGroups();
        
    } catch (error) {
        alert('❌ 添加失败：' + error.message);
    }
}

// ==================== 关联管理：创建页面 ====================

// 初始化关联管理页面
function initRelationsTab() {
    // 清空状态
    selectedUtilitiesMap.clear();
    searchedUtilities = [];
    updateRelationsDisplay();
    
    // 添加回车键搜索
    const searchInput = document.getElementById('hash-search-input');
    if (searchInput) {
        searchInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                searchByHash();
            }
        });
    }
}

// 通过Hash或名称搜索道具
async function searchByHash() {
    const input = document.getElementById('hash-search-input');
    const query = input.value.trim();
    const messageDiv = document.getElementById('search-result-message');
    
    // 清空消息
    messageDiv.textContent = '';
    messageDiv.className = 'search-message';
    
    if (!query) {
        messageDiv.textContent = '⚠️ 请输入Hash值或道具名称';
        messageDiv.className = 'search-message error';
        return;
    }
    
    try {
        // 使用新的搜索API
        const response = await fetch(`/api/relations/search?q=${encodeURIComponent(query)}`);
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || '搜索失败');
        }
        
        const data = await response.json();
        const utilities = data.utilities || [];
        
        if (utilities.length === 0) {
            throw new Error('未找到匹配的道具');
        }
        
        // 过滤掉已经在列表中的道具
        const newUtilities = utilities.filter(u => {
            return !searchedUtilities.find(existing => existing.hash === u.hash);
        });
        
        if (newUtilities.length === 0) {
            messageDiv.textContent = '⚠️ 搜索到的道具已在列表中';
            messageDiv.className = 'search-message error';
            return;
        }
        
        // 添加到搜索列表
        searchedUtilities.push(...newUtilities);
        
        // 显示成功消息
        if (newUtilities.length === 1) {
            messageDiv.textContent = `✅ 找到道具：${newUtilities[0].display_name || newUtilities[0].name || '未命名'}`;
        } else {
            messageDiv.textContent = `✅ 找到 ${newUtilities.length} 个道具`;
        }
        messageDiv.className = 'search-message success';
        
        // 清空输入框
        input.value = '';
        
        // 更新显示
        updateRelationsDisplay();
        
        // 2秒后清空消息
        setTimeout(() => {
            messageDiv.textContent = '';
        }, 2000);
        
    } catch (error) {
        messageDiv.textContent = '❌ ' + error.message;
        messageDiv.className = 'search-message error';
    }
}

// 添加到已选列表（切换选中状态）
function toggleSelectUtility(utility) {
    const hash = utility.hash;
    
    if (selectedUtilitiesMap.has(hash)) {
        // 已选中，取消选中
        selectedUtilitiesMap.delete(hash);
    } else {
        // 未选中，添加选中
        selectedUtilitiesMap.set(hash, utility);
    }
    
    updateRelationsDisplay();
}

// 清空所有已选
function clearAllSelected() {
    if (selectedUtilitiesMap.size === 0 && searchedUtilities.length === 0) {
        return;
    }
    
    const confirmMsg = selectedUtilitiesMap.size > 0 
        ? `确定要清空所有内容吗？\n\n已选择 ${selectedUtilitiesMap.size} 个道具\n搜索过 ${searchedUtilities.length} 个道具`
        : `确定要清空所有搜索结果吗？\n\n共 ${searchedUtilities.length} 个道具`;
    
    if (!confirm(confirmMsg)) {
        return;
    }
    
    selectedUtilitiesMap.clear();
    searchedUtilities = [];
    updateRelationsDisplay();
}

// 更新关联管理显示
function updateRelationsDisplay() {
    const container = document.getElementById('search-result-container');
    const countBadge = document.getElementById('selected-count-badge');
    const batchBtn = document.getElementById('batch-link-btn');
    
    // 更新计数
    const selectedCount = selectedUtilitiesMap.size;
    countBadge.innerHTML = `已选择 <strong>${selectedCount}</strong> 个道具`;
    
    // 更新按钮状态
    if (selectedCount >= 2) {
        batchBtn.disabled = false;
        batchBtn.textContent = `🔗 批量关联选中道具 (${selectedCount}个)`;
    } else {
        batchBtn.disabled = true;
        batchBtn.textContent = '🔗 批量关联选中道具 (至少2个)';
    }
    
    // 如果没有搜索过任何道具
    if (searchedUtilities.length === 0) {
        container.innerHTML = '<div class="empty-state">请使用上方搜索框输入Hash值搜索道具</div>';
        return;
    }
    
    // 渲染所有搜索过的道具
    // 已选中的在前，未选中的在后
    const selectedList = searchedUtilities.filter(u => selectedUtilitiesMap.has(u.hash));
    const unselectedList = searchedUtilities.filter(u => !selectedUtilitiesMap.has(u.hash));
    const sortedList = [...selectedList, ...unselectedList];
    
    const html = sortedList.map((util, index) => {
        const isSelected = selectedUtilitiesMap.has(util.hash);
        const order = isSelected ? Array.from(selectedUtilitiesMap.keys()).indexOf(util.hash) + 1 : 0;
        return renderRelationUtilityCard(util, isSelected, order);
    }).join('');
    
    container.innerHTML = html;
}

// 渲染关联管理页面的道具卡片
function renderRelationUtilityCard(utility, isSelected, order) {
    const screenshotBase = utility.screenshot_filename_base || `${utility.map}_${utility.hash}`;
    const type = utility.type || 'unknown';
    
    const utilityJson = JSON.stringify(utility).replace(/'/g, "\\'").replace(/"/g, '&quot;');
    
    return `
        <div class="search-result-card ${isSelected ? 'selected' : ''}" 
             data-hash="${utility.hash}"
             data-order="${order}">
            
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
                    <span class="label">名称</span>
                    <span class="value"><strong>${utility.display_name || utility.name || '未命名'}</strong></span>
                </div>
                
                <div class="info-row">
                    <span class="label">地图</span>
                    <span class="value">${utility.map.replace('de_', '').toUpperCase()}</span>
                </div>
                
                <div class="info-row">
                    <span class="label">类型</span>
                    <span class="value">${getUtilityTypeIcon(type)} ${type}</span>
                </div>
                
                <div class="actions">
                    ${isSelected ? `
                        <button class="btn btn-primary" onclick='toggleSelectUtility(${utilityJson})'>
                            ✓ 已选中 (${order})
                        </button>
                    ` : `
                        <button class="btn btn-primary" onclick='toggleSelectUtility(${utilityJson})'>
                            ➕ 添加到关联列表
                        </button>
                    `}
                </div>
            </div>
        </div>
    `;
}

// 批量关联选中道具
async function batchLinkSelectedUtilities() {
    const hashes = Array.from(selectedUtilitiesMap.keys());
    
    if (hashes.length < 2) {
        alert('至少需要选择2个道具进行关联');
        return;
    }
    
    // 获取组合名称
    const comboGroupInput = document.getElementById('combo-group-name');
    const comboGroup = comboGroupInput.value.trim() || null;
    
    const utilityNames = Array.from(selectedUtilitiesMap.values())
        .map((u, i) => `${i + 1}. ${u.display_name || u.name}`)
        .join('\n');
    
    let confirmMessage = `确定要将以下道具互相关联吗？\n\n${utilityNames}\n\n共 ${hashes.length} 个道具`;
    
    if (comboGroup) {
        confirmMessage += `\n\n📋 组合名称：${comboGroup}\n🔢 将按照列表顺序自动编号`;
    }
    
    if (!confirm(confirmMessage)) {
        return;
    }
    
    try {
        const response = await fetch('/api/relations/batch-link', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                utility_hashes: hashes,
                combo_group: comboGroup
            })
        });
        
        const result = await response.json();
        
        if (response.ok) {
            let successMsg = `✅ ${result.message}\n\n这些道具已经互相关联`;
            if (comboGroup) {
                successMsg += `\n\n📋 组合名称：${comboGroup}\n🔢 已按顺序编号 1-${hashes.length}`;
            }
            alert(successMsg);
            
            // 清空列表和组名输入框
            selectedUtilitiesMap.clear();
            comboGroupInput.value = '';
            updateRelationsDisplay();
        } else {
            alert('❌ ' + result.error);
        }
    } catch (error) {
        alert('❌ 请求失败：' + error.message);
    }
}
