// 手动添加道具
// 拆分自 client/admin/script.js，以普通 <script> 加载（函数保持全局作用域）
// 依赖: utils.js

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
