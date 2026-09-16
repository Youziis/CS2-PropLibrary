// Demo 文件管理
// 拆分自 client/admin/script.js，以普通 <script> 加载（函数保持全局作用域）
// 依赖: utils.js

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
                <button class="btn btn-primary" onclick="parseDemo('${demo.name}')">
                    ${demo.parsed ? '重新解析' : '解析'}
                </button>
            </div>
        `).join('');
    } catch (error) {
        listEl.innerHTML = '<p class="hint error">加载失败: ' + error.message + '</p>';
    }
}

async function parseDemo(demoName) {
    // 获取按钮文本来判断是否是重新解析
    const btn = event.target;
    const isReparse = btn.textContent.trim() === '重新解析';
    
    const message = isReparse 
        ? `确定要重新解析 ${demoName} 吗？\n\n这将覆盖已有的解析数据（不会删除已截图和已批准的道具）。\n\n解析可能需要几分钟时间。`
        : `确定要解析 ${demoName} 吗？\n\n解析可能需要几分钟时间。`;
    
    if (!confirm(message)) {
        return;
    }
    
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
            loadDemos(); // 刷新Demo列表
        } else {
            alert(`${result.message}`);
        }
    } catch (error) {
        alert('解析失败: ' + error.message);
    } finally {
        btn.disabled = false;
        // 恢复按钮文本
        btn.textContent = isReparse ? '重新解析' : '解析';
    }
}
