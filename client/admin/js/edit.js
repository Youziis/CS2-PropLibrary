// 编辑道具
// 拆分自 client/admin/script.js，以普通 <script> 加载（函数保持全局作用域）
// 依赖: utils.js

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
function cancelEditUtility(skipConfirm = false) {
    if (skipConfirm || confirm('确定要取消编辑吗？未保存的更改将丢失。')) {
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
    
    // 落点位置：表单没有对应输入项，不提交，后端会保留数据库中的原值
    
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
            // 根据自动导出结果显示不同消息
            let message = result.message;
            
            if (result.auto_exported === true) {
                message = '～(∠・ω<) ' + message + ' ✓';
            } else if (result.auto_exported === false) {
                message = '～(∠・ω<) 更新成功，但自动导出失败：' + (result.export_error || '未知错误');
            } else {
                message = '～(∠・ω<) ' + message;
            }
            
            // 显示成功提示（屏幕中央）
            showCenterMessage(message, 'success');
            
            // 2秒后返回道具管理页面（跳过确认对话框）
            setTimeout(() => {
                cancelEditUtility(true);
            }, 2000);
        } else {
            // 显示错误提示（屏幕中央）
            showCenterMessage('✗ 保存失败：' + (result.error || '未知错误'), 'error');
        }
    } catch (error) {
        console.error('保存道具错误:', error);
        showCenterMessage('✗ 保存失败：网络错误', 'error');
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
