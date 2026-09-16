// 审核道具
// 拆分自 client/admin/script.js，以普通 <script> 加载（函数保持全局作用域）
// 依赖: state.js, utils.js

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
        
        // 类型筛选：将incendiary和molotov视为同一类型（燃烧弹）
        if (typeFilter) {
            if (typeFilter === 'incendiary') {
                // 选择"燃烧弹"时，同时匹配incendiary和molotov
                if (type !== 'incendiary' && type !== 'molotov') return false;
            } else {
                // 其他类型正常匹配
                if (type !== typeFilter) return false;
            }
        }
        
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
                    <label>标签</label>
                    <input type="text" class="util-tags" placeholder="用逗号分隔多个标签，如：三楼,A1" value="${u.tags ? (Array.isArray(u.tags) ? u.tags.join(',') : u.tags) : ''}">
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
    
    // 收集标签
    const tagsInput = card.querySelector('.util-tags');
    const tags = tagsInput ? tagsInput.value.trim() : '';
    
    // 收集所有表单数据
    const utilityInfo = {
        display_name: name,
        tags: tags,
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
